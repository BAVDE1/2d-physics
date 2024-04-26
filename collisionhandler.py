from constants import *
from Vec2 import Vec2
from objects import Object, Box, Ball


class CollisionHandler:
    def __init__(self, a: Object, b: Object):
        self.a = a
        self.b = b
        self.normal = Vec2(0, 0)
        self.penetration = 0

        self.handler_func = None  # function

        self.collision_count = 0
        self.collisions = []

    def solve_collision(self):
        if isinstance(self.a, Ball):
            if isinstance(self.b, Ball):
                self.handler_func = ball_colliding_ball

        self.handler_func(self, self.a, self.b)

    def resolve_collision(self):
        rv: Vec2 = self.a.velocity - self.b.velocity  # relative vel

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
        total_mass = self.a.mass + self.b.mass
        ratio_a = self.a.mass / total_mass  # use inverse mass?
        ratio_b = self.b.mass / total_mass  # ^^
        self.a.velocity -= impulse * ratio_a
        self.b.velocity += impulse * ratio_b


def ball_colliding_ball(c: CollisionHandler, a: Ball, b: Ball):
    normal = b.pos - a.pos

    dist_sq = normal.length_sq()
    r = a.radius + b.radius

    # not colliding, ignore
    if dist_sq >= r * r:
        c.collision_count = 0
        return

    dist = normal.length()  # distance from each other's positions
    c.collision_count = 1

    if dist == 0:  # no distance, they currently have the same pos
        c.penetration = a.radius
        c.normal.set(1, 0)
        # add new contact
    else:
        c.penetration = r - dist
        c.normal.set(normal.x / dist, normal.y / dist)
        # add new contact


def box_colliding_box(collision: CollisionHandler, a: Box, b: Box):
    outside_x = a.pos.x > b.lower_pos.x or a.lower_pos.x < b.pos.x
    outside_y = a.pos.y > b.lower_pos.y or a.lower_pos.y < b.pos.y
    return not (outside_x or outside_y)

