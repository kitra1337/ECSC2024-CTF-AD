#!/usr/bin/env python3
import json
import asyncio
import dissononce

from websockets.asyncio.client import connect as connect_ws
from websockets.exceptions import ConnectionClosed
from setup_loggers import *
from utils import *
from user import User
from time import sleep
from exceptions import *
from parameters import p, q, g

from dissononce.processing.impl.handshakestate import HandshakeState
from dissononce.processing.impl.symmetricstate import SymmetricState
from dissononce.processing.impl.cipherstate import CipherState
from dissononce.processing.handshakepatterns.interactive.XX import XXHandshakePattern
from dissononce.cipher.aesgcm import AESGCMCipher
from dissononce.dh.x25519.x25519 import X25519DH
from dissononce.hash.sha256 import SHA256Hash

def auth_needed(func):
    def wrapper(self, *arg, **kwargs):
        if self.user.token == '':
            self.logger.warning(f'{func.__name__}: User is not logged in; {self.user.__dict__}')
            exit()
        return func(self, *arg, **kwargs)
    return wrapper

class Client:
    
    def __init__(self, uri='ws://localhost:5000/api'):
        self.uri       = uri
        self.user      = User()
        self.logger    = logging.getLogger('client')
        self.ws        = None
    
    async def connect(self):
        for _ in range(3):
            try:
                self.ws = await connect_ws(self.uri)
                await self.on_connect()
            except ConnectionClosed:
                self.logger.warning('connection closed unexpectedly, retrying')
            else:
                self.logger.info('connected!\n')
                return
        raise CantConnectException

    async def on_connect(self):
        self.s = X25519DH().generate_keypair()
        self.handshakestate = HandshakeState(SymmetricState(CipherState(AESGCMCipher()), \
                                                            SHA256Hash()), X25519DH())
        self.handshakestate.initialize(XXHandshakePattern(), True, b'', s=self.s)

        self.buffer = bytearray()
        self.handshakestate.write_message(b'', self.buffer)
        self.logger.debug(f'[0] {self.buffer.hex() = }')
        await self.ws.send(self.buffer.hex())

        self.buffer = bytes.fromhex(await self.ws.recv())
        self.logger.debug(f'[1] {self.buffer.hex() = }')
        self.handshakestate.read_message(self.buffer, bytearray())

        self.buffer = bytearray()
        self.cipherstates = self.handshakestate.write_message(b'', self.buffer)
        self.logger.debug(f'[2] {self.buffer.hex() = }')
        await self.ws.send(self.buffer.hex())

        return

    async def send(self, request):
        if self.ws is None:
            await self.connect()

        self.logger.info(f'{request = }')
        while 1:
            try:
                ctx = self.cipherstates[0].encrypt_with_ad(b'', json.dumps(request).encode())
                await self.ws.send(ctx.hex())

                response = bytes.fromhex(await self.ws.recv())
                response = json.loads(self.cipherstates[1].decrypt_with_ad(b'', response).decode())
                self.logger.info(f'{response = }\n')

                return response

            except ConnectionClosed:
                await self.connect()

    async def register(self, username, password):
        request = {
            'action': 'REGISTER',
            'params': {
                'username': username, 
                'password': password, 
                'confirm_password': password
                }
            }
        response = await self.send(request)
        if 'token' in response:
            self.user.name     = username
            self.user.password = password
            self.user.token    = response['token']
            return
        self.logger.warning('register failed')
        raise CantRegisterException(f'{response = }')

    async def login(self, username, password):
        request = {
            'action': 'LOGIN',
            'params': {
                'username': username, 
                'password': password, 
                }
            }
        response = await self.send(request)
        if 'token' in response:
            self.user.name     = username
            self.user.password = password
            self.user.token    = response['token']
            return
        self.logger.warning('login failed')
        raise CantLoginException(f'{response = }')

    async def get_songs(self):
        request = {
            'action': 'GET_SONGS',
            'params': {}
            }
        response = await self.send(request)
        return response
    
    async def get_pictures(self):
        request = {
            'action': 'GET_PICTURES',
            'params': {}
            }
        response = await self.send(request)
        return response

    async def get_playlist(self, playlist_id):
        request = {
            'action': 'GET_PLAYLIST',
            'params': {
                'token': self.user.token,
                'playlist_id': playlist_id
            }
        }
        response = await self.send(request)
        if 'description' in response:
            return response
        self.logger.warning(f'no playlist found')
        raise CantGetPlaylistException(f'{response = }')

    async def get_all_playlists(self):
        request = {
            'action': 'GET_ALL_PLAYLISTS',
            'params': {
                'token': self.user.token
            }
        }
        response = await self.send(request)
        return response
    
    @auth_needed
    async def logout(self):
        request = {
            'action': 'LOGOUT',
            'params': {
                'token': self.user.token
                }
            }
        response = await self.send(request)
        self.user.clear()
        return True

    @auth_needed
    async def add_playlist(self, title, description, public, songs, pubkey=0):
        request = {
            'action': 'ADD_PLAYLIST',
            'params': {
                'token': self.user.token,
                'title': title,
                'description': description,
                'public': public,
                'songs': songs,
                'pubkey': pubkey
            }
        }
        response = await self.send(request)
        if 'id' in response:
            return response['id']
        self.logger.warning(f'failed to add playlist')
        return None

    @auth_needed
    async def set_picture(self, playlist_id, picture_id):
        request = {
            'action': 'SET_PICTURE',
            'params': {
                'token': self.user.token,
                'playlist_id': playlist_id,
                'picture': picture_id
            }
        }
        response = await self.send(request)
        if 'songs' in response:
            return response
        self.logger.warning(f'failed to set playlist picture')
        return None
    
    @auth_needed
    async def get_shared_playlist(self, playlist_id, privkey):
        v = rng.randrange(q)
        comm = pow(g, v, p)
        request = {
            'action': 'INIT_GET_SHARED_PLAYLIST',
            'params': {
                'token': self.user.token,
                'comm': comm
            }
        }
        response = await self.send(request)
        if 'chall' not in response:
            self.logger.warning(f'failed to get shared playlist')
            return None
        chall = response['chall']
        resp = (v + privkey*chall)%q
        request = {
            'action': 'FINISH_GET_SHARED_PLAYLIST',
            'params': {
                'token': self.user.token,
                'resp': resp,
                'playlist_id': playlist_id
            }
        }
        response = await self.send(request)
        if 'description' in response:
            return response
        self.logger.warning('failed to get shared playlist')
        return response

    async def sanity(self):
        username = random_string(20)
        password = random_string(20)
        
        self.logger.info('test register 0')
        await self.register(username, password)

        self.logger.info('test logout 0')
        await self.logout()
        
        self.logger.info('test get_songs')
        songs       = await self.get_songs()
        song_ids    = [song['id'] for song in songs]

        self.logger.info('test get_pictures')
        pictures    = await self.get_pictures()
        picture_ids = [picture['id'] for picture in pictures]

        self.logger.info('test login')
        await self.login(username, password)

        self.logger.info('test add_playlist')
        playlist_id = await self.add_playlist(random_string(10), random_string(20), True, rng.sample(song_ids, k=rng.randint(0, len(songs))))

        self.logger.info('test get_playlist')
        playlist    = await self.get_playlist(playlist_id)

        self.logger.info('test get_all_playlists')
        playlists   = await self.get_all_playlists()

        self.logger.info('test set_picture')
        result = await self.set_picture(playlist_id, rng.choice(picture_ids))

        self.logger.info('test add_shared_playlist')
        x = rng.randrange(q)
        X = pow(g, x, p)
        playlist_id = await self.add_playlist(random_string(10), random_string(20), False, rng.sample(song_ids, k=rng.randint(0, len(songs))), X)

        self.logger.info('test logout 1')
        await self.logout()

        username, password = [random_string(20) for _ in range(2)]

        self.logger.info('test register 0')
        await self.register(username, password)

        self.logger.info('test get_shared_playlist')
        playlist = await self.get_shared_playlist(playlist_id, x)

        await self.ws.close()
        return

if __name__ == '__main__':
    client = Client()
    asyncio.run(client.sanity())
