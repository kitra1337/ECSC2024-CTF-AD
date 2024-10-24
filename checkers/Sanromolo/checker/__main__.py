#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from traceback import format_exc
from typing import Any

from .checklib import get_data, post_flag_id, quit, Action, Status
from .constants import *
from .event_manager import *
from .util import eprint, die, RNG, Timer
from .wallet import Wallet

os.environ['PWNLIB_NOTERM'] = '1'
os.environ['PWNLIB_STDERR'] = '1'
from pwn import context


WALLET_PORT = 1337
MANAGER_PORT = 1338
FLAG_DATA_DIRECTORY = Path(__file__).parent.parent / 'flag_data'


def load_flag_data(flag: str) -> dict:
    try:
        with (FLAG_DATA_DIRECTORY / flag).open() as f:
            flag_data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError, PermissionError):
        die(f'Failed to get flag data for {flag=}:\n{format_exc()}')

    return flag_data


def save_flag_data(flag: str, flag_data: Any):
    try:
        with (FLAG_DATA_DIRECTORY / flag).open('w') as f:
            json.dump(flag_data, f)
    except (TypeError, UnicodeEncodeError, FileNotFoundError, PermissionError):
        die(f'Failed to save flag data for {flag=}:\n{format_exc()}')


def dump_ticket(ticket: bytes):
    for i in range(0, NFCTAG_N_PAGES):
       chunk = ticket[i * NFCTAG_PAGE_SIZE:(i + 1) * i * NFCTAG_PAGE_SIZE]
       chars = ''.join((chr(c) if 0x20 <= c <= 0x7e else '.') for c in chunk)
       eprint(f'[{i:02d}] {chunk.hex()} {chars}')


def check_ticket_event_id(ticket: bytes, expected: bytes):
    ticket_event_id = ticket[NFCTAG_EVENT_ID_OFF:NFCTAG_EVENT_ID_OFF + NFCTAG_EVENT_ID_SIZE]
    if ticket_event_id != expected:
        dump_ticket(ticket)
        quit(Status.DOWN, 'Failed to validate ticket data',
            f'Event ID mismatch: expected {expected.hex()!r}, '
            f'have {ticket_event_id.hex()!r}')


def check_ticket_user(ticket: bytes, expected: bytes):
    ticket_user = ticket[NFCTAG_USER_OFF:NFCTAG_USER_OFF + NFCTAG_USER_SIZE].rstrip(b'\0')
    if ticket_user != expected:
        dump_ticket(ticket)
        quit(Status.DOWN, 'Failed to validate ticket data',
            f'Ticket user mismatch: expected {expected!r}, have {ticket_user!r}')


def wallet_buy_user_ticket(rng: RNG, wallet: Wallet, event_id: bytes):
    orig_num_cards = wallet.num_cards()
    user = rng.random_user_name()
    user_ticket_id = wallet.buy_user(event_id, user)

    num_cards = wallet.num_cards()
    if num_cards != orig_num_cards + 1:
        quit(Status.DOWN, 'Wrong number of tickets in the wallet',
            f'Expected {orig_num_cards + 1}, have {num_cards}')

    ticket_ids: list[bytes] = []
    for i in range(num_cards):
        ticket_ids.append(wallet.get_card(i))

    if user_ticket_id not in ticket_ids:
        quit(Status.DOWN, 'Failed to list wallet',
            f'User ticket {user_ticket_id.hex()} not fonud after listing all '
            f'tickets, have {list(map(bytes.hex, ticket_ids))}')

    ticket = wallet.read_full_ticket(user_ticket_id)
    check_ticket_event_id(ticket, event_id)
    check_ticket_user(ticket, user)
    return user_ticket_id


def wallet_buy_vip_ticket(rng: RNG, wallet: Wallet, event_id: bytes, vip_code: bytes):
    orig_num_cards = wallet.num_cards()
    vip_user = rng.random_user_name()
    vip_ticket_id = wallet.buy_vip(event_id, vip_user, vip_code)

    num_cards = wallet.num_cards()
    if num_cards != orig_num_cards + 1:
        quit(Status.DOWN, 'Wrong number of tickets in the wallet',
            f'Expected {orig_num_cards + 1}, have {num_cards}')

    ticket_ids: list[bytes] = []
    for i in range(num_cards):
        ticket_ids.append(wallet.get_card(i))

    if vip_ticket_id not in ticket_ids:
        quit(Status.DOWN, 'Failed to list wallet',
            f'VIP ticket {vip_ticket_id.hex()} not fonud after listing all '
            f'tickets, have {list(map(bytes.hex, ticket_ids))}')

    ticket = wallet.read_full_ticket(vip_ticket_id)
    check_ticket_event_id(ticket, event_id)
    check_ticket_user(ticket, vip_user)
    return vip_ticket_id


