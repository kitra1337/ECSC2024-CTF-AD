#!/usr/bin/env python3
from random import SystemRandom
from string import ascii_letters, digits

alphabet = ascii_letters + digits
rng = SystemRandom()

def random_string(k):
    return ''.join(rng.choices(alphabet, k=k))