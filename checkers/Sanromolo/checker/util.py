import sys
from atexit import register
from random import Random
from string import ascii_letters, digits
from time import monotonic

from .checklib import quit, Status
from .constants import *
from .name_gen import NAMES, SURNAMES

class Timer:
    __slots__ = ('start',)
    def __init__(self):
        self.start = monotonic()
        register(self.stop)

    def stop(self):
        delta = monotonic() - self.start
        eprint(f'Time: {delta:.2f} seconds')


class RNG(Random):
    def chance(self, n: int, d: int) -> bool:
        '''Return True with probability n/d'''
        return self.randrange(0, d) < n

    def random_string(self, length: int) -> str:
        return ''.join(self.choices(ascii_letters + digits, k=length))

    def random_user_name(self) -> bytes:
        return (self.choice(NAMES) + ' ' + self.choice(SURNAMES)).encode()

    def random_event_name(self) -> bytes:
        return self.random_string(self.randint(8, EVENT_NAME_LEN)).encode()

    def random_star_signature(self) -> bytes:
        return self.random_string(self.randint(8, EVENT_STAR_SIGNATURE_LEN)).encode()


def eprint(*a, **kwa):
    print(*a, **kwa, file=sys.stderr, flush=True)


def die(err: str):
    quit(Status.ERROR, 'System error', err)
