import math
import sys

from constants import *
from Vec2 import Vec2
from objects import Object, Circle, Polygon


class Manifold:
    """ 'A collection of points that represents an area in space' """
    def __init__(self, a: Object, b: Object):
        self.a = a
        self.b = b
        self.normal = Vec2(0, 0)
        self.penetration = 0

        self.collision_count = 0
        self.contact_points: list[Vec2] = [Vec2(), Vec2()]

        self.jump_table = [
            [poly_colliding_poly, poly_colliding_circle],
            [circle_colliding_poly, circle_colliding_circle]
        ]

    def init_collision(self):
        """
        Fills necessary values of this class (normal, pen, contact points) depending upon the types of Objects that are colliding
        """
        a = int(isinstance(self.a, Circle))
        b = int(isinstance(self.b, Circle))

        # execute collision function
        self.jump_table[a][b](self, self.a, self.b)

    def resolve_collision(self):
        """ Apply impulse on colliding objects to solve collisions """
        if not self.collision_count:
            return

        # relative values
        ra: Vec2 = self.contact_points[0] - self.a.pos
        rb: Vec2 = self.contact_points[1] - self.b.pos
        rv: Vec2 = self.b.velocity - self.a.velocity

        contact_vel = rv.dot(self.normal)
        if contact_vel > 0:  # separating, do not collide
            return

        inv_masses = self.a.inv_mass + self.b.inv_mass

        e: float = min(self.a.material.restitution, self.b.material.restitution)  # coefficient of restitution
        is_resting = rv.y ** 2 < Values.RESTING
        e_vec: Vec2 = Vec2(e, 0.0 if is_resting else e)  # fix jitter-ing objects

        j: float = -(e + 1) * contact_vel
        j /= inv_masses
        rebound_dir_vec: Vec2 = -(e_vec + 1)
        j_vec: Vec2 = Vec2(rebound_dir_vec.x, rebound_dir_vec.y) * contact_vel
        j_vec /= inv_masses

        # if object is getting squished between a static, or high mass object, penetration will be high, raise scalar
        j_vec += (self.a.mass + self.b.mass) * self.penetration

        # normal application of impulse (backward cause pygame)
        impulse: Vec2 = j_vec * self.normal
        self.a.apply_impulse(impulse.negate(), ra)
        self.b.apply_impulse(impulse, rb)

        # FRICTION IMPULSE
        t: Vec2 = rv  # tangent
        t += self.normal * -rv.dot(self.normal)
        t.normalise_self()

        jt: float = -rv.dot(t)  # impulse tangent
        jt /= inv_masses

        if jt != 0:
            sf = math.sqrt(self.a.static_friction ** 2 + self.b.static_friction ** 2)

            # Coulumb's law
            if abs(jt) < j * sf:  # assumed at rest
                t_impulse = t * jt
            else:  # already moving (energy of activation broken, less friction required)
                df = math.sqrt(self.a.dynamic_friction ** 2 + self.b.dynamic_friction ** 2)
                t_impulse = (t * j) * -df

            self.a.apply_impulse(t_impulse.negate(), ra)
            self.b.apply_impulse(t_impulse, rb)

    def positional_correction(self):
        """ Fix floating point errors (using linear projection) """
        correction = max(self.penetration - Forces.PENETRATION_ALLOWANCE, 0.0) / (self.a.mass + self.b.mass) * Forces.POSITIONAL_CORRECTION

        self.a.pos += self.normal * (self.a.inv_mass * correction)
        self.b.pos += self.normal * (-self.b.inv_mass * correction)

    def render(self, screen: pg.Surface):
        for ci in range(self.collision_count):
            cp = self.contact_points[ci]
            if cp != Vec2(0, 0):
                rec_a = pg.Rect(cp.get(), (1, 1))
                pg.draw.line(screen, Colours.YELLOW, cp.get(), (cp + self.normal * 2).get())  # 2 pixel long line
                pg.draw.rect(screen, Colours.RED, rec_a)

    def __repr__(self):
        return f'CH({self.a}, {self.b})'


def clamp(value, min_v, max_v):
    return max(min_v, min(max_v, value))


def circle_colliding_circle(m: Manifold, a: Circle, b: Circle):
    normal = b.pos - a.pos
    r = a.radius + b.radius

    # not colliding, ignore
    if normal.length_sq() >= r * r:
        return False

    dist = normal.length()
    m.collision_count = 1

    if dist == 0:  # they are on same pos (chose random value)
        m.normal.set(1, 0)
        m.penetration = a.radius

        m.contact_points[0].set(*a.pos.get())
    else:
        m.normal = normal / dist  # normalise
        m.penetration = r - dist

        cp_a = a.pos + (m.normal * (a.radius - m.penetration * .5))  # middle of penetration
        m.contact_points[0].set(*cp_a.get())
    return True


