#!/usr/bin/env python3
import logging

# do not print anything in checker
websockets_loglevel = logging.CRITICAL
asyncio_loglevel    = logging.CRITICAL
client_loglevel     = logging.CRITICAL
dissononce_loglevel = logging.CRITICAL

logging.basicConfig(format='[+] %(name)s, %(levelname)s: %(message)s', level=logging.DEBUG)

websockets_logger = logging.getLogger('websockets')
websockets_logger.setLevel(websockets_loglevel)
websockets_logger.addHandler(logging.StreamHandler())

asyncio_logger    = logging.getLogger('asyncio')
asyncio_logger.setLevel(asyncio_loglevel)

client_logger     = logging.getLogger('client')
client_logger.setLevel(client_loglevel)

dissononce_logger = logging.getLogger('dissononce')
dissononce_logger.setLevel(dissononce_loglevel)