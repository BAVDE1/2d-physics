from constants import *
from Vec2 import Vec2
from objects import Object, Box, Ball


class Manifold:
    """ 'A collection of points that represents an area in space' """
    def __init__(self, a: Object, b: Object):
        self.a = a
        self.b = b
        self.normal = Vec2(0, 0)
        self.penetration = 0

        self.collision_count = 0
        self.contacts: list[Vec2] = [Vec2(), Vec2()]

    def init_collision(self):
        """ Fills necessary attributes of this class depending upon the types of Objects that are colliding """
        a = int(isinstance(self.a, Ball))
        b = int(isinstance(self.b, Ball))
        functions = [
            [box_colliding_box, box_colliding_ball],
            [ball_colliding_box, ball_colliding_ball]
        ]

        # execute collision function
        functions[a][b](self, self.a, self.b)

    def resolve_collision(self):
        """ Apply impulse to solve collisions """
        if not self.collision_count:
            return
        rv: Vec2 = self.b.velocity - self.a.velocity  # relative vel

        contact_vel = rv.dot(self.normal)
        if contact_vel > 0:  # separating, do not collide
            return

        is_resting = rv.y ** 2 < Values.RESTING
        res = min(self.a.material.restitution, self.b.material.restitution)  # use smallest restitution
        # lower y restitution if object is resting on ground. Fixes jitter-ing objects
        res = Vec2(res, 0.0 if is_resting else res)

        # impulse scalar
        rebound_dir = -(res + 1)
        imp = Vec2(rebound_dir.x, rebound_dir.y) * contact_vel
        imp /= self.a.inv_mass + self.b.inv_mass

        impulse = self.normal * imp  # apply impulse

        # normal application of impulse (backward cause pygame)
        self.a.velocity -= impulse * self.a.inv_mass
        self.b.velocity += impulse * self.b.inv_mass

        if not self.a.static and not self.b.static:
            print(self.a.velocity, '\n', self.b.velocity)
            # print(along_normal > 0.002, along_normal, self.a.velocity, self.b.velocity)

    def positional_correction(self):
        """ Fix floating point errors (using linear projection) """
        correction = max(self.penetration - Forces.PENETRATION_ALLOWANCE, 0.0) / (self.a.mass + self.b.mass) * Forces.POSITIONAL_CORRECTION

        self.a.pos += self.normal * (self.a.inv_mass * correction)
        self.b.pos -= self.normal * (self.b.inv_mass * correction)

    def __repr__(self):
        return f'CH({self.a}, {self.b})'


def clamp(value, min_v, max_v):
    return max(min_v, min(max_v, value))


def ball_colliding_ball(m: Manifold, a: Ball, b: Ball):
    normal = b.pos - a.pos
    r = a.radius + b.radius

    # not colliding, ignore
    if normal.length_sq() >= r * r:
        return False

    dist = normal.length()
    m.collision_count += 1

    if dist == 0:  # they are on same pos (chose random value)
        m.normal.set(1, 0)
        m.penetration = a.radius
    else:
        m.normal = normal / dist  # normalise
        m.penetration = r - dist
    return True


def box_colliding_ball(m: Manifold, a: Box, b: Ball):
    inside = False
    b_size_h = a.size / 2
    x_extent, y_extent = b_size_h.x, b_size_h.y

    centre = (b.pos - b_size_h) - a.pos
    closest = Vec2(*centre.get())  # closest point on a to center of b

    # clamp to edges of box
    closest.x = clamp(closest.x, -x_extent, x_extent)
    closest.y = clamp(closest.y, -y_extent, y_extent)

    # centre of the circle is inside box
    if centre == closest:
        inside = True

        if abs(centre.x) > abs(centre.y):  # find closest axis
            closest.x = x_extent if closest.x > 0 else -x_extent  # x-axis is closer
        else:
            closest.y = y_extent if closest.y > 0 else -y_extent  # y-axis is closer

    # just like circle on circle collision
    normal = centre - closest
    r = b.radius

    # not colliding, ignore
    if normal.length_sq() >= r * r and not inside:
        return False

    dist = normal.length()
    m.collision_count += 1

    normal /= dist  # normalise
    m.normal = -normal if inside else normal  # flip the collision if inside
    m.penetration = r - dist
    return True


def ball_colliding_box(m: Manifold, a: Ball, b: Box):
    val = box_colliding_ball(m, b, a)
    m.normal.negate_self()  # reverse the normal (for the love of god do not forget this step)
    return val


def box_colliding_box(m: Manifold, a: Box, b: Box):
    a_size_h, b_size_h = a.size / 2, b.size / 2

    normal = (b.pos - a_size_h) - (a.pos - b_size_h)  # allows for different size boxes
    x_overlap = a_size_h.x + b_size_h.x - abs(normal.x)

    if x_overlap > 0:
        y_overlap = a_size_h.y + b_size_h.y - abs(normal.y)

        if y_overlap > 0:
            m.collision_count += 1
            # if not a.static and not b.static:
            #     print('x', x_overlap, 'y', y_overlap, 'n', normal)

            # use axis of the least penetration
            if x_overlap < y_overlap:  # push x
                x_normal = int(normal.x > 0) * 2 - 1
                m.normal = Vec2(x_normal, 0)
                m.penetration = x_overlap
            else:  # push y
                y_normal = int(normal.y > 0) * 2 - 1
                m.normal = Vec2(0, y_normal)
                m.penetration = y_overlap
            return True
    return False
