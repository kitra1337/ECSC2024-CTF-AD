import os
import re
from traceback import format_exc

from .checklib import quit, Status
from .constants import *
from .util import eprint

os.environ['PWNLIB_NOTERM'] = '1'
os.environ['PWNLIB_STDERR'] = '1'
from pwnlib.tubes.remote import remote as pwnlib_remote


def check_hex(data: bytes, expected_len: int) -> bool:
    return len(data) == expected_len and re.match(rb'^[a-z0-9]+$', data) is not None


class EventManager:
    remote: pwnlib_remote
    event_id: bytes|None = None
    wallet_id: bytes|None = None
    ticket_id: bytes|None = None
    assigned_seat: int|None = None
    seated: bool = False

    def __init__(self, host: str, port: int):
        try:
            self.remote = pwnlib_remote(host, port)
        except Exception:
            quit(Status.DOWN, 'Error connecting to event manager remote (service down?)',
                f'Error connecting to event manager at {host}:{port}:\n{format_exc()}')

    def __enter__(self) -> 'EventManager':
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.remote.close()

    def create_event(self, name: bytes, star_signature: bytes) -> tuple[bytes,bytes]:
        assert b'\n' not in name
        assert b'\n' not in star_signature
        assert 1 <= len(name) <= EVENT_NAME_LEN
        assert 1 <= len(star_signature) <= EVENT_STAR_SIGNATURE_LEN

        eprint(f'Creating event with {name=} {star_signature=}')
        self.remote.sendlineafter(b'> ', b'2')
        self.remote.sendlineafter(b'> ', name)
        self.remote.sendlineafter(b'> ', star_signature)

        line = self.remote.recvline()
        if not line.startswith(b'Event "' + name + b'" successfully created!'):
            quit(Status.DOWN, 'Failed to create event',
                f'Unexpected output creating event: {line=!r}')

        self.remote.recvuntil(b'Your event id is: ', drop=True)
        event_id_hex = self.remote.recvline().strip()
        if not check_hex(event_id_hex, EVENT_ID_SIZE * 2):
            quit(Status.DOWN, 'Failed to create event',
                f'Bad/missing event ID: {event_id_hex=!r}')

        self.remote.recvuntil(b'Your VIP invitation code is: ', drop=True)
        vip_code_hex = self.remote.recvline().strip()
        if not check_hex(vip_code_hex, EVENT_VIP_INV_CODE_SIZE * 2):
            quit(Status.DOWN, 'Failed to create event',
                f'Bad/missing VIP invitation code: {vip_code_hex=!r}')

        event_id_hex_str = event_id_hex.decode()
        vip_code_hex_str = vip_code_hex.decode()

        eprint(f'Event {event_id_hex_str} created with VIP code {vip_code_hex_str}')
        return bytes.fromhex(event_id_hex_str), bytes.fromhex(vip_code_hex_str)

    def join_event(self, event_id: bytes, wallet_id: bytes, ticket_id: bytes,
                as_vip: bool, expect_invalid: bool=False) -> int:
        assert len(event_id) == EVENT_ID_SIZE
        assert len(wallet_id) == WALLET_ID_SIZE
        assert len(ticket_id) == NFCTAG_SERIAL_FULL_SIZE

        asvip_str = (' as VIP' if as_vip else '')
        eprint(f'Joining{asvip_str} event {event_id.hex()} with wallet '
            f'{wallet_id.hex()} and ticket {ticket_id.hex()}')

        generic_fail_msg = 'Failed to join event'
        self.remote.sendlineafter(b'> ', b'1')
        self.remote.sendlineafter(b'> ', event_id.hex().encode())
        self.remote.sendlineafter(b'> ', wallet_id.hex().encode())
        self.remote.sendlineafter(b'> ', ticket_id.hex().encode())

        line = self.remote.recvline()
        if not line.startswith(b'Please wait while we connect to your wallet'):
            quit(Status.DOWN, generic_fail_msg, f'Unexpected output: {line=!r}')

        line = self.remote.recvline().strip()
        if line != b'Connected to the wallet.':
            quit(Status.DOWN, generic_fail_msg,
                f'Event manager failed to connect to wallet: {line=!r}')

        line = self.remote.recvline().strip()

        if expect_invalid:
            if line != b'Sorry, it appears this ticket has already been used.':
                quit(Status.DOWN, generic_fail_msg, 'Event manager failed to '
                    f'reject a supposedly invalid ticket: {line=!r}')

            # It's expected to not be able to sit, just return an invalid seat
            return -1

        if line != b'Your ticket has been validated!':
            quit(Status.DOWN, generic_fail_msg, 'Event manager failed to '
                f'validate ticket: {line=!r}')

        line = self.remote.recvline().strip()
        if not line.startswith(b'Welcome to the venue for '):
            quit(Status.DOWN, generic_fail_msg, 'Event manager did welcome us '
                f'to the venue: {line=!r}')

        self.remote.recvuntil(b'Your assigned seat is ')
        seat_raw = self.remote.recvuntil(b'.', drop=True)

        try:
            seat = int(seat_raw, 10)
        except ValueError:
            quit(Status.DOWN, generic_fail_msg, f'Bad/missing assigned seat: {seat_raw=!r}')

        if (as_vip and not (0 <= seat <= 99)) or (not as_vip and not (100 <= seat <= 999)):
            quit(Status.DOWN, generic_fail_msg, 'Assigned seat not in correct '
                f'zone: {as_vip=} {seat=}')

        self.event_id  = event_id
        self.wallet_id = wallet_id
        self.ticket_id = ticket_id
        self.assigned_seat = seat
        eprint(f'Event joined with assigned seat {seat}')

        return seat

    def sit(self, seat: int, as_vip: bool):
        assert self.event_id is not None
        assert self.wallet_id is not None
        assert self.ticket_id is not None
        assert self.assigned_seat is not None

        if as_vip:
            assert 0 <= seat <= 99
        else:
            assert 100 <= seat <= 999

        asvip_str = (' as VIP' if as_vip else '')
        eprint(f'Sitting{asvip_str} at event {self.event_id.hex()} seat {seat} '
            f'joined with wallet {self.wallet_id.hex()} and ticket '
            f'{self.ticket_id.hex()}')

        generic_fail_msg = 'Failed to join event'
        self.remote.sendlineafter(b'> ', b'1')
        self.remote.sendlineafter(b'> ', str(seat).encode())

        if as_vip:
            line = self.remote.recvline().strip()
            if not line.startswith(b'As soon as you enter the VIP section security approaches you '):
                quit(Status.DOWN, generic_fail_msg, 'No bouncer check '
                    f'triggered when sitting as VIP: {line=}')

            line = self.remote.recvline().strip()
            if not line.startswith(b"~ I'm sorry for not recognising you mr *looks quickly at his screen*... "):
                quit(Status.DOWN, generic_fail_msg, 'Bouncer did not '
                    f'recognize VIP: {line=}')

            if seat == self.assigned_seat:
                line = self.remote.recvline().strip()
                if line != b'~ Hope you like the show, have a good evening!':
                    quit(Status.DOWN, generic_fail_msg, 'Unexpected '
                        f'after sitting as VIP in correct seat: {line=}')
            else:
                line = self.remote.recvline().strip()
                if line != b'~ Please allow me to show you to your seat.':
                    quit(Status.DOWN, generic_fail_msg, 'Unexpected '
                        f'after sitting as VIP in wrong seat: {line=}')
        else:
            # Normal user
            line = self.remote.recvline().strip()
            if line != f'You sit in seat {seat}. No one questions you.'.encode():
                quit(Status.DOWN, generic_fail_msg, 'Unexpcted output '
                    f'sitting as normal user: {line=}')

        line = self.remote.recvline().strip()
        if line != b'What do you want to do?':
            quit(Status.DOWN, generic_fail_msg, 'No menu after sitting '
                f'at event: {line=}')

        self.seated = True

    def ask_star_autograph(self, as_vip: bool) -> bytes:
        assert self.event_id is not None
        assert self.wallet_id is not None
        assert self.ticket_id is not None
        assert self.seated

        asvip_str = (' as VIP' if as_vip else '')
        eprint(f'Asking for autograph{asvip_str} at event {self.event_id.hex()} '
            f'joined with wallet {self.wallet_id.hex()} and ticket '
            f'{self.ticket_id.hex()}')

        generic_fail_msg = 'Failed to ask for autograph at event'
        self.remote.sendlineafter(b'> ', b'1')

        if not as_vip:
            line = self.remote.recvline().strip()
            if not line.startswith(b'You wave and wave your hand, only for the star to pass '):
                quit(Status.DOWN, generic_fail_msg, 'Star noticed a normal '
                    f'user!? {line=}')

            # It's expected to not be able to get an autograph, return it empty
            return b''

        line = self.remote.recvline().strip()
        if not line.startswith(b'The star actually notices you!'):
            quit(Status.DOWN, generic_fail_msg, "Star didn't notice VIP? "
                f'{line=}')

        self.remote.recvuntil(b"You manage to get the star's autograph: ")
        autograph = self.remote.recvline().strip()
        eprint(f'Got star autograph {autograph!r}')
        return autograph
