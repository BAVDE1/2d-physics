from constants import *
from Vec2 import Vec2


class Object:
    def __init__(self, pos: Vec2):
        self.pos = pos

        self.velocity = Vec2(0, 0)
        self.force = Vec2(0, 0)
        self.restitution = 0.2  # elasticity
        self.mass = 1

    def apply_force(self, force: Vec2):
        self.force += force

    def apply_impulse(self):
        pass

    def update_velocity(self, dt):
        dt_h = dt * 0.5
        self.velocity.add_dt(self.force, dt_h)  # mass * dt_h

        self.velocity.add_dt(-Forces.GRAVITY, dt_h)
        self.velocity.add_dt(-Forces.AIR_VELOCITY, dt_h)

    def update(self, dt):
        self.pos += self.velocity * dt

        self.update_velocity(dt)


class Ball(Object):
    def __init__(self, pos: Vec2, radius=7):
        super().__init__(pos)
        self.radius = radius

    def render(self, screen: pg.Surface):
        pg.draw.circle(screen, Colours.WHITE, self.pos.get(), self.radius)


class Box(Object):
    def __init__(self, pos: Vec2, size: Vec2):
        super().__init__(pos)
        self.size = size

    @property
    def lower_pos(self):
        return self.pos + self.size

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, Colours.WHITE, pg.Rect(self.pos.get(), self.size.get()))
