import math
import time

from constants import *
from Vec2 import Vec2


class Ripple:
    """
    Generates the block order that a ripple will travel (in both directions)
    """
    def __init__(self, strength, start_num, total_num):
        self.strength = strength
        self.strength_decay = 0.98

        self.start_num = start_num
        self.total_num = total_num

        self.generated = self.generate()
        self.on_ripple = -1

        self.end_cut_off = 1

    def generate(self):
        sn = self.start_num
        li = [[sn]]  # first ripple already there
        for number in range(1, self.total_num):
            up = sn + number
            down = sn - number
            seg = []
            if up < self.total_num:
                seg.append(up)
            if down > -1:
                seg.append(down)
            if len(seg):
                li.append(seg)
        return li

    def get_next(self):
        self.on_ripple += 1

        self.strength = self.strength * self.strength_decay
        # None if no more iterations or strength is too low
        val = None if len(self.generated) == 0 or self.strength < self.end_cut_off else self.generated.pop(0)
        return [val, self.on_ripple]


class BlockSine:
    """
    One ripple handled for one block
    """
    def __init__(self, strength):
        self.strength = strength

        self.started_time = time.time()
        self.max_time_alive = 0.8

    def get_sine(self):
        time_alive = time.time() - self.started_time
        time_left = self.max_time_alive - time_alive

        perc_completed = time_left / self.max_time_alive
        freq = 18 + (self.strength / 2)  # between 18 - 22
        sine = (self.strength * perc_completed) * math.sin(freq * time_alive)
        return sine if time_left >= 0 else None


class WaterBlock:
    def __init__(self, wave, pos: Vec2, size, num):
        self.wave = wave
        self.num = num

        self.display_rect = pg.Rect(pos.get(), [size] * 2)
        self.og_display_rect = pg.Rect(self.display_rect)

        margin = size * 1.5
        self.coll_bounds = pg.Rect(self.display_rect.x, self.display_rect.y - margin / 2,
                                   self.display_rect.w, self.display_rect.h + margin)
        self.mouse_in = False
        self.block_sines = []
        self.max_sines = 10

    def new_sine(self, strength):
        if strength > 0 and len(self.block_sines) < self.max_sines:
            self.block_sines.insert(0, BlockSine(strength))

    def update(self):
        mp = pg.Rect(
            Vec2(pg.mouse.get_pos()[0] / Values.RES_MUL, pg.mouse.get_pos()[1] / Values.RES_MUL).get(),
            [1, 1]
        )
        colliding = self.coll_bounds.contains(mp)

        if not self.mouse_in and colliding:
            self.mouse_in = True
            self.wave.mouse_collided(self.num)
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

        self.blocks_size = block_size
        self.blocks = self.generate_blocks()

        self.ripples = []
        self.max_ripples = 22
        self.allow_rebound = 10

    def generate_blocks(self):
        li = []
        num_blocks = math.ceil(self.size.x / self.blocks_size)

        for i in range(num_blocks):
            pos = Vec2(self.pos.x + (self.blocks_size * i), self.pos.y)
            li.append(WaterBlock(self, pos, self.blocks_size, i))
        return li

    def new_ripple(self, block_num, strength=5):
        self.ripples.insert(0, Ripple(strength, block_num, len(self.blocks)))

    def mouse_collided(self, block_num):
        total_ripples = len(self.ripples)
        if total_ripples < self.max_ripples:
            self.new_ripple(block_num)

    def update(self):
        for b in self.blocks:
            b.update()

        for i, ripple in enumerate(self.ripples):
            ripple_nums, on_ripple = ripple.get_next()
            if ripple_nums is None:
                del self.ripples[i]
                continue

            # give next block new ripple
            for block in ripple_nums:
                self.blocks[block].new_sine(ripple.strength)

                # rebound ripple if few enough ripples exist (and not on first ripple)
                if on_ripple > 0 and len(self.ripples) < self.allow_rebound and (block == 0 or block == len(self.blocks) - 1):
                    self.new_ripple(block, ripple.strength)

    def render(self, screen: pg.Surface):
        for b in self.blocks:
            b.render(screen)
