#!/usr/bin/env python3

from checklib import *
from client import *
from hashlib import sha256
import json
import sys

print_err = lambda x : print(x, file=sys.stderr, flush=True)

port = 5000

async def check_register(client, username, password):
    print_err(f'checking register {username = }, {password = }')
    # register
    try:
        await client.register(username, password)
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except CantRegisterException as e:
        quit(Status.DOWN, "Registration failed", f'Registration failed, {e = }')
    except Exception as e:
        quit(Status.DOWN, "Registration failed", f"Registration failed, unknown {e = }")

async def check_logout(client):
    print_err('checking logout')
    # logout
    try:
        await client.logout()
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except Exception as e:
        quit(Status.DOWN, "Logout failed", f"Logout failed, {e = }")

async def check_login(client, username, password):
    print_err(f'checking login {username = }, {password = }')
    # login
    try:
        await client.login(username, password)
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except CantLoginException as e:
        quit(Status.DOWN, "Login failed", f"Login failed, {e = }")
    except Exception as e:
        quit(Status.DOWN, "Login failed", f"Login failed, unknown {e = }")

async def check_sla(host):
    print_err('check sla start')
    # Check service functionality
    client = Client(f'ws://{host}:{port}/api')
    username, password = [random_string(20, 5) for _ in range(2)]

    await check_register(client, username, password)
    await check_logout(client)
    await check_login(client, username, password)

    # get_songs
    print_err(f'checking get_songs')
    try:
        songs = await client.get_songs()
        song_ids = [song['id'] for song in songs]
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except Exception as e:
        quit(Status.DOWN, "Cannot get songs", f"Cannot get songs, unknown {e = }")
    
    # get_pictures
    print_err(f'checking get_pictures')
    try:
        pictures = await client.get_pictures()
        picture_ids = [picture['id'] for picture in pictures]
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except Exception as e:
        quit(Status.DOWN, "Cannot get pictures", f"Cannot get pictures, unknown {e = }")

    # add_private_playlist
    print_err('checking add_private_playlist')
    try:
        title = random_string(15, 5)
        description = random_string(30, 10)
        public = False
        songs_ = rng.sample(song_ids, k=rng.randint(0, len(songs)))
        privkey = rng.randrange(q)
        pubkey = pow(g, privkey, p)
        playlist_id = await client.add_playlist(title, description, public, songs_, pubkey)
        if playlist_id is None:
            quit(Status.DOWN, "Cannot add playlist", f'Cannot add playlist')
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except Exception as e:
        quit(Status.DOWN, "Cannot add playlist", f'Cannot add playlist, unknown {e = }')

    # set_picture
    print_err('checking set_picture')
    try:
        picture_id = rng.choice(picture_ids)
        playlist_ = await client.set_picture(playlist_id, picture_id)
        if playlist_ is None:
            quit(Status.DOWN, "Cannot set picture", "Cannot set picture")
        if any(k not in playlist_ for k in ['title', 'description', 'public', 'songs', 'id', 'picture', 'user_id']):
            quit(Status.DOWN, "Cannot set picture", f'Cannot set picture, malformed playlist {playlist_ = }')
        if playlist_['title'] != title or playlist_['description'] != description or bool(playlist_['public']) != public or playlist_['picture'] != pictures[picture_id]['url']:
            quit(Status.DOWN, "Cannot set picture", f'Picture set different from expected {playlist_["picture"] = }, {pictures = }')
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except Exception as e:
        quit(Status.DOWN, "Cannot set picture", f'Cannot set picture, unknown {e = }')

    # get_playlist
    print_err('checking get_playlist')
    try:
        response = await client.get_playlist(playlist_id)
        if any(k not in response for k in ['title', 'description', 'public', 'songs', 'id', 'picture', 'user_id']):
            quit(Status.DOWN, "Cannot get playlist", f'Cannot get playlist, malformed playlist {response = }')
        if response['title'] != title or response['description'] != description or bool(response['public']) != public:
            quit(Status.DOWN, "Cannot get playlist", f'Playlist different from expected {response = }')
    except CantConnectException:
        quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
    except CantGetPlaylistException as e:
        quit(Status.DOWN, "Cannot get playlist", f"Cannot get playlist, {e = }")
    except Exception as e:
        quit(Status.DOWN, "Cannot get playlist", f'Cannot get playlist, unknown {e = }')
    
    # get_shared_playlist
    print_err('checking get_shared_playlist')
    if not public:
        await check_logout(client)
        username1, password1 = [random_string(20, 5) for _ in range(2)]
        await check_register(client, username1, password1)

        if wrong := bool(rng.randint(0,1)):
            privkey = rng.randrange(q)

        try:
            playlist1 = await client.get_shared_playlist(playlist_id, privkey)
            if playlist1 is None:
                quit(Status.DOWN, "Cannot get shared playlist", 'Cannot get shared playlist')
            if not wrong:
                if any(k not in playlist1 for k in ['title', 'description', 'public', 'id', 'user_id']):
                    quit(Status.DOWN, "Cannot get shared playlist", f'Cannot get shared playlist, malformed playlist {playlist1 = }')
                if playlist1['title'] != title or playlist1['description'] != description or bool(playlist1['public']) != public:
                    quit(Status.DOWN, "Cannot get shared playlist", f'playlist different from expected {playlist1 = }, {pictures = }')
            else:
                if "pubkey" not in playlist1:
                    quit(Status.DOWN, "Cannot get shared playlist", f"pubkey is not returned when verification fails, {playlist1 = }")
                else:
                    if playlist1['pubkey'] != pubkey:
                        quit(Status.DOWN, "Cannot get shared playlist", f'wrong pubkey returned {playlist1["pubkey"] = }, {pubkey = }')
        except CantConnectException:
            quit(Status.DOWN, "Server unreachable", "Connection failed / noise handshake failed")
        except Exception as e:
            quit(Status.DOWN, "Cannot get shared playlist", f'Cannot get shared playlist, unknown {e = }')
    print_err('done check sla')

