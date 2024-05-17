import math
import sys

from constants import *
from Vec2 import Vec2
from objects import Object, Circle, Polygon


class Manifold:
    """ 'A collection of points that represents an area in space' """
    def __init__(self, a: Object, b: Object):
        self.a: Object = a
        self.b: Object = b
        self.normal: Vec2 = Vec2()
        self.penetration: float = 0

        self.contact_count: int = 0
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
        if not self.contact_count:
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
        # j_vec += (self.a.mass + self.b.mass) * self.penetration

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
        for ci in range(self.contact_count):
            cp = self.contact_points[ci]
            if cp != Vec2(0, 0):
                rec_a = pg.Rect(cp.get(), (1, 1))
                pg.draw.line(screen, Colours.YELLOW, cp.get(), (cp + self.normal * 2).get())  # 2 pixel long line
                pg.draw.rect(screen, Colours.RED, rec_a)

    def __repr__(self):
        return f'CH({self.a}, {self.b})'


def clamp(value, min_v, max_v):
    return max(min_v, min(max_v, value))


def circle_colliding_circle(m: Manifold, c1: Circle, c2: Circle) -> bool:
    normal = c2.pos - c1.pos
    r = c1.radius + c2.radius

    # not colliding, ignore
    if normal.length_sq() >= r * r:
        return False

    dist = normal.length()
    m.contact_count = 1

    if dist == 0:  # they are on same pos (chose random value)
        m.normal.set(1, 0)
        m.penetration = c1.radius

        m.contact_points[0].set(*c1.pos.get())
    else:
        m.normal = normal / dist  # normalise
        m.penetration = r - dist

        cp_a = c1.pos + (m.normal * (c1.radius - m.penetration * .5))  # middle of penetration
        m.contact_points[0].set(*cp_a.get())
    return True


def circle_colliding_poly(m: Manifold, c: Circle, p: Polygon) -> bool:
    # circle center into polygon model space
    center: Vec2 = p.mat2.transpose().mul_vec(c.pos - p.pos)

    separation: float = -sys.float_info.max
    v_inx: int = 0
    for i in range(p.vertex_count):
        s: float = p.normals[i].dot(center - p.vertices[i])
        if s > c.radius:
            return False  # too far away, skip collision
        if s > separation:
            separation = s
            v_inx = i

    # face vertices
    v1: Vec2 = p.vertices[v_inx]
    v_inx2 = (v_inx + 1) % p.vertex_count  # next face
    v2: Vec2 = p.vertices[v_inx2]

    # if center within poly
    if separation < EPSILON:
        m.contact_count = 1
        m.normal = p.mat2.mul_vec(p.normals[v_inx]).negate()
        m.contact_points[0] = (m.normal * c.radius) + c.pos
        m.penetration = c.radius
        return True

    # Determine which voronoi region of the edge center of circle lies within
    dot1: float = (center - v1).dot(v2 - v1)
    dot2: float = (center - v2).dot(v1 - v2)
    m.penetration = c.radius - separation

    # get vertex furthest within c, or None if face should be used
    v: Vec2 = v1 if dot1 <= 0 else v2 if dot2 <= 0 else None
    if v is not None:
        if center.length_sq_other(v) > c.radius ** 2:
            return False

        m.normal = p.mat2.mul_vec(v - center).normalise_self()
        m.contact_points[0] = p.mat2.mul_vec(v) + p.pos
    else:  # face closest
        n: Vec2 = p.normals[v_inx]
        if (center - v1).dot(n) > c.radius:
            return False

        m.normal = p.mat2.mul_vec(n).negate()
        m.contact_points[0] = c.pos + (m.normal * c.radius)
    m.contact_count = 1
    return True


def poly_colliding_circle(m: Manifold, p: Polygon, c: Circle) -> bool:
    val = circle_colliding_poly(m, c, p)
    m.normal.negate_self()  # reverse the normal (for the love of god do not forget this step)
    return val


