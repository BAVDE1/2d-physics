import sys

from constants import *
from Vec2 import Vec2
from objects import Object, Circle, Polygon

# fixed: second object (b) appears to gain velocity exponentially when colliding (object type disregarded)
# fixed: Poly:Poly collision does not seem to detect every collision (after rotation was implemented)
# done: IMPORTANT collisions inside objects are not resolving / not resolving properly (could fix other bugs)
# fixed: Poly:Poly collusion does not seem to apply impulse when rotating into another (sometimes)
# fixed: Once inside another object, objects do not actively push away from each other (not very much at least)
# fixed: Poly very slowly sinking into static Poly (could be fixed by above bug)


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

    def solve_collision(self):
        """
        Fills necessary values of this class (normal, pen, contact points) depending upon the types of Objects that are colliding
        """
        a = int(isinstance(self.a, Circle))
        b = int(isinstance(self.b, Circle))

        # execute collision function
        self.jump_table[a][b](self, self.a, self.b)

    def get_relative_velocity(self, ra: Vec2, rb: Vec2) -> Vec2:
        """ Return relative velocity (including angular vel) of objects """
        return ((self.b.velocity - rb.cross_fl(self.b.angular_velocity)) -
                (self.a.velocity - ra.cross_fl(self.a.angular_velocity)))

    def resolve_collision(self):
        """ Apply impulse on colliding objects to solve collisions """
        if not self.contact_count:
            return

        for i in range(self.contact_count):
            # relative values
            rel_a: Vec2 = self.contact_points[i] - self.a.pos
            rel_b: Vec2 = self.contact_points[i] - self.b.pos
            rel_vel: Vec2 = self.get_relative_velocity(rel_a, rel_b)

            contact_vel: float = rel_vel.dot(self.normal)
            if contact_vel > 0:  # separating, do not apply impulse
                return

            ra_cross_n: float = rel_a.cross_vec(self.normal)
            rb_cross_n: float = rel_b.cross_vec(self.normal)
            inv_masses: float = self.a.inv_mass + self.b.inv_mass + ((ra_cross_n ** 2) * self.a.inv_inertia) + ((rb_cross_n ** 2) * self.b.inv_inertia)

            # restitution & rebound
            is_resting = rel_vel.y ** 2 <= Values.RESTING
            restitution: float = min(self.a.material.restitution, self.b.material.restitution)  # coefficient of restitution
            restitution_vec: Vec2 = Vec2(restitution, 0.0 if is_resting else restitution)  # fix jitter-ing objects
            rebound_vec: Vec2 = -(restitution_vec + 1)

            # impulse
            impulse_scalar: Vec2 = Vec2(rebound_vec.x, rebound_vec.y) * contact_vel
            impulse_scalar /= inv_masses
            impulse_scalar /= self.contact_count

            impulse: Vec2 = self.normal * impulse_scalar
            self.a.apply_impulse(impulse.negate(), rel_a)
            self.b.apply_impulse(impulse, rel_b)

            # FRICTION IMPULSE
            rel_vel: Vec2 = self.get_relative_velocity(rel_a, rel_b)  # re-calculate after applying main impulse
            tan: Vec2 = rel_vel + (self.normal * -rel_vel.dot(self.normal))  # tangent
            tan.normalise_self()

            impulse_tan_scalar: float = -rel_vel.dot(tan)
            impulse_tan_scalar /= inv_masses
            impulse_tan_scalar /= self.contact_count

            if impulse_tan_scalar != 0:
                sf = math.sqrt(self.a.static_friction ** 2 + self.b.static_friction ** 2)

                # Coulumb's law
                if abs(impulse_tan_scalar) < impulse_scalar.x * sf:  # assumed at rest
                    tan_impulse = tan * impulse_tan_scalar
                else:  # already moving (energy of activation broken, less friction required)
                    df = math.sqrt(self.a.dynamic_friction ** 2 + self.b.dynamic_friction ** 2)
                    tan_impulse = (tan * impulse_scalar) * -df

                self.a.apply_impulse(tan_impulse.negate(), rel_a)
                self.b.apply_impulse(tan_impulse, rel_b)

    def positional_correction(self):
        """ Fix floating point errors (using linear projection) """
        correction = max(self.penetration - Forces.PENETRATION_ALLOWANCE, 0.0) / (self.a.inv_mass + self.b.inv_mass) * Forces.POSITIONAL_CORRECTION

        self.a.pos += self.normal * (-self.a.inv_mass * correction)
        self.b.pos += self.normal * (self.b.inv_mass * correction)

    def render(self, screen: pg.Surface):
        for i in range(self.contact_count):
            cp = self.contact_points[i]
            if cp != Vec2(0, 0):
                rec_a = pg.Rect(cp.get(), (1, 1))
                pg.draw.line(screen, Colours.YELLOW, cp.get(), (cp + self.normal * 2).get())  # 2 pixel-long line
                pg.draw.rect(screen, Colours.RED, rec_a)

    def __repr__(self):
        return f'CH({self.a}, {self.b})'