def wallet_update_user(rng: RNG, wallet: Wallet, ticket_id: bytes, event_id: bytes):
    new_user = rng.random_user_name()
    wallet.rename_ticket_user(ticket_id, new_user)

    ticket = wallet.read_full_ticket(ticket_id)
    check_ticket_event_id(ticket, event_id)
    check_ticket_user(ticket, new_user)


def check_wallet_usage(rng: RNG, host: str):
    event_name = rng.random_event_name()
    secret     = rng.random_star_signature()

    eprint('Creating one event')
    with EventManager(host, MANAGER_PORT) as evtman:
        event_id, vip_code = evtman.create_event(event_name, secret)

    eprint('Creating wallet and tickets')
    with Wallet(host, WALLET_PORT) as wallet:
        if wallet.num_cards() != 0:
            quit(Status.DOWN, 'Wrong number of tickets in the wallet',
                'Wallet not empty at creation')

        # Buy a few tickets, some VIP and some not VIP, but at least one each
        tickets: list[bytes] = []
        to_buy = [True] * rng.randint(1, 5) + [False] * rng.randint(1, 5)
        rng.shuffle(to_buy)

        for is_vip in to_buy:
            if is_vip:
                tickets.append(wallet_buy_vip_ticket(rng, wallet, event_id, vip_code))
            else:
                tickets.append(wallet_buy_user_ticket(rng, wallet, event_id))

        eprint('Updating ticket users')

        # Update the user on some of the tickets (at least one), possibly even
        # multiple times.
        for tid in rng.choices(tickets, k=rng.randint(1, 10)):
            wallet_update_user(rng, wallet, tid, event_id)


def check_event_join(rng: RNG, host: str):
    event_name = rng.random_event_name()
    secret     = rng.random_star_signature()

    events: list[tuple[bytes,bytes]] = []
    jobs: list[tuple[bytes,bytes,bytes,bytes|None,bool]] = []

    eprint('Creating events')

    # Create 1 to 5 events
    for _ in range(rng.randint(1, 5)):
        with EventManager(host, MANAGER_PORT) as evtman:
            events.append(evtman.create_event(event_name, secret))

    eprint('Creating wallets')
    # Create 1 to 3 wallets
    for _ in range(rng.randint(1, 3)):
        with Wallet(host, WALLET_PORT) as wallet:
            # Choose random event to join
            event_id, vip_code = rng.choice(events)

            # Create a ticket per wallet (50% chance of doing it now, 50% chance
            # of doing it later)
            if rng.chance(1, 2):
                # Make it a VIP ticket with 50% chance
                is_vip = rng.chance(1, 2)

                if is_vip:
                    ticket_id = wallet_buy_vip_ticket(rng, wallet, event_id, vip_code)
                else:
                    ticket_id = wallet_buy_user_ticket(rng, wallet, event_id)
            else:
                is_vip = False
                ticket_id = None

            jobs.append((event_id, vip_code, wallet.wallet_id, ticket_id, is_vip))

    # Avoid mistakes lol
    del event_id
    del vip_code
    del wallet
    del ticket_id
    del is_vip

    rng.shuffle(jobs)
    eprint('Joining events')

    for eid, vip_code, wid, tid, is_vip in jobs:
        # Re-use existing wallets
        with Wallet(host, WALLET_PORT, wid) as wallet:
            # Create ticket now if needed (50% chance)
            if tid is None:
                # Make it a VIP ticket with 50% chance
                is_vip = rng.chance(1, 2)

                if is_vip:
                    tid = wallet_buy_vip_ticket(rng, wallet, eid, vip_code)
                else:
                    tid = wallet_buy_user_ticket(rng, wallet, eid)

        with EventManager(host, MANAGER_PORT) as evtman:
            seat = rng.randint(0, 99) if is_vip else rng.randint(100, 999)
            evtman.join_event(eid, wid, tid, as_vip=is_vip)
            evtman.sit(seat, as_vip=is_vip)
            evtman.ask_star_autograph(as_vip=is_vip)

        # Try re-using a ticket 0 to 2 times and check that we are denied access
        # to the event
        for _ in range(rng.randint(0, 2)):
            with EventManager(host, MANAGER_PORT) as evtman:
                evtman.join_event(eid, wid, tid,
                    as_vip=is_vip, expect_invalid=True)