def poly_colliding_poly(m: Manifold, p1: Polygon, p2: Polygon) -> bool:
    # check for penetrating faces with both a and b polygons
    face_a_inx, pen_a = find_axis_penetration(p1, p2)
    if pen_a < 0.0:
        face_b_inx, pen_b = find_axis_penetration(p2, p1)
        if pen_b < 0.0:
            # polys are colliding, get collision values
            flip: bool = not greater_than(pen_a, pen_b)  # always a to b

            ref_poly: Polygon  # reference
            inc_poly: Polygon  # incident
            ref_poly, inc_poly = (p2, p1) if flip else (p1, p2)
            ref_inx: int = face_b_inx if flip else face_a_inx

            # get face vertices (in world space)
            inc_v1: Vec2
            inc_v2: Vec2
            inc_v1, inc_v2 = find_incident_face(ref_poly, inc_poly, ref_inx)
            ref_v1: Vec2
            ref_v2: Vec2
            ref_v1, ref_v2 = find_reference_face(ref_poly, ref_inx)

            side_plane_norm: Vec2 = (ref_v2 - ref_v1).normalise_self()
            ref_face_norm: Vec2 = Vec2(side_plane_norm.y, -side_plane_norm.x)  # orthogonal

            # c distance from origin
            ref_c: float = ref_face_norm.dot(ref_v1)
            neg_side: float = -side_plane_norm.dot(ref_v1)
            pos_side: float = side_plane_norm.dot(ref_v2)

            # Clip incident face to reference face side planes
            inc_v1, inc_v2, sp = clip(side_plane_norm.negate(), neg_side, inc_v1, inc_v2)
            if sp < 2:
                return False
            inc_v1, inc_v2, sp = clip(side_plane_norm, pos_side, inc_v1, inc_v2)
            if sp < 2:
                return False

            # flip
            m.normal = ref_face_norm.clone()
            if flip:
                m.normal.negate_self()

            # Keep points behind reference face
            cp: int = 0  # clipped points behind reference face
            separation: float = ref_face_norm.dot(inc_v1) - ref_c
            if separation <= 0:
                m.contact_points[cp] = inc_v1.clone()
                m.penetration = -separation
                cp += 1

            separation: float = ref_face_norm.dot(inc_v2) - ref_c
            if separation <= 0:
                m.contact_points[cp] = inc_v2.clone()
                m.penetration += -separation
                cp += 1

                m.penetration /= cp  # average
            m.contact_count = cp
            return True
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


def find_incident_face(ref_poly: Polygon, inc_poly: Polygon, ref_inx: int) -> tuple[Vec2, Vec2]:
    """ Returns face vertices on incident poly in world space """
    ref_norm: Vec2 = ref_poly.normals[ref_inx]

    # Calculate normal in incident's frame of reference
    ref_norm: Vec2 = ref_poly.mat2.mul_vec(ref_norm)  # world space
    ref_norm: Vec2 = inc_poly.mat2.transpose().mul_vec(ref_norm)  # inc model space

    # Find most anti-normal face on incident polygon
    inc_face: int = 0
    min_dot: float = sys.float_info.max
    for i in range(inc_poly.vertex_count):
        dot: float = ref_norm.dot(inc_poly.normals[i])

        if dot < min_dot:
            min_dot = dot
            inc_face = i

    # Assign face vertices for incident faces (transformed into world space by adding pos)
    face1: Vec2 = inc_poly.mat2.mul_vec(inc_poly.vertices[inc_face]) + inc_poly.pos
    inc_face = (inc_face + 1) % inc_poly.vertex_count  # next face
    face2: Vec2 = inc_poly.mat2.mul_vec(inc_poly.vertices[inc_face]) + inc_poly.pos
    return face1, face2


def find_reference_face(ref_poly: Polygon, ref_inx: int) -> tuple[Vec2, Vec2]:
    """ Returns face vertices on reference poly in world space """
    # Assign face vertices for ref faces
    # "x_poly.vertices[x_inx]" is model space, add poly pos to be world space
    face1: Vec2 = ref_poly.mat2.mul_vec(ref_poly.vertices[ref_inx]) + ref_poly.pos
    ref_inx = (ref_inx + 1) % ref_poly.vertex_count  # next face
    face2: Vec2 = ref_poly.mat2.mul_vec(ref_poly.vertices[ref_inx]) + ref_poly.pos
    return face1, face2


def clip(norm: Vec2, side: float, inc_face1: Vec2, inc_face2: Vec2) -> tuple[Vec2, Vec2, int]:
    """ Clip down the given faces to side length """
    i: int = 0
    faces = [inc_face1.clone(), inc_face2.clone()]

    # Retrieve distances from each endpoint to the line
    d1: float = norm.dot(inc_face1) - side
    d2: float = norm.dot(inc_face2) - side

    # If negative (behind plane) clip
    if d1 <= 0:
        faces[i] = inc_face1.clone()
        i += 1
    if d2 <= 0:
        faces[i] = inc_face2.clone()
        i += 1

    # If the points are on different sides of the plane
    if d1 * d2 < 0:
        alpha: float = d1 / (d2 - d1)
        faces[i] = (inc_face1 - inc_face2) * alpha
        faces[i] += inc_face1
        i += 1

    return faces[0], faces[1], i
