import flask
import json
import dissononce

from flask_sock import Sock
from validation import validate_request
from handlers import get_handler, make_error
from functools import partial
from dissononce.processing.impl.handshakestate import HandshakeState
from dissononce.processing.impl.symmetricstate import SymmetricState
from dissononce.processing.impl.cipherstate import CipherState
from dissononce.processing.handshakepatterns.interactive.XX import XXHandshakePattern
from dissononce.cipher.aesgcm import AESGCMCipher
from dissononce.dh.x25519.x25519 import X25519DH
from dissononce.hash.sha256 import SHA256Hash

app = flask.Flask(__name__)
sock = Sock(app)

@sock.route('/api')
def handler(ws):
    s = X25519DH().generate_keypair()
    handshakestate = HandshakeState(SymmetricState(CipherState(AESGCMCipher()), \
                                                            SHA256Hash()), X25519DH())
    handshakestate.initialize(XXHandshakePattern(), False, b'', s=s)
    
    buffer = bytes.fromhex(ws.receive())
    handshakestate.read_message(buffer, bytearray())

    buffer = bytearray()
    handshakestate.write_message(b'', buffer)
    ws.send(buffer.hex())

    buffer = bytes.fromhex(ws.receive())
    cipherstates = handshakestate.read_message(buffer, bytearray())

    while True:
        request = cipherstates[0].decrypt_with_ad(b'', bytes.fromhex(ws.receive())).decode()
        try:
            request = validate_request(request)
            handler = get_handler(request['action'])
            response = handler(request.get('params', {}))
            
        except ValueError as e:
            response = make_error(str(e))
        
        response = json.dumps(response).encode()
        response = cipherstates[1].encrypt_with_ad(b'', response).hex()
        ws.send(response)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")