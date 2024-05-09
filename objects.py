import math

from constants import *
from Vec2 import Vec2


DEF_STATIC = False
DEF_MAT = Materials.TESTING
DEF_LAYER = 10


class Material:
    def __init__(self, mat: Materials):
        self.restitution = mat[Materials.REST]
        self.density = mat[Materials.DENS]

    def __repr__(self):
        return f'Material(rest: {self.restitution}, dens: {self.density})'


class Object:
    def __init__(self, pos: Vec2, static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        self._type = 'Object'
        self.pos = pos
        self.static = static
        self.colour = Colours.WHITE
        self.layer = layer

        self.velocity = Vec2(0, 0)
        self.force = Vec2(0, 0)
        self.static_friction = 0.5  # at rest
        self.dynamic_friction = 0.3  # already moving

        self.material = Material(material)
        self.mass = 0
        self.inv_mass = 0

        # texture
        self._outline_size = 2

    def apply_force(self, force: Vec2):
        """ Apply external force to object """
        self.force += force

    def apply_impulse(self, impulse: Vec2, contact_vec: Vec2):
        """ Apply given impulse to self (multiplied by inv_mass) """
        if not self.static:
            self.velocity.add_self(impulse, self.inv_mass)

    def is_out_of_bounds(self, check_top=False):
        """ Is object too far from screen bounds to be considered worth keeping alive """
        above = self.pos.y < 0 - Values.SCREEN_HEIGHT
        below = self.pos.y > Values.SCREEN_HEIGHT * 2
        left = self.pos.x < 0 - Values.SCREEN_WIDTH
        right = self.pos.x > Values.SCREEN_WIDTH * 2
        return below or left or right or (check_top and above)

    def static_correction(self):
        """ Reset velocity on static objects """
        if self.static:
            self.velocity.set(0, 0)

    def should_ignore_collision(self, b):
        """ Checks whether both are static OR on different layers and neither are static """
        both_static = self.static and b.static
        one_static = self.static or b.static
        not_on_layer = self.layer != b.layer
        return both_static or (not_on_layer and not one_static)

    def update_velocity(self, dt):
        """ Should be called twice - before updating pos and after - for each physics calculation """
        if not self.static:
            dt_h = dt * 0.5
            self.velocity.add_self(self.force, dt_h)  # external force

            self.velocity.add_self(Forces.GRAVITY, dt_h)
            self.velocity.add_self(Forces.AIR_VELOCITY, dt_h)

    def update(self, dt):
        """ See README on better dt """
        self.pos += self.velocity * dt

        self.update_velocity(dt)
        self.static_correction()

    def __repr__(self):
        return f'{self._type}(layer: {self.layer})'


class Circle(Object):
    def __init__(self, pos: Vec2, radius=5, static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        super().__init__(pos, static, material, layer)
        self._type = 'Ball'
        self.radius = radius

        # lowered friction
        self.static_friction = 0.1
        self.dynamic_friction = 0.05

        self.compute_mass()

    def compute_mass(self):
        mass = math.pi * self.radius * self.radius * self.material.density
        self.mass = Forces.INF_MASS if self.static else mass
        self.inv_mass = 0 if self.static else 1 / self.mass

    def render(self, screen: pg.Surface):
        ps = 1  # half of line size
        pg.draw.line(screen, self.colour,
                     Vec2(self.pos.x - ps, self.pos.y).get(), Vec2(self.pos.x - ps, self.pos.y - self.radius).get(), 2)
        pg.draw.circle(screen, self.colour, self.pos.get(), ps)
        pg.draw.circle(screen, self.colour, self.pos.get(), self.radius, 2)


class Square(Object):
    def __init__(self, pos: Vec2, size: Vec2 = Vec2(10, 10), static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        super().__init__(pos, static, material, layer)
        self._type = 'Box'
        self.size = size

        self.compute_mass()

    @property
    def lower_pos(self):
        return self.pos + self.size

    def compute_mass(self):
        mass = self.material.density * self.size.x * self.size.y
        self.mass = Forces.INF_MASS if self.static else mass
        self.inv_mass = 0 if self.static else 1 / self.mass

    def render(self, screen: pg.Surface):
        pg.draw.line(screen, self.colour, self.pos.get(), (self.lower_pos - 1).get())
        pg.draw.rect(screen, self.colour, pg.Rect(self.pos.get(), self.size.get()), self._outline_size)
