import pygame as pg
from Vec2 import Vec2, EPSILON
from mat2 import Mat2


def do_lines_cross(line_a: tuple[Vec2, Vec2], line_b: tuple[Vec2, Vec2]) -> bool:
    """ Returns whether the two given lines intersect / cross one another """
    # unpack lines
    a1, a2 = line_a
    b1, b2 = line_b

    def on_segment(a, b, c):
        """ checks if point b lies on line segment 'ac' """
        return ((b.x <= max(a.x, c.x)) and (b.x >= min(a.x, c.x)) and
                (b.y <= max(a.y, c.y)) and (b.y >= min(a.y, c.y)))

    def get_orient(a, b, c):
        """ find the orientation of an ordered triplet """
        orient = ((b.y - a.y) * (c.x - b.x)) - ((b.x - a.x) * (c.y - b.y))
        if orient > 0:  # clockwise
            return 1
        elif orient < 0:  # counter-clockwise
            return 2
        return 0  # collinear

    o1 = get_orient(b1, b2, a1)
    o2 = get_orient(b1, b2, a2)
    o3 = get_orient(a1, a2, b1)
    o4 = get_orient(a1, a2, b2)

    # normal case (return early)
    if (o1 != o2) and (o3 != o4):
        return True

    # collinear cases
    cc_1 = (o1 == 0) and on_segment(b1, a1, b2)
    cc_2 = (o2 == 0) and on_segment(b1, a2, b2)
    cc_3 = (o3 == 0) and on_segment(a1, b1, a2)
    cc_4 = (o4 == 0) and on_segment(a1, b2, a2)

    return cc_1 or cc_2 or cc_3 or cc_4


def clamp(value, min_v, max_v):
    return max(min_v, min(max_v, value))


def greater_than(a: float, b: float):
    return a >= (b * Forces.BIAS_RELATIVE) + (a * Forces.BIAS_ABSOLUTE)


class Forces:
    PENETRATION_ALLOWANCE = 0.05  # aka slop
    POSITIONAL_CORRECTION = 0.2  # 20% - 80%
    BIAS_RELATIVE = 0.95
    BIAS_ABSOLUTE = 0.01
    INF_MASS = 0
    GRAVITY = Vec2(0, 100)  # 100
    AIR_VELOCITY = Vec2()  # for wind or something


class Materials:
    REST = 'rest'  # restitution
    DENS = 'dens'  # density
    ROCK = {REST: 0.1, DENS: 0.6}
    WOOD = {REST: 0.2, DENS: 0.3}
    METAL = {REST: 0.05, DENS: 1.2}
    TESTING = {REST: .2, DENS: 1}


class Values:
    FONT = "Times New Roman"

    FPS = 60
    DT = 1 / FPS
    RESTING = (Forces.GRAVITY * DT).length_sq() + EPSILON

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