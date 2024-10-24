import os
from ctypes import Structure, c_uint8, c_char, Array, sizeof
from enum import IntEnum
from traceback import format_exc
from typing import Type

from .checklib import quit, Status
from .constants import *
from .util import eprint

os.environ['PWNLIB_NOTERM'] = '1'
os.environ['PWNLIB_STDERR'] = '1'
from pwnlib.tubes.remote import remote as pwnlib_remote


def iso14443a_crc(data: bytes) -> bytes:
    crc = 0x6363

    for b in data:
        b = b ^ (crc & 0xFF)
        b = b ^ (b << 4) & 0xFF
        crc = (crc >> 8) ^ ((b << 8) & 0xFFFF) ^ ((b << 3) & 0xFFFF) ^ (b >> 4)

    return bytes((crc & 0xFF, (crc >> 8) & 0xFF))


class MessageType(IntEnum):
    Read         = 0x30
    Write        = 0xA2
    BuyUser      = 0x59
    BuyVIP       = 0x95
    NumCards     = 0x75
    GetCard      = 0x39
    CreateWallet = 0x99


class ResponseCode(IntEnum):
    ACK     = 0xA
    InvArg  = 0x0
    CRCErr  = 0x1
    Unknown = 0x9


class WalletCommand(Structure):
    type: MessageType
    _fields_: list[tuple[str,Type]]

    # Have to use a custom constructor because c_uint8 arrays are not implicitly
    # converted from bytes. Only c_char arrays are converted implicitly, but
    # they are also truncated at the first NUL byte, and we don't want that.
    # This also forces kwargs usage.
    def __init__(self, **kwargs):
        for name, ctype in self._fields_:
            if name in kwargs:
                if issubclass(ctype, Array):
                    setattr(self, name, ctype(*kwargs[name]))
                else:
                    setattr(self, name, ctype(kwargs[name]))

    def serialize_with_crc(self) -> bytes:
        # c_char is fine here and does not truncate at the first NUL
        raw = (c_char * 1).from_buffer_copy(c_uint8(self.type)).raw
        raw += (c_char * sizeof(self)).from_buffer_copy(self).raw
        return raw + iso14443a_crc(raw)


class WalletReadCommand(WalletCommand):
    type = MessageType.Read
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
        ('ticket_id', c_uint8 * NFCTAG_SERIAL_FULL_SIZE),
        ('page'     , c_uint8),
    ]


class WalletWriteCommand(WalletCommand):
    type = MessageType.Write
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
        ('ticket_id', c_uint8 * NFCTAG_SERIAL_FULL_SIZE),
        ('page'     , c_uint8),
        ('page_data', c_uint8 * NFCTAG_PAGE_SIZE),
    ]


class WalletBuyUserCommand(WalletCommand):
    type = MessageType.BuyUser
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
        ('event_id' , c_uint8 * EVENT_ID_SIZE),
        ('user'     , c_uint8 * NFCTAG_USER_SIZE),
    ]


class WalletBuyVIPCommand(WalletCommand):
    type = MessageType.BuyVIP
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
        ('event_id' , c_uint8 * EVENT_ID_SIZE),
        ('user'     , c_uint8 * NFCTAG_USER_SIZE),
        ('vip_code' , c_uint8 * EVENT_VIP_INV_CODE_SIZE),
    ]


class WalletNumCardsCommand(WalletCommand):
    type = MessageType.NumCards
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
    ]


class WalletGetCardCommand(WalletCommand):
    type = MessageType.GetCard
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
        ('offset'   , c_uint8),
    ]


class WalletCreateWalletCommand(WalletCommand):
    type = MessageType.CreateWallet
    _fields_ = [
        ('wallet_id', c_uint8 * WALLET_ID_SIZE),
    ]


