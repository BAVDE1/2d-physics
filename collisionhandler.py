from constants import *
from Vec2 import Vec2
from objects import Object, Box, Ball


class CollisionHandler:
    def __init__(self, a: Object, b: Object):
        self.a = a
        self.b = b
        self.normal = Vec2(0, 0)
        self.penetration = 0

        self.collision_count = 0

    def init_collision(self):
        """ Fills necessary attributes of this class """
        a = int(isinstance(self.a, Ball))
        b = int(isinstance(self.b, Ball))
        functions = [
            [box_colliding_box, box_colliding_ball],
            [ball_colliding_box, ball_colliding_ball]
        ]

        functions[a][b](self, self.a, self.b)

    def resolve_collision(self):
        """ Apply impulse to solve collisions """
        rv: Vec2 = self.b.velocity - self.a.velocity  # relative vel

        along_normal = rv.dot(self.normal)

        if along_normal > 0:  # separating, do not collide
            return

        res = min(self.a.restitution, self.b.restitution)  # use smallest restitution

        # inverted mass pre-compute
        inv_mass_a = 1 / self.a.mass
        inv_mass_b = 1 / self.b.mass

        # impulse scalar
        imp = -(1 + res) * along_normal
        imp /= inv_mass_a + inv_mass_b

        # apply impulse
        impulse = self.normal * imp

        # affect objects of smaller mass more
        # total_mass = inv_mass_a + inv_mass_b
        # ratio_a = inv_mass_a / total_mass  # use inverse mass?
        # ratio_b = inv_mass_b / total_mass  # ^^
        # self.a.velocity -= impulse * ratio_a
        # self.b.velocity += impulse * ratio_b

        # normal application of impulse
        self.a.velocity -= impulse * inv_mass_a
        self.b.velocity += impulse * inv_mass_b

    def __repr__(self):
        return f'CH({self.a}, {self.b})'


def ball_colliding_ball(c: CollisionHandler, a: Ball, b: Ball):
    normal = b.pos - a.pos
    r = a.radius + b.radius

    # not colliding, ignore
    if normal.length_sq() >= r * r:
        c.collision_count = 0
        return

    dist = normal.length()  # distance from each other's positions
    c.collision_count = 1

    if dist == 0:  # they are on same pos (chose random but consistent value)
        c.penetration = a.radius
        c.normal.set(1, 0)
    else:
        c.penetration = r - dist
        c.normal = normal / dist


def ball_colliding_box(c: CollisionHandler, a: Ball, b: Box):
    pass


def box_colliding_ball(c: CollisionHandler, a: Box, b: Ball):
    pass


def box_colliding_box(collision: CollisionHandler, a: Box, b: Box):
    outside_x = a.pos.x > b.lower_pos.x or a.lower_pos.x < b.pos.x
    outside_y = a.pos.y > b.lower_pos.y or a.lower_pos.y < b.pos.y
    return not (outside_x or outside_y)

