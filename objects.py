import math

from constants import *
from Vec2 import Vec2


class Material:
    def __init__(self, mat: Materials):
        self.restitution = mat[Materials.REST]
        self.density = mat[Materials.DENS]

    def __repr__(self):
        return f'Material(rest: {self.restitution}, dens: {self.density})'


class Object:
    def __init__(self, pos: Vec2, static=False, material=Materials.TESTING):
        self.type = 'Object'
        self.pos = pos
        self.outline = 2
        self.static = static

        self.velocity = Vec2(0, 0)
        self.force = Vec2(0, 0)

        self.material = Material(material)
        self.mass = 0
        self.inv_mass = 0

    def apply_force(self, force: Vec2):
        self.force += force

    def apply_impulse(self):
        pass

    def update_velocity(self, dt):
        if not self.static:
            def integrate(force: Vec2, _dt):
                """ Using Symplectic Euler """
                acceleration = force * (1 / self.mass)
                self.velocity.add_dt(acceleration, _dt)

            dt_h = dt * 0.5
            # integrate(self.force, self.mass * dt_h)  # external force
            self.velocity.add_dt(self.force, self.mass * dt_h)  # external force

            # integrate(Forces.GRAVITY, dt_h)
            # integrate(Forces.AIR_VELOCITY, dt_h)
            self.velocity.add_dt(Forces.GRAVITY, dt_h)
            self.velocity.add_dt(Forces.AIR_VELOCITY, dt_h)

    def update(self, dt):
        self.pos += self.velocity * dt

        # see README on better gravity
        self.update_velocity(dt)  # update velocity again after pos update

    def __repr__(self):
        return f'{self.type}({self.pos})'


class Ball(Object):
    def __init__(self, pos: Vec2, radius=7, static=False, material=Materials.TESTING):
        super().__init__(pos, static, material)
        self.type = 'Ball'
        self.radius = radius

        self.mass = Forces.INF_MASS if static else self.compute_mass()
        self.inv_mass = 0 if static else 1 / self.mass

    def compute_mass(self):
        return math.pi * self.radius * self.radius * self.material.density

    def render(self, screen: pg.Surface):
        ps = 1
        pg.draw.line(screen, Colours.WHITE,
                     Vec2(self.pos.x - ps, self.pos.y).get(), Vec2(self.pos.x - ps, self.pos.y - self.radius).get(), 2)
        pg.draw.circle(screen, Colours.WHITE, self.pos.get(), ps)
        pg.draw.circle(screen, Colours.WHITE, self.pos.get(), self.radius, 2)


class Box(Object):
    def __init__(self, pos: Vec2, size: Vec2 = Vec2(10, 10), static=False, material=Materials.TESTING):
        super().__init__(pos, static, material)
        self.type = 'Box'
        self.size = size

        self.mass = Forces.INF_MASS if static else self.compute_mass()
        self.inv_mass = 0 if static else 1 / self.mass

    @property
    def lower_pos(self):
        return self.pos + self.size

    def compute_mass(self):
        return self.material.density * self.size.x * self.size.y

    def render(self, screen: pg.Surface):
        pg.draw.line(screen, Colours.WHITE, self.pos.get(), (self.lower_pos - 1).get())
        pg.draw.rect(screen, Colours.WHITE, pg.Rect(self.pos.get(), self.size.get()), self.outline)
