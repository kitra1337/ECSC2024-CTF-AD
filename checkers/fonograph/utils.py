#!/usr/bin/env python3
from random import SystemRandom, Random
from string import ascii_letters, digits

alphabet = ascii_letters + digits
rng = SystemRandom()
det_rng = Random()

def det_random_string(k, v):
    j = det_rng.randrange(-v,v)
    return ''.join(det_rng.choices(alphabet, k=k+j))

def random_string(k, v):
    j = rng.randrange(-v,v)
    return ''.join(rng.choices(alphabet, k=k+j))