import time

from constants import *
from Vec2 import Vec2


class Particle:
    def __init__(self, pos: Vec2,
                 colour=Colours.WHITE, size=Vec2(1, 1), velocity=Vec2(0, 0),
                 lifetime=1):
        self.pos = pos
        self.size = size

        self.colour = colour
        self.lifetime = lifetime
        self.alive = time.time()

        self.velocity = velocity

    @property
    def rect(self):
        return pg.Rect(self.pos.get(), self.size.get())

    def should_del(self):
        is_off_screen = self.pos.x > Values.SCREEN_WIDTH or self.pos.x < 0 or self.pos.y > Values.SCREEN_HEIGHT
        is_dead = time.time() - self.alive > self.lifetime
        return is_off_screen or is_dead

    def update_velocity(self, dt):
        dt_h = dt * 0.5
        self.velocity.add_dt(Forces.GRAVITY, dt_h)
        self.velocity.add_dt(Forces.AIR_VELOCITY, dt_h)

    def update(self, dt):
        self.update_velocity(dt)
        self.pos += self.velocity * dt
        self.update_velocity(dt)  # see README

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, self.colour, self.rect)

    def __repr__(self):
        return f'Particle({self.pos})'
