import math
import time

from constants import *


class WaveBlock:
    def __init__(self, wave, pos: Vec2, size, num):
        self.wave = wave
        self.num = num
        self.rect = pg.Rect(pos, [size] * 2)
        self.og_rect = pg.Rect(self.rect)

    def render(self, screen: pg.Surface):
        s = 2 * math.sin((2 * time.time()) + self.num)
        self.rect.y = self.og_rect.y + s
        pg.draw.rect(screen, Colours.WHITE, self.rect)


class Wave:
    def __init__(self, y_pos, left_x, right_x, blocks_num):

        self.pos: Vec2 = Vec2(left_x, y_pos)
        self.to_pos: Vec2 = Vec2(right_x, y_pos)
        self.blocks_num = blocks_num
        self.blocks = self.generate_blocks()

    def generate_blocks(self):
        li = []
        diff = self.to_pos.x - self.pos.x
        size = math.ceil(diff / self.blocks_num)
        print(diff, size)
        for i in range(self.blocks_num):
            pos = Vec2(self.pos.x + (size * i), self.pos.y)
            li.append(
                WaveBlock(self, pos, size, i)
            )

        return li

    def render(self, screen: pg.Surface):
        for b in self.blocks:
            b.render(screen)
