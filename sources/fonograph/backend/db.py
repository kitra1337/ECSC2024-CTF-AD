import mysql.connector
import os
from werkzeug.security import generate_password_hash
import uuid
from parameters import p, q, g
from random import SystemRandom
import json

rng = SystemRandom()

class DBException(Exception):
    pass

local = os.environ.get("LOCALTEST", "no") == "1"
if local:
    BUCKET_URL = "http://localhost:8080"
else:
    BUCKET_URL = "http://10.10.0.5"

# Import music
SONGS = []
with open("music.json", "r") as f:
    SONGS = json.load(f)

    for x in SONGS:
        x["download_link"] = x["download_link"].format(BUCKET_URL=BUCKET_URL)


PICTURES = [
    {
        "id": i,
        "url": f"{BUCKET_URL}/pictures/picture-{i:02}.png",
    }
    for i in range(50)
]

picture_id2url = lambda picture_id: PICTURES[picture_id]["url"]


TABLES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(36) PRIMARY KEY,
        username VARCHAR(200) UNIQUE,
        password VARCHAR(200),
        comm VARCHAR(1000),
        chall VARCHAR(1000)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS playlist (
        id VARCHAR(36) PRIMARY KEY,
        title VARCHAR(200),
        description VARCHAR(1000),
        public BOOLEAN DEFAULT FALSE,
        picture INTEGER DEFAULT NULL,
        user_id VARCHAR(36),
        pubkey VARCHAR(1000),

        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS song_playlist(
        song_id INTEGER,
        playlist_id VARCHAR(36),

        PRIMARY KEY (song_id, playlist_id),
        FOREIGN KEY (playlist_id) REFERENCES playlist(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS session(
        token VARCHAR(32) PRIMARY KEY,
        user_id VARCHAR(36),

        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
]


class DB():
    hostname = os.environ.get('DBHOST', '127.0.0.1')
    dbname = os.environ.get('MYSQL_DATABASE', 'app')
    username = 'root'
    password = os.environ.get('MYSQL_ROOT_PASSWORD', 'password')


    def __init__(self):
        data = {
            "user": DB.username,
            "password": DB.password,
            "host": DB.hostname,
            "database": DB.dbname
        }

        try:
            self.conn = mysql.connector.connect(**data)
        except mysql.connector.Error as err:
            print(err)
            raise DBException("Error on database connection")


    def get_cursor(self) -> mysql.connector.cursor.MySQLCursor:
        return self.conn.cursor(dictionary=True)
    

    def commit(self):
        self.conn.commit()


    def check_data(self, data):
        for d in data:
            if any([x in d for x in ["'", '"', ";", "--", "/*", "*/"]]):
                raise DBException("Invalid data")


    def get_user(self, username):
        cursor = self.get_cursor()
        self.check_data([username])

        cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
        user = cursor.fetchone()

        self.commit()

        return user


    def get_user_by_token(self, token):
        cursor = self.get_cursor()
        self.check_data([token])

        cursor.execute(f"""
            SELECT u.*
            FROM users u
            INNER JOIN session s ON u.id = s.user_id
            WHERE s.token = '{token}'
        """)
        user = cursor.fetchone()

        self.commit()

        return user


    def get_songs(self):
        return SONGS


    def get_pictures(self):
        return PICTURES


    @classmethod
    def playlist_fetch_related(cls, cursor, playlist):
        if playlist['picture'] is not None:
            playlist['picture'] = picture_id2url(playlist['picture'])

        cursor.execute(
            f"""
            SELECT sp.song_id
            FROM song_playlist sp
            WHERE sp.playlist_id = '{playlist['id']}'
            """)
        songs = cursor.fetchall()
        playlist['songs'] = [
            SONGS[song['song_id']] for song in songs
        ]


    def get_all_playlists(self, token: str) -> list:
        cursor = self.get_cursor()
        self.check_data([token])

        cursor.execute(
            f"""
            SELECT DISTINCT p.*
            FROM playlist p
            LEFT OUTER JOIN session s ON p.user_id = s.user_id
            WHERE p.public = TRUE OR s.token = '{token}'
            LIMIT 50
            """)
        playlists = cursor.fetchall()

        for playlist in playlists:        
            DB.playlist_fetch_related(cursor, playlist)
            
        self.commit()
        
        return playlists


    def get_playlist(self, playlist_id: str, token: str) -> dict:
        cursor = self.get_cursor()
        self.check_data([playlist_id, token])

        cursor.execute(
            f"""
            SELECT DISTINCT p.*
            FROM playlist p
            LEFT OUTER JOIN session s ON p.user_id = s.user_id
            WHERE p.id = '{playlist_id}' AND (p.public = TRUE OR s.token = '{token}')
            """)
        playlist = cursor.fetchone()

        if not playlist:
            return None

        DB.playlist_fetch_related(cursor, playlist)

        self.commit()

        return playlist


    def get_shared_playlist(self, user: dict, playlist_id: str) -> dict:
        cursor = self.get_cursor()
        self.check_data([playlist_id])

        cursor.execute(
            f"""
            SELECT *
            FROM playlist
            WHERE id = '{playlist_id}'
            """)
        playlist = cursor.fetchone()
        
        if not playlist:
            return None

        DB.playlist_fetch_related(cursor, playlist)

        self.commit()

        return playlist


    def make_session(self, user_id, token):
        cursor = self.get_cursor()

        cursor.execute("INSERT INTO session(token, user_id) VALUES (%s, %s)", (token, user_id))

        self.commit()


    def delete_session(self, token):
        cursor = self.get_cursor()

        cursor.execute(f"DELETE FROM session WHERE token = %s", (token,))

        self.commit()


    def make_user(self, username, password) -> dict:
        cursor = self.get_cursor()

        id = str(uuid.uuid4())
        
        chall = rng.randrange(q)

        cursor.execute("INSERT INTO users (id, username, password, chall) VALUES (%s, %s, %s, %s)", (id, username, password, str(chall)))

        self.commit()

        user = {
            "id": id,
            "username": username,
            "password": password
        }
        
        return user


    def add_playlist(self, user: dict, title: str, description: str, public: bool, songs: list, pubkey: int = 0) -> dict:
        cursor = self.get_cursor()

        playlist_id = str(uuid.uuid4())

        if public:
            cursor.execute("INSERT INTO playlist(id, title, description, public, user_id) VALUES (%s, %s, %s, %s, %s)", (playlist_id, title, description, public, user['id']))
        else:
            cursor.execute("INSERT INTO playlist(id, title, description, public, user_id, pubkey) VALUES (%s, %s, %s, %s, %s, %s)", (playlist_id, title, description, public, user['id'], str(pubkey)))

        for song_id in songs:
            cursor.execute("INSERT INTO song_playlist(song_id, playlist_id) VALUES (%s, %s)", (song_id, playlist_id))

        self.commit()

        return {
            "id": playlist_id
        }


    def set_chall(self, user: dict) -> dict:
        cursor = self.get_cursor()
        
        chall = rng.randrange(q)
        cursor.execute("UPDATE users SET chall = %s WHERE id = %s", (str(chall), user['id']))
        
        self.commit()
        
        return {
            "id": user['id']
        }


    def set_comm(self, user: dict, comm: int) -> dict:
        cursor = self.get_cursor()

        cursor.execute("UPDATE users SET comm = %s WHERE id = %s", (str(comm), user['id']))
        
        self.commit()
        
        return {
            "id": user['id']
        }


    def set_picture(self, user: dict, playlist_id: str, picture: int) -> dict:
        cursor = self.get_cursor()

        cursor.execute("UPDATE playlist SET picture = %s WHERE id = %s AND user_id = %s", (picture, playlist_id, user['id']))
        cursor.execute("SELECT * FROM playlist WHERE id = %s", (playlist_id,))

        playlist = cursor.fetchone()

        if not playlist:
            return None

        DB.playlist_fetch_related(cursor, playlist)

        self.commit()

        return playlist


if __name__ == "__main__":
    db = DB()

    for table in TABLES:
        print(f"Doing: {table}")
        db.get_cursor().execute(table)

    db.commit()
    db.conn.close()
