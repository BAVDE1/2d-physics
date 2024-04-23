import math
import time

from constants import *


class WaveBlock:
    def __init__(self, wave, pos: Vec2, size, num):
        self.wave = wave
        self.num = num

        self.display_rect = pg.Rect(pos, [size] * 2)
        self.og_display_rect = pg.Rect(self.display_rect)

        self.coll_bounds = pg.Rect(self.display_rect.x, self.display_rect.y - size,
                                   self.display_rect.w, self.display_rect.h + (size * 2))
        self.mouse_in = False

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
        pg.draw.rect(screen, Colours.RED, self.coll_bounds)
        pg.draw.rect(screen, Colours.WHITE, self.display_rect)


class Wave:
    def __init__(self, y_pos, left_x, right_x, block_size=5):
        self.pos: Vec2 = Vec2(left_x, y_pos)
        self.to_pos: Vec2 = Vec2(right_x, y_pos)

        self.blocks_size = block_size
        self.blocks = self.generate_blocks()

    def generate_blocks(self):
        li = []
        diff = self.to_pos.x - self.pos.x
        num_blocks = math.ceil(diff / self.blocks_size)

        for i in range(num_blocks):
            pos = Vec2(self.pos.x + (self.blocks_size * i), self.pos.y)
            li.append(
                WaveBlock(self, pos, self.blocks_size, i)
            )
        return li

    def mouse_collided(self, block_num):
        print(block_num)

    def update(self):
        for b in self.blocks:
            b.update()

    def render(self, screen: pg.Surface):
        for b in self.blocks:
            b.render(screen)
