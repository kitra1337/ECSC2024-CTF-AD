#!/usr/bin/env python3

class User:

    def __init__(self, username='', password=''):
        self.name     = username
        self.password = password
        self.token    = ''
    
    def clear(self):
        self.name     = ''
        self.password = ''
        self.token    = ''