def poly_colliding_circle(m: Manifold, a: Polygon, b: Circle):
    # inside = False
    # b_size_h = a.size / 2
    # x_extent, y_extent = b_size_h.x, b_size_h.y
    #
    # centre = (b.pos - b_size_h) - a.pos
    # closest = centre.clone()  # closest point on a to center of b
    #
    # # clamp to edges of box
    # closest.x = clamp(closest.x, -x_extent, x_extent)
    # closest.y = clamp(closest.y, -y_extent, y_extent)
    #
    # # centre of the circle is inside box
    # if centre == closest:
    #     inside = True
    #
    #     if abs(centre.x) > abs(centre.y):  # find closest axis
    #         closest.x = x_extent if closest.x > 0 else -x_extent  # x-axis is closer
    #     else:
    #         closest.y = y_extent if closest.y > 0 else -y_extent  # y-axis is closer
    #
    # # just like circle on circle collision
    # normal = centre - closest
    # r = b.radius
    #
    # # not colliding, ignore
    # if normal.length_sq() >= r * r and not inside:
    #     return False
    #
    # dist = normal.length()
    # m.collision_count = 1
    #
    # normal /= dist  # normalise
    # m.normal = -normal if inside else normal  # flip the collision if inside
    # m.penetration = r - dist
    # m.contact_points[0].set_vec(b.pos - (m.normal * b.radius))
    # return True
    return False


def circle_colliding_poly(m: Manifold, a: Circle, b: Polygon):
    val = poly_colliding_circle(m, b, a)
    m.normal.negate_self()  # reverse the normal (for the love of god do not forget this step)
    return val


def poly_colliding_poly(m: Manifold, a: Polygon, b: Polygon):
    # check for penetrating faces with both a and b polygons
    face_a_inx, pen_a = find_axis_penetration(a, b)
    if pen_a >= 0.0:
        return

    face_b_inx, pen_b = find_axis_penetration(b, a)
    if pen_b >= 0.0:
        return

    # polys are colliding, get collision values
    flip: bool = not greater_than(pen_a, pen_b)  # always a to b

    ref_poly: Polygon
    inc_poly: Polygon
    ref_poly, inc_poly = (b, a) if flip else (a, b)
    ref_inx: int = face_b_inx if flip else face_a_inx


    # a_size_h, b_size_h = a.size / 2, b.size / 2
    #
    # normal = (b.pos - a_size_h) - (a.pos - b_size_h)  # allows for different size boxes
    # x_overlap = a_size_h.x + b_size_h.x - abs(normal.x)
    #
    # if x_overlap > 0:
    #     y_overlap = a_size_h.y + b_size_h.y - abs(normal.y)
    #
    #     if y_overlap > 0:
    #         cp = 0
    #         cp += 2
    #
    #         # use axis of the least penetration
    #         if x_overlap < y_overlap:  # push x
    #             x_normal = int(normal.x > 0) * 2 - 1
    #             m.normal = Vec2(x_normal, 0)
    #             m.penetration = x_overlap
    #
    #             m.contact_points[0].set_vec((a.pos - b.pos) - normal)
    #         else:  # push y
    #             y_normal = int(normal.y > 0) * 2 - 1
    #             m.normal = Vec2(0, y_normal)
    #             m.penetration = y_overlap
    #
    #             m.contact_points[0].set_vec((a.pos - b.pos) - normal)
    #         # m.contact_points[0].set_vec(a.pos + y_overlap)
    #         m.collision_count = cp
    #         return True
    return False


def find_axis_penetration(a: Polygon, b: Polygon) -> tuple[int, float]:
    """ Find axis (vertex of polygon a) of the least penetration (with polygon b) and return the vertex index & penetration distance """
    best_dist: float = -sys.float_info.max  # so (mostly) anything is greater than this
    best_inx: int = 0

    for i in range(a.vertex_count):
        norm: Vec2 = a.normals[i]

        # transform face normal into b's model space
        b_mat: Mat2 = b.mat2.transpose()
        n: Vec2 = b_mat.mul_vec(norm)

        # support point
        support: Vec2 = b.get_support(n.negate())

        # transform support vertex into b's model space
        vert: Vec2 = (a.mat2.mul_vec(a.vertices[i]) + a.pos) - b.pos
        vert: Vec2 = b_mat.mul_vec(vert)

        # distance of penetration
        dist: float = n.dot(support - vert)

        # store biggest distance
        if dist > best_dist:
            best_dist = dist
            best_inx = i

    return best_inx, best_dist