async def put_flag(host, flag):
    print_err('check put flag start')
    client = Client(f'ws://{host}:{port}/api')

    det_rng.seed(flag)
    username, password = [det_random_string(20, 5) for _ in range(2)]

    try:
        print_err('registering user')
        await client.register(username, password)
        # get_songs
        print_err('getting songs')
        songs = await client.get_songs()
        song_ids = [song['id'] for song in songs]
        title = det_random_string(15, 5)
        description = flag
        public = False
        songs_ = det_rng.sample(song_ids, k=det_rng.randint(0, len(songs)))
        privkey = det_rng.randrange(q)
        pubkey = pow(g, privkey, p)
        print_err('adding playlist')
        flag_id = await client.add_playlist(title, description, public, songs_, pubkey)
        if flag_id is None:
            quit(Status.DOWN, "put flag failed", f'put flag failed')
    except Exception as e:
        quit(Status.DOWN, "put flag failed", f'put flag failed, {e = }')
    
    try:
        with open(f'./flags/{sha256(flag.encode()).hexdigest()}.json', 'w') as wf:
            wf.write(json.dumps({'privkey': privkey, 'flag_id': flag_id}))          
    except Exception as e:
        quit(Status.ERROR, 'Failed to post flag id', f'failed to write privkey to file {e = }')
    
    # Post flag id to game server
    try:
        post_flag_id('fonograph', team_id, {"playlist_id": flag_id})
    except Exception as e:
        quit(Status.ERROR, 'Failed to post flag id', str(e))
    
    print_err('check put flag done')

async def get_flag(host, flag):
    print_err('check get flag')
    client = Client(f'ws://{host}:{port}/api')
    try:
        with open(f'./flags/{sha256(flag.encode()).hexdigest()}.json', 'r') as rf:
            data = json.loads(rf.read())
            privkey = data['privkey']
            flag_id = data['flag_id']
    except Exception as e:
        quit(Status.ERROR, 'get flag failed', f'failed to read privkey from file {e = }')
    
    det_rng.seed(flag)
    username, password = [det_random_string(20, 5) for _ in range(2)]

    try:
        print_err('logging in')
        await client.login(username, password)
        print_err('getting playlist (flag user)')
        response = await client.get_playlist(flag_id)
        if 'description' not in response:
            quit(Status.DOWN, 'get flag failed', 'get flag failed, no description')
        if flag != response['description']:
            quit(Status.DOWN, 'get flag failed', f'get flag failed, flag mismatch {flag = }, {response["description"] = }')
        print_err('logging out')
        await client.logout()

        username, password = [random_string(20, 5) for _ in range(2)]
        print_err('registering another user')
        await client.register(username, password)
        print_err('getting flag from other user')
        response = await client.get_shared_playlist(flag_id, privkey)
        if 'description' not in response:
            quit(Status.DOWN, 'get flag failed', f'get flag failed, no description, {response =}')
        if flag != response['description']:
            quit(Status.DOWN, 'get flag failed', f'get flag failed, flag mismatch {flag = }, {response["description"] = }')
    except Exception as e:
        quit(Status.DOWN, 'get flag failed', f'get flag failed {e = }')
    print_err('check get flag done')

async def main():
    if action == Action.CHECK_SLA.name:
        try:
            await check_sla(host)
        except Exception as e:
            quit(Status.DOWN, 'Cannot check SLA', str(e))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            await put_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot put flag", str(e))
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            await get_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot get flag", str(e))
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK, 'OK')

if __name__ == '__main__':
    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'
    if os.environ.get('LOCALHOST', 0) == '1':
        host = 'localhost'
    asyncio.run(main())