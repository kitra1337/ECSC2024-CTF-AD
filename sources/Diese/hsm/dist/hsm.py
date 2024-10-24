#!/usr/bin/env -S python3 -u

import base64
import binascii
import dataclasses
import enum
import struct
import subprocess
import sqlite3
import sys


class HSMError(Exception):
    pass


class MsgType(enum.IntEnum):
    # Replies
    OK = 0x00
    ERROR = 0x01
    # Host -> HSM
    IMPORT_KEY = 0x10
    IMPORT_ITEM = 0x11
    GET_ITEM = 0x12
    # HSM -> host
    KS_PUT = 0x20
    KS_GET = 0x21
    CS_PUT = 0x22
    CS_GET = 0x23


@dataclasses.dataclass(kw_only=True)
class Msg:
    typ: MsgType
    data: bytes


class Store:
    def __init__(self, db: sqlite3.Connection, name: str) -> None:
        self._name = name
        self._db = db

        self._db.execute(f"""CREATE TABLE IF NOT EXISTS {self._name} (
            key INTEGER PRIMARY KEY,
            value BLOB
        )""")

    def put(self, key: int, value: bytes) -> None:
        try:
            self._db.execute(f'INSERT INTO {self._name} VALUES (?, ?)', (key, value))
        except sqlite3.IntegrityError:
            raise HSMError(f'trying to overwrite {self._name} key {key}') from None

    def get(self, key: int) -> bytes:
        res = self._db.execute(f'SELECT value FROM {self._name} WHERE key = ?', (key,))
        row = res.fetchone()
        if row is None:
            raise HSMError(f'unknown {self._name} key {key}')
        return row[0]


class HSM:
    def __init__(self, fw_path: str) -> None:
        self._p = None
        self._p = subprocess.Popen([
            'qemu-system-arm', '-M', 'versatilepb', '-m', '1M', '-nographic',
            '-serial', 'stdio', '-monitor', 'none', '-parallel', 'none',
            '-kernel', fw_path,
        ], bufsize=0, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    def __del__(self) -> None:
        if self._p is not None:
            self._p.kill()

    def send_msg(self, msg: Msg) -> None:
        self._p.stdin.write(struct.pack('<BI', msg.typ, len(msg.data)))
        self._p.stdin.write(msg.data)

    def recv_msg(self) -> Msg:
        typ, size = struct.unpack('<BI', self._readn(5))
        return Msg(typ=MsgType(typ), data=self._readn(size))

    def _readn(self, size: int) -> bytes:
        data = b''
        while len(data) != size:
            if self._p.poll() is not None:
                raise RuntimeError("HSM process died")
            data += self._p.stdout.read(size - len(data))
        return data


class HSMInterface:
    def __init__(self, hsm: HSM, ks: Store, cs: Store) -> None:
        self._hsm = hsm
        self._ks = ks
        self._cs = cs

    def import_key(self, key_id: int, key_data: bytes) -> None:
        if len(key_data) > 1024:
            raise HSMError('key too long')
        data = struct.pack('<I', key_id) + key_data
        self._request(MsgType.IMPORT_KEY, data)

    def import_item(self, item_id: int, key_id: int, item_data: bytes) -> None:
        if len(item_data) > 1024:
            raise HSMError('item too long')
        data = struct.pack('<II', item_id, key_id) + item_data
        self._request(MsgType.IMPORT_ITEM, data)

    def get_item(self, item_id: int, key_id: int, share_token: bytes) -> bytes:
        if len(share_token) > 1024:
            raise HSMError('share token too long')
        data = struct.pack('<II', item_id, key_id) + share_token
        return self._request(MsgType.GET_ITEM, data)

    def _request(self, typ: MsgType, data: bytes) -> bytes:
        self._hsm.send_msg(Msg(typ=typ, data=data))
        while True:
            msg = self._hsm.recv_msg()
            if msg.typ == MsgType.OK:
                return msg.data
            elif msg.typ == MsgType.ERROR:
                raise HSMError(msg.data.decode())
            elif msg.typ == MsgType.KS_PUT:
                key, data = struct.unpack('<I', msg.data[:4])[0], msg.data[4:]
                self._ks.put(key, data)
            elif msg.typ == MsgType.KS_GET:
                key = struct.unpack('<I', msg.data[:4])[0]
                data = self._ks.get(key)
                self._hsm.send_msg(Msg(typ=MsgType.OK, data=data))
            elif msg.typ == MsgType.CS_PUT:
                key, data = struct.unpack('<I', msg.data[:4])[0], msg.data[4:]
                self._cs.put(key, data)
            elif msg.typ == MsgType.CS_GET:
                key = struct.unpack('<I', msg.data[:4])[0]
                data = self._cs.get(key)
                self._hsm.send_msg(Msg(typ=MsgType.OK, data=data))


def handle_cmd(hsm_if: HSMInterface, cmd: str) -> bytes:
    parts = cmd.split(' ')

    if parts[0] == 'IMPORT_KEY':
        if len(parts) != 3:
            raise HSMError('IMPORT_KEY: wrong number of arguments')
        try:
            key_id = int(parts[1])
        except ValueError:
            raise HSMError('IMPORT_KEY: invalid key ID') from None
        try:
            key_data = base64.b64decode(parts[2])
        except binascii.Error:
            raise HSMError('IMPORT_KEY: invalid key data') from None
        hsm_if.import_key(key_id, key_data)
        return b''

    if parts[0] == 'IMPORT_ITEM':
        if len(parts) != 4:
            raise HSMError('IMPORT_ITEM: wrong number of arguments')
        try:
            item_id = int(parts[1])
        except ValueError:
            raise HSMError('IMPORT_ITEM: invalid item ID') from None
        try:
            key_id = int(parts[2])
        except ValueError:
            raise HSMError('IMPORT_ITEM: invalid key ID') from None
        try:
            item_data = base64.b64decode(parts[3])
        except binascii.Error:
            raise HSMError('IMPORT_ITEM: invalid item data') from None
        hsm_if.import_item(item_id, key_id, item_data)
        return b''

    if parts[0] == 'GET_ITEM':
        if len(parts) != 4:
            raise HSMError('GET_ITEM: wrong number of arguments')
        try:
            item_id = int(parts[1])
        except ValueError:
            raise HSMError('GET_ITEM: invalid item ID') from None
        try:
            key_id = int(parts[2])
        except ValueError:
            raise HSMError('GET_ITEM: invalid key ID') from None
        try:
            share_token = base64.b64decode(parts[3])
        except binascii.Error:
            raise HSMError('GET_ITEM: invalid share token') from None
        item_data = hsm_if.get_item(item_id, key_id, share_token)
        return item_data

    raise HSMError('unknown command')


def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <firmware> <database>', file=sys.stderr)
        exit(1)

    fw_path, db_path = sys.argv[1:]

    db = sqlite3.connect(db_path, isolation_level=None)
    db.execute('PRAGMA journal_mode=WAL')

    hsm = HSM(fw_path)

    ks = Store(db, 'key_store')
    cs = Store(db, 'content_store')

    hsm_if = HSMInterface(hsm, ks, cs)

    for line in sys.stdin:
        cmd = line.strip()
        try:
            res = handle_cmd(hsm_if, cmd)
            print(f'OK {base64.b64encode(res).decode()}')
        except HSMError as e:
            print(f'ERROR {base64.b64encode(str(e).encode()).decode()}')
            break


if __name__ == '__main__':
    main()
