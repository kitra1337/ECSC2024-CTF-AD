#!/usr/bin/env python3

import pygame
import pygame_gui

# ============================================================= Constants

FPS = 60
WIDTH = 1600
HEIGHT = 900
CENTER = WIDTH // 2
BORDER_RADIUS = 5
EXPECTED_START_URL_PICTURES = 'http://10.10.0.5/pictures/'
EXPECTED_START_URL_MUSIC    = 'http://10.10.0.5/music/'

# ============================================================= Images

logo = pygame.image.load("assets/logo.png")
volume_icon = pygame.image.load("assets/volume.png")

# ============================================================= Colors

BG_COLOR = "#FFECC8"

