import pygame as pg
from Vec2 import Vec2


class Forces:
    PENETRATION_ALLOWANCE = 0.05  # aka slop
    POSITIONAL_CORRECTION = 0.8  # 20% - 80%
    INF_MASS = 0
    GRAVITY = Vec2(0, 250)  # 250
    AIR_VELOCITY = Vec2(0, 0)  # for wind or something


class Materials:
    REST = 'rest'  # restitution
    DENS = 'dens'  # density
    ROCK = {REST: 0.1, DENS: 0.6}
    WOOD = {REST: 0.2, DENS: 0.3}
    METAL = {REST: 0.05, DENS: 1.2}
    TESTING = {REST: .2, DENS: 1}


class Values:
    FONT = "Times New Roman"

    FPS = 120
    DT = 1 / FPS

    SCREEN_WIDTH = 300
    SCREEN_HEIGHT = 200
    RES_MUL = 4


class Colours:
    BG_COL = (0, 10, 10)
    BG_COL_LIGHT = (0, 15, 15)
    WHITE = (255, 255, 255)
    LIGHT_GREY = (150, 150, 150)
    GREY = (60, 100, 100)
    DARK_GREY = (30, 50, 50)
    DARKER_GREY = (10, 25, 25)
    DARKERER_GREY = (5, 15, 15)
    BLACK = (0, 0, 0)

    RED = (255, 60, 60)
    ORANGE = (255, 140, 60)
    YELLOW = (255, 255, 0)
    GREEN = (100, 255, 100)
    AQUA = (100, 255, 255)
    LIGHT_BLUE = (194, 221, 255)
    BLUE = (70, 150, 255)
    MAGENTA = (200, 0, 200)
    PINK = (255, 100, 255)