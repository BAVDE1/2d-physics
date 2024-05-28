import math
import time

from constants import *
from Vec2 import Vec2

BASE_RIPPLE_SPEED = 1 / 60


class Ripple:
    """ Generates the block order that a ripple will travel (in both directions) """
    def __init__(self, strength: float, start_inx: int, end_inx: int, speed: float = BASE_RIPPLE_SPEED):
        self.strength: float = strength
        self.strength_decay: float = 0.98
        self.ripple_speed: float = speed

        self.start_inx: int = start_inx
        self.end_inx: int = end_inx

        self.generated_order: list = self.generate_order()
        self.on_ripple: int = -1

        self.strength_cut_off: float = 1

        self.last_progressed: float = time.time()
        self.accumulated_dt: float = 0

    def generate_order(self) -> list:
        """ Generates the order in which the ripple will travel. Returns list of indexes of the blocks """
        sn = self.start_inx
        li = [[sn]]  # first ripple already there
        for number in range(1, self.end_inx):
            up = sn + number
            down = sn - number
            seg = []
            if up < self.end_inx:
                seg.append(up)
            if down > -1:
                seg.append(down)
            if len(seg):
                li.append(seg)
        return li

    def get_next(self) -> list[int]:
        """ Get next blocks to add a ripple to """
        self.on_ripple += 1
        self.strength *= self.strength_decay

        blocks_left = len(self.generated_order)
        too_weak = self.strength < self.strength_cut_off
        val = None if blocks_left == 0 or too_weak else self.generated_order.pop(0)

        return [val, self.on_ripple]


class BlockSine:
    """ One ripple handled for one block """
    def __init__(self, strength):
        self.strength: float = strength

        self.started_time: float = time.time()
        self.max_time_alive: float = 0.8

    def get_sine(self):
        """ Return sine value for block """
        time_alive = time.time() - self.started_time
        time_left = self.max_time_alive - time_alive

        perc_completed = time_left / self.max_time_alive
        freq = 18 + (self.strength / 2)  # between 18 - 22
        sine = (self.strength * perc_completed) * math.sin(freq * time_alive)
        return sine if time_left >= 0 else None


class WaterBlock:
    def __init__(self, water, pos: Vec2, size: int, inx: int):
        self.water: Water = water
        self.inx: int = inx

        self.display_rect: pg.Rect = pg.Rect(pos.get(), [size] * 2)
        self.og_display_rect: pg.Rect = pg.Rect(self.display_rect)

        margin: float = size * 1.5
        self.coll_bounds: pg.Rect = pg.Rect(self.display_rect.x, self.display_rect.y - margin / 2,
                                   self.display_rect.w, self.display_rect.h + margin)
        self.mouse_in: bool = False
        self.block_sines: list[BlockSine] = []
        self.max_sines: int = 10

    def new_sine(self, strength, offset):
        """ Create a fresh ripple for the block, places at start of list """
        if strength > 0 and len(self.block_sines) < self.max_sines:
            s = BlockSine(strength)
            s.started_time -= offset
            self.block_sines.insert(0, s)

    def update(self):
        mp = pg.Rect(
            Vec2(pg.mouse.get_pos()[0] / Values.RES_MUL, pg.mouse.get_pos()[1] / Values.RES_MUL).get(),
            [1, 1]
        )
        colliding = self.coll_bounds.contains(mp)

        if not self.mouse_in and colliding:
            self.mouse_in = True
            self.water.on_mouse_collided(self.inx)
        elif self.mouse_in and not colliding:
            self.mouse_in = False

    def render(self, screen: pg.Surface):
        prev_rect = self.display_rect
        self.display_rect = pg.Rect(self.og_display_rect)

        # add sines to y pos
        for i, sine in enumerate(self.block_sines):
            val = sine.get_sine()
            if val is None:
                del self.block_sines[i]
                continue

            val = val / (i + 1)  # diminish older sines (so there's no insane stacking)
            self.display_rect.y -= val

        # display cube
        pg.draw.rect(screen, Colours.RED, self.coll_bounds)
        if prev_rect != self.display_rect:
            pg.draw.rect(screen, Colours.BLUE, prev_rect)  # behind block
        pg.draw.rect(screen, Colours.LIGHT_BLUE, self.display_rect)


class Water:
    def __init__(self, pos: Vec2, size: Vec2, block_size=4):
        self.pos: Vec2 = pos
        self.size: Vec2 = size

        self.blocks_size: int = block_size
        self.blocks: list[WaterBlock] = self.generate_blocks()

        self.ripples: list[Ripple] = []
        self.max_ripples: int = 22
        self.allowed_rebound: int = 10  # allows rebound if less than x ripples exist

    def generate_blocks(self) -> list[WaterBlock]:
        """ Generates the blocks for the water, from left to right """
        li = []
        num_blocks = math.ceil(self.size.x / self.blocks_size)

        for i in range(num_blocks):
            pos = Vec2(self.pos.x + (self.blocks_size * i), self.pos.y)
            li.append(WaterBlock(self, pos, self.blocks_size, i))
        return li

    def new_ripple(self, block_num, strength=5.0):
        """ Add new ripple to the water. Inserts at beginning of list """
        self.ripples.insert(0, Ripple(strength, block_num, len(self.blocks)))

    def on_mouse_collided(self, block_num):
        """ Event called when mouse collides with a block """
        total_ripples = len(self.ripples)
        if total_ripples < self.max_ripples:
            self.new_ripple(block_num)

    def update_ripple(self, ripple, ripple_inx, offset) -> bool:
        """ Progress ripple, giving sines and spawning rebound ripples if needed. Returns whether ripple was deleted """
        ripple_nums, on_ripple = ripple.get_next()
        if ripple_nums is None:
            del self.ripples[ripple_inx]
            return False

        # give next block new ripple
        for inx in ripple_nums:
            self.blocks[inx].new_sine(ripple.strength, offset)

            # rebound ripple if few enough ripples exist (and not old enough)
            on_water_edge = len(self.ripples) < self.allowed_rebound and (inx == 0 or inx == len(self.blocks) - 1)
            if on_ripple > 0 and on_water_edge:
                self.new_ripple(inx, ripple.strength)
        return True

    def update_all_ripples(self):
        """
        Progress every ripple
        Iterations are how many times the r should be progressed. Based on how much time since the r was last updated, and the r's speed.
        """
        for i, ripple in enumerate(self.ripples):
            ripple.accumulated_dt += time.time() - ripple.last_progressed
            iterations = math.floor(ripple.accumulated_dt / ripple.ripple_speed)

            for it in range(iterations):
                offset = ripple.ripple_speed * (iterations - it)
                if not self.update_ripple(ripple, i, offset):
                    break  # stop iterating if deleted

            ripple.last_progressed = time.time()
            ripple.accumulated_dt -= ripple.ripple_speed * iterations

    def update(self):
        self.update_all_ripples()

        for b in self.blocks:
            b.update()


    def render(self, screen: pg.Surface):
        for b in self.blocks:
            b.render(screen)
