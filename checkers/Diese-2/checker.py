#!/usr/bin/env python3

import functools
import json
import os
import random
import redis
import traceback
import typing

from checklib import *
from hsmutil import *
from interactions import Diesi


CHECKER_SECRET = 'REDACTED-2'
SERVICE_ID = 'Diese-2'


class ExceptionContext:
    def __init__(self, message: str, status: Status = Status.DOWN) -> None:
        self._message = message
        self._status = status

    def __call__(self, func: typing.Callable) -> typing.Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, SystemExit):
                    raise e
                quit(self._status, self._message, traceback.format_exc())
        return wrapper

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_tb) -> bool:
        if exc_value is not None:
            if isinstance(exc_value, SystemExit):
                return False
            exc_str = ''.join(traceback.format_exception(exc_value))
            quit(self._status, self._message, exc_str)
        return True


class CheckSLAExCtx(ExceptionContext):
    def __init__(self, message: str, status: Status = Status.DOWN) -> None:
        super().__init__(f'Cannot check SLA: {message}', status)


class PutFlagExCtx(ExceptionContext):
    def __init__(self, message: str, status: Status = Status.DOWN) -> None:
        super().__init__(f'Cannot put flag: {message}', status)


class GetFlagExCtx(ExceptionContext):
    def __init__(self, message: str, status: Status = Status.DOWN) -> None:
        super().__init__(f'Cannot get flag: {message}', status)


class RandomScheduler:
    def __init__(self):
        self._tasks = {}

    def task(self, name: str, *deps: str, prob: float = 1.0):
        def decorator(func: typing.Callable) -> typing.Callable:
            assert name not in self._tasks, f'Redefined task: {name}'
            for dep in deps:
                assert dep in self._tasks, f'Unknown dependency: {dep}'
            self._tasks[name] = (func, set(deps), prob)
            return func
        return decorator

    def run(self, run_all: bool = False) -> None:
        env: dict[str, typing.Any] = {}
        names = list(self._tasks.keys())
        processed: set[str] = set()
        scheduled: set[str] = set()
        have_new_scheduled = True
        while have_new_scheduled:
            have_new_scheduled = False
            random.shuffle(names)
            for name in names:
                if name in processed:
                    continue
                func, deps, prob = self._tasks[name]
                if not deps.issubset(scheduled):
                    continue
                processed.add(name)
                if run_all or random.random() < prob:
                    func(env)
                    scheduled.add(name)
                    have_new_scheduled = True
                    break


class FlagInfoStore:
    def __init__(self, namespace: str = 'Diese:fs2') -> None:
        self._namespace = namespace
        self._r = redis.Redis(
            host=os.environ['REDIS_HOST'],
            port=int(os.environ['REDIS_PORT']),
            db=int(os.environ['REDIS_DB']),
            password=os.environ.get('REDIS_PASSWORD'),
            decode_responses=True,
        )

    def get(self, flag: str) -> tuple[int, list[int]]:
        value = self._r.get(f'{self._namespace}:{flag}')
        if value is None:
            raise RuntimeError(f'no flag info key for {flag}')
        parts = value.split(':')
        item_id, key_ids = int(parts[0]), [int(s) for s in parts[1:]]
        return item_id, key_ids

    def put(self, flag: str, item_id: int, key_ids: list[int]) -> None:
        ser = f'{item_id}' + ''.join(f':{key_id}' for key_id in key_ids)
        self._r.set(f'{self._namespace}:{flag}', ser)


