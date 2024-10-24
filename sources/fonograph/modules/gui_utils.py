#!/usr/bin/env python3

import pygame
import pygame_gui
import os

local = os.environ.get("LOCALTEST", 'no') == '1'

# ============================================================= Constants

FPS = 60
WIDTH = 1600
HEIGHT = 900
CENTER = WIDTH // 2
BORDER_RADIUS = 5

if local:
    EXPECTED_START_URL_PICTURES = 'http://localhost:8080/pictures/'
    EXPECTED_START_URL_MUSIC    = 'http://localhost:8080/music/'
else:
    EXPECTED_START_URL_PICTURES = 'http://10.10.0.5/pictures/'
    EXPECTED_START_URL_MUSIC    = 'http://10.10.0.5/music/'

# ============================================================= Images

logo = pygame.image.load("assets/logo.png")
volume_icon = pygame.image.load("assets/volume.png")

# ============================================================= Colors

BG_COLOR = "#FFECC8"