def circle_colliding_circle(m: Manifold, c1: Circle, c2: Circle) -> bool:
    normal = c2.pos - c1.pos
    radius = c1.radius + c2.radius

    # not colliding, ignore
    if normal.length_sq() >= radius * radius:
        return False

    dist = normal.length()
    m.contact_count = 1

    if dist == 0:  # they are on same pos (chose random value)
        m.normal.set(1, 0)
        m.penetration = c1.radius
        m.contact_points[0] = c1.pos.clone()
    else:
        m.normal = normal / dist  # normalise
        m.penetration = radius - dist
        m.contact_points[0] = (m.normal * c1.radius + c1.pos).clone()
    return True


def circle_colliding_poly(m: Manifold, c: Circle, p: Polygon) -> bool:
    # circle center into polygon model space
    center: Vec2 = p.mat2.transpose().mul_vec(c.pos - p.pos)

    separation: float = -sys.float_info.max
    v_inx: int = 0

    # find best separation within radius
    for i in range(p.vertex_count):
        s: float = p.normals[i].dot(center - p.vertices[i])
        if s > c.radius:
            return False  # too far away, skip collision
        if s > separation:
            separation = s
            v_inx = i

    # face vertices
    v1: Vec2 = p.vertices[v_inx]
    v2: Vec2 = p.vertices[(v_inx + 1) % p.vertex_count]  # next face

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
            inc_v1, inc_v2 = find_incident_face_vertices(ref_poly, inc_poly, ref_inx)
            ref_v1, ref_v2 = find_face_vertices(ref_poly, ref_inx)

            side_plane_norm: Vec2 = (ref_v2 - ref_v1).normalise_self()
            ref_face_norm: Vec2 = Vec2(side_plane_norm.y, -side_plane_norm.x)  # orthogonal

            # c distance from origin
            ref_c: float = ref_face_norm.dot(ref_v1)
            neg_side: float = -side_plane_norm.dot(ref_v1)
            pos_side: float = side_plane_norm.dot(ref_v2)

            # Clip incident face to reference face side planes
            inc_v1, inc_v2, sp = clip_faces(side_plane_norm.negate(), neg_side, inc_v1, inc_v2)
            if sp < 2:
                return False
            inc_v1, inc_v2, sp = clip_faces(side_plane_norm, pos_side, inc_v1, inc_v2)
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
    best_pen: float = -sys.float_info.max  # so (mostly) anything is greater than this
    best_inx: int = 0

    for i in range(a.vertex_count):
        normal: Vec2 = a.mat2.mul_vec(a.normals[i])

        # transform face normal into b's model space
        b_mat: Mat2 = b.mat2.transpose()
        b_oriented_norm: Vec2 = b_mat.mul_vec(normal)

        # support point
        support: Vec2 = b.get_support(b_oriented_norm.negate())

        # transform support vertex into b's model space
        vert: Vec2 = (a.get_oriented_vert(i)) - b.pos
        vert: Vec2 = b_mat.mul_vec(vert)

        # distance of penetration
        penetration: float = b_oriented_norm.dot(support - vert)

        # store biggest distance
        if penetration > best_pen:
            best_pen = penetration
            best_inx = i

    return best_inx, best_pen


def find_incident_face_vertices(ref_poly: Polygon, inc_poly: Polygon, ref_inx: int) -> tuple[Vec2, Vec2]:
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
    return find_face_vertices(inc_poly, inc_face)


def find_face_vertices(poly: Polygon, inx: int) -> tuple[Vec2, Vec2]:
    """ Returns the 2 face vertices on poly from inx given. transformed into world space """
    vert1: Vec2 = poly.get_oriented_vert(inx)
    vert2: Vec2 = poly.get_oriented_vert((inx + 1) % poly.vertex_count)
    return vert1, vert2


def clip_faces(norm: Vec2, side: float, inc_face1: Vec2, inc_face2: Vec2) -> tuple[Vec2, Vec2, int]:
    """ Clip down the given faces to side length. Returns faces & no. clips made """
    clip_no: int = 0
    faces = [inc_face1.clone(), inc_face2.clone()]

    # Retrieve distances from each endpoint to the line
    dist_1: float = norm.dot(inc_face1) - side
    dist_2: float = norm.dot(inc_face2) - side

    # If negative (behind plane) clip
    if dist_1 <= 0:
        faces[clip_no] = inc_face1.clone()
        clip_no += 1
    if dist_2 <= 0:
        faces[clip_no] = inc_face2.clone()
        clip_no += 1

    # If the points are on different sides of the plane
    if dist_1 * dist_2 < 0:
        alpha: float = dist_1 / (dist_2 - dist_1)
        faces[clip_no] = (inc_face1 - inc_face2) * alpha
        faces[clip_no] += inc_face1
        clip_no += 1

    return faces[0], faces[1], clip_no