class Wallet:
    wallet_id: bytes
    remote: pwnlib_remote

    def __init__(self, host: str, port: int, wallet_id: bytes|None=None):
        try:
            self.remote = pwnlib_remote(host, port)
        except Exception:
            quit(Status.DOWN, 'Error connecting to wallet remote (service down?)',
                f'Error connecting to wallet at {host}:{port}:\n{format_exc()}')

        if wallet_id is None:
            self.create()
        else:
            self.wallet_id = wallet_id

        assert self.wallet_id is not None
        assert len(self.wallet_id) == WALLET_ID_SIZE

    def __enter__(self) -> 'Wallet':
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.remote.close()

    def _send_command(self, cmd: WalletCommand) -> None:
        data = cmd.serialize_with_crc()
        self.remote.send(len(data).to_bytes(1, 'big') + data)

    def _recv_and_verify_response(self, expected_data_sz: int, err_msg: str) -> bytes:
        rlen = self.remote.recvn(1)[0]
        if rlen < 3:
            quit(Status.DOWN, 'Wallet remote returned invalid response length',
                f'Invalid response length: {rlen=}')

        resp_code = self.remote.recvn(1)
        resp_data = self.remote.recvn(rlen - 3) if rlen > 3 else b''
        resp_crc  = self.remote.recvn(2)

        try:
            parsed_resp_code = ResponseCode(resp_code[0])
        except ValueError:
            quit(Status.DOWN, 'Wallet remote returned invalid response code',
                f'Invalid response code: {resp_code[0]:#x}')

        if parsed_resp_code != ResponseCode.ACK:
            quit(Status.DOWN, err_msg,
                f'Wallet remote returned error: {parsed_resp_code!r}')

        expected_crc = iso14443a_crc(resp_code + resp_data)
        if resp_crc != expected_crc:
            quit(Status.DOWN, 'Wallet remote returned invalid response CRC',
                f'Bad response CRC: expected {expected_crc.hex()!r}, have '
                f'{resp_crc.hex()!r}')

        if len(resp_data) != expected_data_sz:
            quit(Status.DOWN, f'{err_msg}: wallet remote returned unexpected '
                'amount of data', 'Bad response data len: expected '
                f'{expected_data_sz}, have {len(resp_data)}')

        return resp_data

    def read_page(self, ticket_id: bytes, page: int) -> bytes:
        assert len(ticket_id) == NFCTAG_SERIAL_FULL_SIZE
        assert 0 <= page < NFCTAG_N_PAGES

        self._send_command(WalletReadCommand(
            wallet_id=self.wallet_id,
            ticket_id=ticket_id,
            page=page
        ))

        return self._recv_and_verify_response(NFCTAG_PAGE_SIZE,
            'Failed to read data from ticket')

    def write_page(self, ticket_id: bytes, page: int,
                page_data: bytes) -> bytes:
        assert len(ticket_id) == NFCTAG_SERIAL_FULL_SIZE
        assert 0 <= page < NFCTAG_N_PAGES
        assert len(page_data) == NFCTAG_PAGE_SIZE

        self._send_command(WalletWriteCommand(
            wallet_id=self.wallet_id,
            ticket_id=ticket_id,
            page=page,
            page_data=page_data
        ))

        return self._recv_and_verify_response(0, 'Failed to write data to ticket')

    def buy_user(self, event_id: bytes, user: bytes) -> bytes:
        assert len(event_id) == EVENT_ID_SIZE
        assert len(user) <= NFCTAG_USER_SIZE

        eprint('Wallet', self.wallet_id.hex(), 'buying user ticket for event',
            event_id.hex())

        user = user.ljust(NFCTAG_USER_SIZE, b'\0')
        self._send_command(WalletBuyUserCommand(
            wallet_id=self.wallet_id,
            event_id=event_id,
            user=user
        ))

        res = self._recv_and_verify_response(NFCTAG_SERIAL_FULL_SIZE,
            'Failed to buy ticket')
        eprint('Wallet', self.wallet_id.hex(), 'bought user ticket', res.hex())
        return res

    def buy_vip(self, event_id: bytes, user: bytes, vip_code: bytes) -> bytes:
        assert len(event_id) == EVENT_ID_SIZE
        assert len(user) <= NFCTAG_USER_SIZE
        assert len(vip_code) == EVENT_VIP_INV_CODE_SIZE

        eprint('Wallet', self.wallet_id.hex(), 'buying VIP ticket for event',
            event_id.hex(), 'using VIP code', vip_code.hex())

        user = user.ljust(NFCTAG_USER_SIZE, b'\0')
        self._send_command(WalletBuyVIPCommand(
            wallet_id=self.wallet_id,
            event_id=event_id,
            user=user,
            vip_code=vip_code
        ))

        res = self._recv_and_verify_response(NFCTAG_SERIAL_FULL_SIZE,
            'Failed to buy ticket')
        eprint('Wallet', self.wallet_id.hex(), 'bought VIP ticket', res.hex())
        return res

    def num_cards(self) -> int:
        self._send_command(WalletNumCardsCommand(wallet_id=self.wallet_id))
        data = self._recv_and_verify_response(1, 'Failed to get ticket count')
        return data[0]

    def get_card(self, offset: int) -> bytes:
        assert 0 <= offset < 256

        self._send_command(WalletGetCardCommand(wallet_id=self.wallet_id, offset=offset))
        return self._recv_and_verify_response(NFCTAG_SERIAL_FULL_SIZE,
            'Failed to list wallet')

    def create(self) -> bytes:
        self._send_command(WalletCreateWalletCommand())
        self.wallet_id = self._recv_and_verify_response(WALLET_ID_SIZE,
            'Failed to create wallet')
        eprint('Wallet', self.wallet_id.hex(), 'created')
        return self.wallet_id

    def read_full_ticket(self, ticket_id: bytes) -> bytes:
        res = b''
        for i in range(NFCTAG_N_PAGES):
            res += self.read_page(ticket_id, i)

        return res

    def rename_ticket_user(self, ticket_id: bytes, new_user: bytes) -> None:
        assert len(new_user) <= NFCTAG_USER_SIZE

        eprint('Wallet', self.wallet_id.hex(), 'updating user on ticket',
            ticket_id.hex(), 'to', repr(new_user))
        new_user = new_user.ljust(NFCTAG_USER_SIZE, b'\0')

        for i in range(NFCTAG_USER_SIZE // NFCTAG_PAGE_SIZE):
            start = i * NFCTAG_PAGE_SIZE
            end = start + NFCTAG_PAGE_SIZE
            self.write_page(ticket_id, NFCTAG_USER_PAGE + i, new_user[start:end])
