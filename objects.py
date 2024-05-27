import math
import sys

from constants import *
from Vec2 import Vec2

DEF_STATIC = False
DEF_MAT = Materials.TESTING
DEF_LAYER = 10


class Material:
    def __init__(self, mat: Materials):
        self.restitution: float = mat[Materials.REST]
        self.density: float = mat[Materials.DENS]

    def __repr__(self):
        return f'Material(rest: {self.restitution}, dens: {self.density})'


class Object:
    def __init__(self, pos: Vec2, static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        self._object_type = 'Object'
        self._og_pos = pos.clone()
        self.pos: Vec2 = pos
        self.static: bool = static
        self.layer: int = layer

        # texture
        self.colour = Colours.WHITE

        # linear properties
        self.velocity: Vec2 = Vec2()
        self.force: Vec2 = Vec2()
        self.static_friction: float = 0.5  # at rest
        self.dynamic_friction: float = 0.3  # already moving

        # angular properties
        self.orientation: float = 0  # in radians
        self.angular_velocity: float = 0
        self.torque: float = 0
        self.mat2: Mat2 = Mat2(self.orientation)

        # mass
        self.material: Material = Material(material)
        self.mass: float = 0
        self.inv_mass: float = 0
        self.inertia: float = 0
        self.inv_inertia: float = 0

    def apply_force(self, force: Vec2):
        """ Apply external force to object """
        self.force += force

    def apply_impulse(self, impulse: Vec2, contact_vec: Vec2):
        """ Apply given impulse to self (multiplied by inv_mass) """
        if not self.static:
            self.velocity += impulse * self.inv_mass
            self.angular_velocity += self.inv_inertia * contact_vec.cross_vec(impulse)

    def update_velocity(self, dt):
        """ Should be called twice - before updating pos and after - for each physics calculation """
        if not self.static:
            dt_h = dt * 0.5
            self.velocity += self.force * dt_h  # external force

            self.velocity += Forces.GRAVITY * dt_h
            self.velocity += Forces.AIR_VELOCITY * dt_h

            self.angular_velocity += self.torque * self.inv_inertia * dt_h

    def set_orient(self):
        pass

    def update(self, dt):
        """ See README on better dt """
        self.pos += self.velocity * dt
        self.orientation += self.angular_velocity * dt
        self.set_orient()

        self.update_velocity(dt)
        self.static_correction()

    def is_point_in_obj(self, p: Vec2):
        return False

    def is_out_of_bounds(self, check_top=False) -> bool:
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
            self.angular_velocity = 0
            self.mat2.set_rad(0)

    def should_ignore_collision(self, b) -> bool:
        """ Checks whether both are static OR on different layers and neither are static """
        same_object = self == b
        both_static = self.static and b.static
        one_static = self.static or b.static
        not_on_layer = self.layer != b.layer
        return same_object or both_static or (not_on_layer and not one_static)

    def get_type(self):
        """ All objects should return of type 'Object' """
        return Object

    def __repr__(self):
        return f'{self._object_type}(static: {self.static}, layer: {self.layer}, pos: {self.pos})'


class Circle(Object):
    def __init__(self, pos: Vec2, radius=5, static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        super().__init__(pos, static, material, layer)
        self._object_type = 'Circle'
        self.radius: float = radius

        self.compute_mass()

    def compute_mass(self):
        mass = math.pi * self.radius * self.radius * self.material.density
        self.mass = Forces.INF_MASS if self.static else mass
        self.inv_mass = 0 if self.static else 1 / self.mass

        self.inertia = self.mass * self.radius * self.radius
        self.inv_inertia = 0 if self.static else 1 / self.inertia

    def is_point_in_obj(self, p: Vec2):
        dist = (p - self.pos).length()
        return dist < self.radius

    def render(self, screen: pg.Surface):
        r = self.radius - 1
        rot: Vec2 = Vec2(math.cos(self.orientation) * r, math.sin(self.orientation) * r)

        line_to: Vec2 = self.pos + rot
        pg.draw.line(screen, self.colour,
                     self.pos.get(), line_to.get(), 1)
        pg.draw.circle(screen, self.colour, self.pos.get(), self.radius, 1)


class Polygon(Object):
    MIN_VERTEX_COUNT = 3
    MAX_VERTEX_COUNT = 16

    def __init__(self, pos: Vec2, vertices=None, static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        super().__init__(pos, static, material, layer)
        self._object_type = 'Poly'
        self.vertex_count = 0
        self.vertices: list[Vec2] = []
        self.normals: list[Vec2] = []

        if vertices is not None:
            self.set(vertices)

    def compute_mass(self):
        """ Add all triangle areas of polygon for mass. Sets position to the centre of mass. """
        com = Vec2()  # centre of mass
        area = 0.0
        inertia = 0.0
        K_INV3: float = 1 / 3

        for i in range(self.vertex_count):
            v1: Vec2 = self.vertices[i]
            v2: Vec2 = self.vertices[(i + 1) % self.vertex_count]  # loop back to 0 if exceeding v count

            sq_area: float = v1.cross_vec(v2)
            tri_area = 0.5 * sq_area
            area += tri_area

            # Use area to weight the centroid average, not just vertex position
            weight: float = tri_area * K_INV3
            com += v1 * weight
            com += v2 * weight

            int_x2: float = (v1.x ** 2) + (v2.x * v1.x) + (v2.x ** 2)
            int_y2: float = (v1.y ** 2) + (v2.y * v1.y) + (v2.y ** 2)
            inertia += (.25 * K_INV3 * sq_area) * (int_x2 + int_y2)

        com *= 1 / area
        self.pos = self._og_pos + com  # move pos to com

        # translate vertices to centroid (centroid 0, 0)
        for i in range(self.vertex_count):
            self.vertices[i] -= com

        self.mass = abs(self.material.density * area)
        self.inv_mass = 0 if self.static else 1 / self.mass
        self.inertia = abs(inertia * self.material.density)
        self.inv_inertia = 0 if self.static else 1 / self.inertia

    def set(self, verts: list[Vec2]):
        """ Set vertices for polygon & (re) calculate the mass """
        # todo: validate allowed (no loops) polygon?
        self.vertices = verts
        self.vertex_count = len(verts)

        # compute normals for each face
        for i in range(self.vertex_count):
            face: Vec2 = self.vertices[(i + 1) % self.vertex_count] - self.vertices[i]

            normal = Vec2(face.y, -face.x)  # calculate normal with 2D cross product between vector and scalar
            self.normals.append(normal.normalise_self())

        self.compute_mass()

    def get_support(self, direction: Vec2) -> Vec2:
        """ Find objects furthest support point (vertex) along given direction """
        best_projection: float = -sys.float_info.max
        best_vertex: Vec2 = Vec2()

        for v in self.vertices:
            proj: float = v.dot(direction)

            if proj > best_projection:
                best_projection = proj
                best_vertex = v
        return best_vertex

    def is_point_in_obj(self, p1: Vec2):
        """
        Checks whether a point is within the polygon.
        Ray casts in direction from p1 to edge of screen, if number of faces passed though is odd, point is within poly
        """
        intersections = 0
        p2: Vec2 = Vec2(0, p1.y)

        for i in range(self.vertex_count):
            v1: Vec2 = self.get_oriented_vert(i)
            v2: Vec2 = self.get_oriented_vert((i + 1) % self.vertex_count)

            if do_lines_cross((p1, p2), (v1, v2)):
                intersections += 1
        return bool(intersections % 2)

    def get_oriented_vert(self, index: int) -> Vec2:
        """ Returns vertice at given index rotated to poly's mat2 in world space """
        return self.mat2.mul_vec(self.vertices[index]) + self.pos

    def set_orient(self):
        self.mat2.set_rad(self.orientation)

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, self.colour, pg.Rect(self.pos.get(), (1, 1)))  # com
        last_vertex: Vec2 = self.get_oriented_vert(-1)

        for i in range(self.vertex_count):
            vert: Vec2 = self.get_oriented_vert(i)
            pg.draw.line(screen, self.colour, last_vertex.get(), vert.get(), 1)
            last_vertex = vert


class SquarePoly(Polygon):
    def __init__(self, pos: Vec2, size=Vec2(1, 1), static=DEF_STATIC, material=DEF_MAT, layer=DEF_LAYER):
        self._object_type = 'SquarePoly'
        self.pos = pos
        self.size = size

        vertices = self.generate_vertices()
        super().__init__(pos, vertices, static, material, layer)

    def generate_vertices(self) -> list[Vec2]:
        """ Applies normals to size before adding to pos """
        return [
            Vec2(),
            self.size * Vec2(1, 0),
            self.size * Vec2(1, 1),
            self.size * Vec2(0, 1)
        ]
