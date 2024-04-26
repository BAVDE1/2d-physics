import math

from constants import *
from Vec2 import Vec2


class Object:
    def __init__(self, pos: Vec2):
        self.type = 'Object'
        self.pos = pos

        self.velocity = Vec2(0, 0)
        self.force = Vec2(0, 0)
        self.restitution = 0.2  # elasticity
        self.density = 1.0
        self.mass = 0

    def apply_force(self, force: Vec2):
        self.force += force

    def apply_impulse(self):
        pass

    def update_velocity(self, dt):
        dt_h = dt * 0.5
        self.velocity.add_dt(self.force, self.mass * dt_h)  # mass * dt_h

        self.velocity.add_dt(Forces.GRAVITY, dt_h)
        self.velocity.add_dt(Forces.AIR_VELOCITY, dt_h)

    def update(self, dt):
        self.pos += self.velocity * dt  # -velocity cause pygame x&y is backwards :shrug:

        self.update_velocity(dt)

    def __repr__(self):
        return f'{self.type}({self.pos})'


class Ball(Object):
    def __init__(self, pos: Vec2, radius=7):
        super().__init__(pos)
        self.type = 'Ball'
        self.radius = radius

        self.mass = self.compute_mass()

    def compute_mass(self):
        return math.pi * self.radius * self.radius * self.density

    def render(self, screen: pg.Surface):
        ps = 1
        pg.draw.line(screen, Colours.WHITE,
                     Vec2(self.pos.x - ps, self.pos.y).get(), Vec2(self.pos.x - ps, self.pos.y - self.radius).get(), 2)
        pg.draw.circle(screen, Colours.WHITE, self.pos.get(), ps)
        pg.draw.circle(screen, Colours.WHITE, self.pos.get(), self.radius, 2)


class Box(Object):
    def __init__(self, pos: Vec2, size: Vec2):
        super().__init__(pos)
        self.type = 'Box'
        self.size = size

        self.mass = self.compute_mass()

    def compute_mass(self):
        return self.density * (self.size.x * self.size.y)

    @property
    def lower_pos(self):
        return self.pos + self.size

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, Colours.WHITE, pg.Rect(self.pos.get(), self.size.get()))
