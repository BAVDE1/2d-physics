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
        rv: Vec2 = self.b.velocity - self.a.velocity  # relative vel

        along_normal = rv.dot(self.normal)

        if along_normal > 0:  # separating, do not collide
            return

        res = min(self.a.restitution, self.b.restitution)  # use smallest restitution

        # impulse scalar
        imp = -(1 + res) * along_normal
        imp /= self.a.inv_mass + self.b.inv_mass

        # apply impulse
        impulse = self.normal * imp

        # affect objects of smaller mass more
        # total_mass = inv_mass_a + inv_mass_b
        # ratio_a = inv_mass_a / total_mass  # use inverse mass?
        # ratio_b = inv_mass_b / total_mass  # ^^
        # self.a.velocity -= impulse * ratio_a
        # self.b.velocity += impulse * ratio_b

        # normal application of impulse (backward cause pygame)
        self.a.velocity -= impulse * self.a.inv_mass
        self.b.velocity += impulse * self.b.inv_mass

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

    dist = normal.length()  # distance from each other's positions
    m.collision_count = 1

    if dist == 0:  # they are on same pos (chose random but consistent value)
        m.normal.set(1, 0)
        m.penetration = a.radius
    else:
        m.normal = normal / dist
        m.penetration = r - dist
    return True


def box_colliding_ball(m: Manifold, a: Box, b: Ball):
    b_size_h = a.size / 2

    norm = (b.pos - b_size_h) - a.pos
    closest = Vec2(*norm.get())  # closest point on a to center of b

    x_extent = b_size_h.x
    y_extent = b_size_h.y

    # clamp to edges of box
    closest.x = clamp(closest.x, -x_extent, x_extent)
    closest.y = clamp(closest.y, -y_extent, y_extent)

    inside = False

    # centre of the circle is inside box
    if norm == closest:
        inside = True

        # find closest axis
        if abs(norm.x) > abs(norm.y):  # x-axis is closer
            if closest.x > 0:
                closest.x = x_extent
            else:
                closest.x = -x_extent
        else:  # y-axis is closer
            if closest.y > 0:
                closest.y = y_extent
            else:
                closest.y = -y_extent

    # just like circle on circle collision
    normal = norm - closest
    r = b.radius

    # not colliding, ignore
    if normal.length_sq() >= r * r and not inside:
        return False

    dist = normal.length()
    m.collision_count = 1

    normal /= dist  # normalise (without another sqrt)
    m.normal = -normal if inside else normal  # flip the collision if inside
    m.penetration = r - dist
    return True


def ball_colliding_box(m: Manifold, a: Ball, b: Box):
    return box_colliding_ball(m, b, a)


def box_colliding_box(m: Manifold, a: Box, b: Box):
    a_size_h = a.size / 2
    b_size_h = b.size / 2

    normal = (b.pos - a_size_h) - (a.pos - b_size_h)  # allows for different size boxes
    x_overlap = a_size_h.x + b_size_h.x - abs(normal.x)

    if x_overlap > 0:
        y_overlap = a_size_h.y + b_size_h.y - abs(normal.y)

        if y_overlap > 0:
            m.collision_count = 1

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
