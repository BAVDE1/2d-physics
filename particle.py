from constants import *
from Vec2 import Vec2


class Particle:
    def __init__(self, pos: Vec2, colour=Colours.WHITE, size=Vec2(1, 1), velocity=Vec2(0, 0)):
        self.pos = pos
        self.size = size

        self.colour = colour

        self.velocity = velocity

    @property
    def rect(self):
        return pg.Rect(self.pos.get(), self.size.get())

    def is_off_screen(self):
        return self.pos.x > Values.SCREEN_WIDTH or self.pos.x < 0 or self.pos.y > Values.SCREEN_HEIGHT

    def update(self, dt):
        dt_h = dt * 0.5
        self.velocity.add_dt(Forces.GRAVITY, dt_h)
        self.velocity.add_dt(Forces.AIR_VELOCITY, dt_h)
        self.pos += self.velocity * dt

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, self.colour, self.rect)