def check_sla(host: str, team_id: str, round: str) -> None:
    seed = rand_alnum(32, 32)
    print(f'SLA check seed: {seed}', file=sys.stderr)

    random.seed(seed)
    num_users = random.randint(2, 7)
    usernames = [rand_username() for _ in range(num_users)]
    passwords = [rand_password() for _ in range(num_users)]
    do_login = [random.choice([True, False]) for _ in range(num_users)]
    keys = rand_keys(num_users)
    item = rand_item()
    nonce_root = rand_nonce()
    nonce_share = rand_nonce()
    extra_root = random.randbytes(1024 - 41 - len(nonce_root))
    extra_share = random.randbytes(1024 - 41 - len(nonce_share) - 36*(num_users-1))

    checks = RandomScheduler()

    def gen_user_tasks(i: int) -> None:
        @checks.task(f'register_{i}')
        @CheckSLAExCtx('registration failed')
        def check_sla_register(env: dict[str, typing.Any]) -> None:
            client = Diesi(host)
            client.register_checked(usernames[i], passwords[i])
            env[f'client_{i}'] = client

        @checks.task(f'login_{i}', f'register_{i}')
        @CheckSLAExCtx('login failed')
        def check_sla_login(env: dict[str, typing.Any]) -> None:
            if do_login[i]:
                client = Diesi(host)
                client.login_checked(usernames[i], passwords[i])
                env[f'client_{i}'] = client

        @checks.task(f'import_key_{i}', f'login_{i}')
        @CheckSLAExCtx('failed to import key')
        def check_sla_import_key(env: dict[str, typing.Any]) -> None:
            client = env[f'client_{i}']
            key_id = client.hsm_import_key(keys[i])
            env[f'key_id_{i}'] = key_id

    for i in range(num_users):
        gen_user_tasks(i)

    @checks.task('import_item', 'import_key_0')
    @CheckSLAExCtx('failed to import item')
    def check_sla_import_item(env: dict[str, typing.Any]) -> None:
            client = env['client_0']
            item_id = client.hsm_import_item(encrypt_item(item, keys[0]))
            env['item_id'] = item_id

    @checks.task('get_item_root', 'import_item')
    @CheckSLAExCtx('failed to get item')
    def check_sla_get_item_root(env: dict[str, typing.Any]) -> None:
        client, key_id, item_id = env['client_0'], env['key_id_0'], env['item_id']
        token = make_root_token(key_id, item_id, keys[0], extra_root)
        token = finalize_token(token, keys[0], nonce_root)
        assert len(token) == 1024 # Prevent people from blocking long tokens
        recv_item = decrypt_item(client.hsm_get_item(item_id, token), keys[0])
        if recv_item != item:
            quit(Status.DOWN, 'Cannot check SLA: wrong item contents',
                 f'Epected item {item!r} got {recv_item!r}')

    @checks.task('get_item_share', 'import_item', *(f'import_key_{i}' for i in range(1, num_users)))
    @CheckSLAExCtx('failed to get item')
    def check_sla_get_item_share(env: dict[str, typing.Any]) -> None:
        client, item_id = env[f'client_{num_users-1}'],  env['item_id']
        token = make_root_token(env['key_id_0'], item_id, keys[0], extra_share)
        for i in range(0, num_users-1):
            token = make_share_token(env[f'key_id_{i+1}'], token, keys[i])
        token = finalize_token(token, keys[num_users-1], nonce_share)
        assert len(token) == 1024 # Prevent people from blocking long tokens
        recv_item = decrypt_item(client.hsm_get_item(item_id, token), keys[num_users-1])
        if recv_item != item:
            quit(Status.DOWN, 'Cannot check SLA: wrong item contents',
                 f'Epected item {item!r} got {recv_item!r}')

    checks.run()


def put_flag(host: str, team_id: str, flag: str) -> None:
    random.seed(f'{CHECKER_SECRET}:flag:{flag}')
    num_users = random.randint(1, 7)
    usernames = [rand_username() for _ in range(num_users)]
    passwords = [rand_password() for _ in range(num_users)]
    keys = rand_keys(num_users)

    clients = [Diesi(host) for _ in range(num_users)]

    key_ids = []
    for i in range(num_users):
        with PutFlagExCtx('registration failed'):
            clients[i].register_checked(usernames[i], passwords[i])
        with PutFlagExCtx('failed to import key'):
            key_ids.append(clients[i].hsm_import_key(keys[i]))

    with PutFlagExCtx('failed to import item'):
        item_id = clients[0].hsm_import_item(
            encrypt_item(flag.encode(), keys[0]))

    with PutFlagExCtx('failed to save flag info', status=Status.ERROR):
        FlagInfoStore().put(flag, item_id, key_ids)

    flag_id = {
        'key_id': key_ids[0],
        'item_id': item_id,
    }

    if 'DEV_SKIP_PUT_FLAG_ID' in os.environ:
        print(json.dumps(flag_id))
    else:
        with PutFlagExCtx('failed to post flag ID', status=Status.ERROR):
            post_flag_id(SERVICE_ID, team_id, flag_id)


def get_flag(host: str, flag: str) -> None:
    random.seed(f'{CHECKER_SECRET}:flag:{flag}')
    num_users = random.randint(1, 7)
    usernames = [rand_username() for _ in range(num_users)]
    passwords = [rand_password() for _ in range(num_users)]
    keys = rand_keys(num_users)

    nonce = rand_nonce()
    extra = random.randbytes(1024 - 41 - len(nonce) - 36*(num_users-1))

    with GetFlagExCtx('failed to get flag info', status=Status.ERROR):
        item_id, key_ids = FlagInfoStore().get(flag)

    client = Diesi(host)

    with GetFlagExCtx('login failed'):
        client.login_checked(usernames[num_users-1], passwords[num_users-1])

    token = make_root_token(key_ids[0], item_id, keys[0], extra)
    for i in range(num_users-1):
        token = make_share_token(key_ids[i+1], token, keys[i])
    token = finalize_token(token, keys[num_users-1], nonce)
    assert len(token) == 1024 # Prevent people from blocking long tokens

    with GetFlagExCtx('failed to get item'):
        item = decrypt_item(client.hsm_get_item(item_id, token), keys[num_users-1])

    if item != flag.encode():
        quit(Status.DOWN, 'Cannot get flag: wrong flag', f'Found {item!r} for flag {flag}')


if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'

    if 'DEV_FORCE_HOST' in os.environ:
        host = os.environ['DEV_FORCE_HOST']

    if action == Action.CHECK_SLA.name:
        round = data['round']
        with ExceptionContext('Cannot check SLA'):
            check_sla(host, team_id, round)
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        with ExceptionContext('Cannot put flag'):
            put_flag(host, team_id, flag)
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        with ExceptionContext('Cannot get flag'):
            get_flag(host, flag)
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK, 'OK')