def check_sla(host):
    seed = os.environ.get('SEED', os.urandom(16).hex())
    eprint('CHECK_SLA RNG seed:', seed)

    rng = RNG(seed)
    checks = [check_wallet_usage, check_event_join]
    rng.shuffle(checks)

    for check in checks:
        check(rng, host)


def put_flag(team_id: str, host: str, flag: str):
    seed = os.environ.get('SEED', os.urandom(16).hex())
    eprint('PUT_FLAG RNG seed:', seed)

    rng = RNG(seed)

    with EventManager(host, MANAGER_PORT) as evtman:
        event_id, vip_code = evtman.create_event(rng.random_event_name(), flag.encode())

    event_id_hex = event_id.hex()
    vip_code_hex = vip_code.hex()
    flag_data = {'event_id': event_id_hex, 'vip_code': vip_code_hex}
    save_flag_data(flag, flag_data)

    if os.getenv('DEV') is not None:
        eprint('[dev] Skip posting to flag ID service')
    else:
        post_flag_id('Sanromolo', team_id, {'event_id': event_id_hex})


def get_flag(host: str, flag: str):
    seed = os.environ.get('SEED', os.urandom(16).hex())
    eprint('GET_FLAG RNG seed:', seed)

    rng = RNG(seed)
    flag_data = load_flag_data(flag)

    try:
        assert isinstance(flag_data, dict)
        event_id = bytes.fromhex(flag_data['event_id'])
        vip_code = bytes.fromhex(flag_data['vip_code'])
    except (KeyError, ValueError, AssertionError):
        die(f'Malformed flag data for {flag=}\n{format_exc()}')

    with Wallet(host, WALLET_PORT) as wallet:
        ticket_id = wallet_buy_vip_ticket(rng, wallet, event_id, vip_code)

    with EventManager(host, MANAGER_PORT) as evtman:
        assigned_seat = evtman.join_event(event_id, wallet.wallet_id, ticket_id, as_vip=True)
        evtman.sit(assigned_seat, as_vip=True)
        received_flag = evtman.ask_star_autograph(as_vip=True)

    expected_flag = flag.encode()
    if received_flag != expected_flag:
        quit(Status.DOWN, 'Retrieved flag does not match',
            f'Flag mismatch: expected {expected_flag!r} VS actual {received_flag!r}')


def main() -> None:
    Timer()

    if os.getenv('DEBUG', '0') == '1':
        context(log_level='DEBUG')
    else:
        context(log_level='WARNING')

    if os.getenv('DEV') is not None:
        # Dev mode, only need ACTION and optionally FLAG
        action = os.getenv('ACTION')
        if action is None:
            sys.exit('Missing ACTION=')

        team_id = os.getenv('TEAM_ID', '255')
        host    = os.getenv('HOST', '127.0.0.1')
        flag    = os.getenv('FLAG') or ('THISISATEST'.ljust(32, 'A') + '=')
    else:
        data    = get_data()
        action  = data['action']
        team_id = data['teamId']
        host    = f'10.60.{team_id}.1'
        flag    = data['flag']

    FLAG_DATA_DIRECTORY.mkdir(0o700, parents=True, exist_ok=True)

    try:
        match Action(action):
            case Action.CHECK_SLA:
                check_sla(host)
            case Action.PUT_FLAG:
                assert flag is not None
                put_flag(team_id, host, flag)
            case Action.GET_FLAG:
                assert flag is not None
                get_flag(host, flag)
    except EOFError:
        # Treat EOFError as team's fault
        quit(Status.DOWN, 'Unexpected EOF', f'Unexpected EOFError:\n{format_exc()}')

    quit(Status.OK, 'OK')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        if isinstance(e, SystemExit):
            raise e from None
        else:
            die('Unexpected exception:\n' + format_exc())
