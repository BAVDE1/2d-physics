import math
import time

from constants import *


class Ripple:
    def __init__(self, strength, start_num, total_num):
        self.strength = strength
        self.start_num = start_num
        self.total_num = total_num

        self.generated = self.generate()

    def generate(self):
        sn = self.start_num
        li = [[sn]]
        for number in range(1, self.total_num):
            up = sn + number
            down = sn - number
            seg = []
            if sn < up < self.total_num:
                seg.append(up)
            if sn > down > -1:
                seg.append(down)
            if len(seg):
                li.append(seg)
        return li

    def get_next(self):
        return self.generated.pop(0) if len(self.generated) > 0 else None


class BlockSine:
    def __init__(self, strength):
        self.strength = strength

        self.started_time = time.time()
        self.max_time_alive = 2

    def get_sine(self):
        time_alive = time.time() - self.started_time
        time_left = self.max_time_alive - time_alive

        perc = time_left / self.max_time_alive
        sine = (self.strength * perc) * math.sin(8 * time_alive)
        return sine if time_left >= 0 else None


class WaterBlock:
    def __init__(self, wave, pos: Vec2, size, num):
        self.wave = wave
        self.num = num

        self.display_rect = pg.Rect(pos, [size] * 2)
        self.og_display_rect = pg.Rect(self.display_rect)

        self.coll_bounds = pg.Rect(self.display_rect.x, self.display_rect.y - size,
                                   self.display_rect.w, self.display_rect.h + (size * 2))
        self.mouse_in = False

        self.sines = []

        self.eg = False

    def new_sine(self, strength):
        self.eg = True
        self.sines.append(BlockSine(strength))

    def update(self):
        mp = pg.Rect(
            Vec2(pg.mouse.get_pos()[0] / GameValues.RES_MUL, pg.mouse.get_pos()[1] / GameValues.RES_MUL),
            [1, 1]
        )
        colliding = self.coll_bounds.contains(mp)

        if not self.mouse_in and colliding:
            self.mouse_in = True
            self.wave.mouse_collided(self.num)
        elif self.mouse_in and not colliding:
            self.mouse_in = False

    def render(self, screen: pg.Surface):
        # collision bounds
        pg.draw.rect(screen, Colours.RED, self.coll_bounds)

        # add sines to y pos
        self.display_rect = pg.Rect(self.og_display_rect)
        for i, sine in enumerate(self.sines):
            val = sine.get_sine()
            if val is None:
                del self.sines[i]
                continue

            self.display_rect.y -= val

        # display cube
        pg.draw.rect(screen, Colours.WHITE, self.display_rect)

        # visual example
        if self.eg:
            self.eg = False
            pg.draw.rect(screen, Colours.BLUE, self.display_rect)


class Water:
    def __init__(self, y_pos, left_x, right_x, block_size=5):
        self.pos: Vec2 = Vec2(left_x, y_pos)
        self.to_pos: Vec2 = Vec2(right_x, y_pos)

        self.blocks_size = block_size
        self.blocks = self.generate_blocks()

        self.ripples = []

    def generate_blocks(self):
        li = []
        diff = self.to_pos.x - self.pos.x
        num_blocks = math.ceil(diff / self.blocks_size)

        for i in range(num_blocks):
            pos = Vec2(self.pos.x + (self.blocks_size * i), self.pos.y)
            li.append(
                WaterBlock(self, pos, self.blocks_size, i)
            )
        return li

    def mouse_collided(self, block_num):
        total_ripples = len(self.ripples)
        if total_ripples < 5:
            strength = 5 - total_ripples
            self.ripples.append(Ripple(strength, block_num, len(self.blocks)))

    def update(self):
        for b in self.blocks:
            b.update()

        for i, ripple in enumerate(self.ripples):
            ripple_nums = ripple.get_next()
            if ripple_nums is None:
                del self.ripples[i]
                continue

            # give next block new sine
            for block in ripple_nums:
                self.blocks[block].new_sine(ripple.strength)

    def render(self, screen: pg.Surface):
        for b in self.blocks:
            b.render(screen)
