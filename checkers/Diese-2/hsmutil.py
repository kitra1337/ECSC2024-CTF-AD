import hashlib
import hmac
import random
import string
import struct

from Crypto.Cipher import ChaCha20


def rand_alnum(min_len: int, max_len: int) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits)
        for _ in range(random.randint(min_len, max_len)))


def rand_username() -> str:
    return rand_alnum(16, 32)


def rand_password() -> str:
    return rand_alnum(16, 32)


# Size sequence is safe for tokens (0 -> n-1 is root -> target), i.e., it
# avoids heap exhausting and the associated vulnerability.
def rand_keys(count: int) -> list[bytes]:
    keys = [random.randbytes(random.randint(128, 1024)) for _ in range(count)]
    # Descending size for root -> target to avoid fragmentation.
    keys.sort(key=len, reverse=True)
    return keys


def rand_item() -> bytes:
    return random.randbytes(random.randint(128, 1024))


def rand_nonce() -> bytes:
    # NOTE: size multiple of 4 to avoid OOB bug
    return random.randbytes(4 * random.randint(0, 3))


def hsm_cipher(data: bytes, key: bytes, nonce: bytes) -> bytes:
    assert len(nonce) == 12
    cipher = ChaCha20.new(key=hashlib.sha256(key).digest(), nonce=nonce)
    return cipher.encrypt(data)


def encrypt_item(data: bytes, key: bytes) -> bytes:
    return hsm_cipher(data, key, b'I'*12)


def decrypt_item(data: bytes, key: bytes) -> bytes:
    return hsm_cipher(data, key, b'I'*12)


def make_root_token(owner_key_id: int, item_id: int, key: bytes, extra: bytes = b'') -> bytes:
    token = struct.pack('<II', owner_key_id, item_id) + extra
    h = hmac.new(key, token, hashlib.sha256).digest()
    return token + h


def make_share_token(target_key_id: int, prev_token: bytes, key: bytes) -> bytes:
    token = struct.pack('<I', target_key_id) + prev_token
    h = hmac.new(key, token, hashlib.sha256).digest()
    return token + h


def finalize_token(token: bytes, key: bytes, nonce: bytes) -> bytes:
    assert 0 <= len(nonce) <= 12
    final = struct.pack('<B', len(nonce))
    final += hsm_cipher(nonce, key, b'T'*12)
    final += hsm_cipher(token, key, nonce.rjust(12, b'\x00'))
    return final
