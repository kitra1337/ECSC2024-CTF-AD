from jsonschema import validate, ValidationError
import json
from db import SONGS, PICTURES

class ENDPOINTS:
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    LOGOUT = "LOGOUT"
    GET_SONGS = "GET_SONGS"
    GET_PICTURES = "GET_PICTURES"
    GET_PLAYLIST = "GET_PLAYLIST"
    ADD_PLAYLIST = "ADD_PLAYLIST"
    GET_ALL_PLAYLISTS = "GET_ALL_PLAYLISTS"
    SET_PICTURE = "SET_PICTURE"
    INIT_GET_SHARED_PLAYLIST = "INIT_GET_SHARED_PLAYLIST"
    FINISH_GET_SHARED_PLAYLIST = "FINISH_GET_SHARED_PLAYLIST"


SCHEMAS = {
    ENDPOINTS.LOGIN : {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"}
        },
        "required": ["username", "password"]
    },
    ENDPOINTS.REGISTER : {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
            "confirm_password": {"type": "string"},
        },
        "required": ["username", "password", "confirm_password"]
    },

    
    # AUTH NEEDED
    ENDPOINTS.LOGOUT : {
        "type": "object",
        "properties": {
            "token": {"type":"string"}
        },
        "required": ["token"]
    },
    ENDPOINTS.GET_PLAYLIST : {
        "type": "object",
        "properties": {
            "token": {"type": "string"},
            "playlist_id": {"type": "string"}
        },
        "required": ["token", "playlist_id"]
    },
    ENDPOINTS.GET_ALL_PLAYLISTS : {
        "type": "object",
        "properties": {
            "token": {"type": "string"}
        },
        "required": ["token"]
    },
    ENDPOINTS.ADD_PLAYLIST : {
        "type": "object",
        "properties": {
            "token": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "public": {"type": "boolean"},
            "songs": {
                "type": "array", 
                "items": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": len(SONGS) -1 
                },
                "minItems": 0,
                "uniqueItems": True,
                "maxItems": len(SONGS)
            },
            "pubkey": {"type": "integer"}
        },
        "required": ["token", "title", "description", "public", "songs"]
    },
    ENDPOINTS.SET_PICTURE : {
        "type": "object",
        "properties": {
            "token": {"type": "string"},
            "playlist_id": {"type": "string"},
            "picture": {
                "type": "integer",
                "minimum": 0,
                "maximum": len(PICTURES) - 1
            }
        },
        "required": ["token", "playlist_id", "picture"]
    },
    ENDPOINTS.INIT_GET_SHARED_PLAYLIST : {
        "type": "object",
        "properties": {
            "token": {"type": "string"},
            "comm": {"type": "integer"}
        },
        "required": ["token", "comm"]
    },
    ENDPOINTS.FINISH_GET_SHARED_PLAYLIST : {
        "type": "object",
        "properties": {
            "token": {"type": "string"},
            "resp": {"type": "integer"},
            "playlist_id": {"type": "string"}
        },
        "required": ["token", "resp", "playlist_id"]
    }

}


REQUEST = {
    "type": "object",
    "properties": {
        "action": {"type": "string"},
        "params": {"type": "object"}
    },
    "required": ["action", "params"]
}


def validate_request(request: str) -> object:
    try:
        request = json.loads(request)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON")
    
    try:
        validate(request, REQUEST)
    except ValidationError:
        raise ValueError("Invalid request")
    
    if not hasattr(ENDPOINTS, request['action']):
        raise ValueError("Invalid action")
    
    if request['action'] in SCHEMAS:
        try:
            validate(request['params'], SCHEMAS[request['action']])
        except ValidationError:
            raise ValueError("Invalid parameters")
    
    return request

