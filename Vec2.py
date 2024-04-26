import math


class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def length(self):
        """ Magnitude (using sqrt) """
        return math.sqrt(self.length_sq())

    def length_sq(self):
        """ Length squared """
        return self.x * self.x + self.y * self.y

    def normalise(self):
        """ The vector with a length of 1 """
        length = self.length()
        return Vec2(self.x / length, self.y / length)

    def dot(self, vec):
        """ Dot product of this and vec """
        return self.x * vec.x + self.y * vec.y

    def get(self):
        """ Tuple conversion of Vec2 """
        return self.x, self.y

    def set(self, x, y):
        self.x = x
        self.y = y

    def add_dt(self, vec, dt):
        self.x = self.x + (vec.x * dt)
        self.y = self.y + (vec.y * dt)
        return self

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __mul__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x * other.x, self.y * other.y)
        return Vec2(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vec2(self.x / other.x, self.y / other.y)

    def __repr__(self):
        return f'Vec2({self.x}, {self.y})'
