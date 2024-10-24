from validation import ENDPOINTS
from db import DB
from parameters import p, q, g
import os

make_token = lambda: os.urandom(16).hex()
make_error = lambda message: {'error': message}
get_handler = lambda action: HANDLERS[action]

def auth_needed(func):
    def wrapper(params: dict) -> dict:
        token = params.get('token')
        connection = DB()
        user = connection.get_user_by_token(token)
        
        if user is None:
            return make_error("Invalid token")
        
        return func(connection, user, params)
    
    return wrapper


def login_handler(params : dict) -> dict:
    username = params.get('username')
    password = params.get('password')
    
    connection = DB()
    user = connection.get_user(username)

    if user is None or user['password'] != password:
        return make_error("Invalid username or password")

    token = make_token()
    connection.make_session(user['id'], token)

    return {
        'token': token
    }


def register_handler(params : dict) -> dict:
    username = params.get('username')
    password = params.get('password')
    confirm_password = params.get('confirm_password')

    if password != confirm_password:
        return make_error("Passwords do not match")

    connection = DB()
    if connection.get_user(username):
        return make_error("Username already exists")

    user = connection.make_user(username, password)

    token = make_token()
    connection.make_session(user['id'], token)

    return {
        'token': token
    }


def get_available_songs(params: dict) -> dict:
    connection = DB()
    return connection.get_songs()


def get_available_pictures(params: dict) -> dict:
    connection = DB()
    return connection.get_pictures()


@auth_needed
def logout_handler(connection: DB, user: dict, params: dict) -> dict:
    token = params.get('token')
    connection.delete_session(token)
    return {}


def get_all_playlists(params: dict) -> dict:
    token = params.get('token')

    connection = DB()

    playlist = connection.get_all_playlists(token)
    return playlist


def get_playlist(params: dict) -> dict:
    playlist_id = params.get('playlist_id')
    token = params.get('token')
    
    connection = DB()

    playlist = connection.get_playlist(playlist_id, token)
    if playlist:
        return playlist
    
    return make_error("Invalid playlist id")

@auth_needed
def init_get_shared_playlist(connection: DB, user: dict, params: dict) -> dict:
    comm = params.get('comm')
    connection.set_comm(user, comm)

    return {
        'chall': int(user['chall'])
    }
    
@auth_needed
def finish_get_shared_playlist(connection: DB, user: dict, params: dict) -> dict:
    resp = params.get('resp')
    playlist_id = params.get('playlist_id')
    playlist = connection.get_shared_playlist(user, playlist_id)
    if playlist is None:
        return make_error('invalid playlist_id')
    comm = int(user['comm'])
    chall = int(user['chall'])
    pubkey = int(playlist['pubkey'])
    connection.set_chall(user)
    if pow(g, resp, p) == (comm * pow(pubkey, chall, p)) % p:
        return playlist
        
    return {
        'pubkey': pubkey
    }

@auth_needed
def add_playlist(connection: DB, user: dict, params: dict) -> dict:
    title = params.get('title')
    description = params.get('description')
    public = params.get('public')
    songs = params.get('songs')
    pubkey = 0
    if not public:
        pubkey = params.get('pubkey')

    return connection.add_playlist(user, title, description, public, songs, pubkey)


@auth_needed
def set_picture(connection: DB, user: dict, params: dict) -> dict:
    playlist_id = params.get('playlist_id')
    picture = params.get('picture')
    
    return connection.set_picture(user, playlist_id, picture)


HANDLERS = {
    ENDPOINTS.LOGIN : login_handler,
    ENDPOINTS.REGISTER : register_handler,
    ENDPOINTS.LOGOUT : logout_handler,
    ENDPOINTS.GET_SONGS : get_available_songs,
    ENDPOINTS.GET_PICTURES : get_available_pictures,
    ENDPOINTS.GET_PLAYLIST : get_playlist,
    ENDPOINTS.GET_ALL_PLAYLISTS : get_all_playlists,
    ENDPOINTS.ADD_PLAYLIST : add_playlist,
    ENDPOINTS.SET_PICTURE : set_picture,
    ENDPOINTS.INIT_GET_SHARED_PLAYLIST: init_get_shared_playlist,
    ENDPOINTS.FINISH_GET_SHARED_PLAYLIST: finish_get_shared_playlist
}