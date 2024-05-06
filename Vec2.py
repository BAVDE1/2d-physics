import math


class Vec2:
    def __init__(self, x=0, y=0):
        self.x: int = x
        self.y: int = y

    def length(self):
        """ Magnitude (using sqrt) """
        return math.sqrt(self.length_sq())

    def length_sq(self):
        """ Length squared """
        return self.x ** 2 + self.y ** 2

    def normalise(self):
        """ This vector but with a length of 1 """
        length = self.length()
        return Vec2(self.x / length, self.y / length)

    def dot(self, vec):
        """ Dot product of this and vec """
        return self.x * vec.x + self.y * vec.y

    def get(self):
        """ Tuple representation of Vec2 """
        return self.x, self.y

    def clamp_self(self, min_v, max_v):
        """ Clamp vector between a min vec or int, and a max vec or int (in place) """
        if isinstance(min_v, Vec2) and isinstance(max_v, Vec2):
            self.x = max(min_v.x, min(max_v.x, self.x))
            self.y = max(min_v.y, min(max_v.y, self.y))
        else:
            self.x = max(min_v, min(max_v, self.x))
            self.y = max(min_v, min(max_v, self.y))

    def set(self, x=None, y=None):
        """ Set either x and/or y of this vector (in place) """
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y

    def set_vec(self, vec):
        """ Set either x and/or y of this vector (in place) """
        if isinstance(vec, Vec2):
            self.x = vec.x
            self.y = vec.y

    def add_self(self, vec, val: float):
        """ Multiply vec by val and add it to instance (in place) """
        if isinstance(vec, Vec2):
            self.x += vec.x * val
            self.y += vec.y * val

    def negate_self(self):
        """ Negate own x and y (in place) """
        self.x = -self.x
        self.y = -self.y

    def __add__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x + other.x, self.y + other.y)
        return Vec2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x - other.x, self.y - other.y)
        return Vec2(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x * other.x, self.y * other.y)
        return Vec2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x / other.x, self.y / other.y)
        return Vec2(self.x / other, self.y / other)

    def __eq__(self, other):
        return isinstance(other, Vec2) and self.get() == other.get()

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __repr__(self):
        return f'Vec2({self.x}, {self.y})'
