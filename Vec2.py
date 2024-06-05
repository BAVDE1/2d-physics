import math
from typing import Self

EPSILON = 0.0001
EPSILON_SQ = EPSILON ** 2


class Vec2:
    def __init__(self, x=0.0, y=0.0):
        self.x: float = x
        self.y: float = y

    def length(self) -> float:
        """ Magnitude (using sqrt) """
        return math.sqrt(self.length_sq())

    def length_sq(self) -> float:
        """ Length squared """
        return (self.x ** 2) + (self.y ** 2)

    def length_sq_other(self, other: Self) -> float:
        """ Finds distance and squares to find the length """
        v = Vec2(self.x - other.x, self.y - other.y)
        return (v.x ** 2) + (v.y ** 2)

    def normalise_self(self, x_only=False, y_only=False) -> Self:
        """ This vector with a length of 1 (in place) """
        length_sq = self.length_sq()
        if length_sq > EPSILON_SQ:
            inv_len = 1 / math.sqrt(length_sq)
            if not y_only:
                self.x *= inv_len
            if not x_only:
                self.y *= inv_len
        return self

    def dot(self, vec) -> float:
        """ Dot product of this and vec """
        return self.x * vec.x + self.y * vec.y

    def get(self) -> tuple:
        """ Tuple representation of Vec2 """
        return self.x, self.y

    def clone(self) -> Self:
        """ Return a clone of self """
        return Vec2(self.x, self.y)

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

    def negate(self) -> Self:
        """ Return new vector as a negative of self """
        return Vec2(-self.x, -self.y)

    def negate_self(self):
        """ Negate own x and y (in place) """
        self.x = -self.x
        self.y = -self.y

    def cross_fl(self, f: float) -> Self:
        """ Cross this and float, returns a new vec """
        return Vec2(self.y * f, self.x * -f)

    def cross_vec(self, other: Self) -> float:
        """ Cross product of self and vector (returns a scalar) """
        if isinstance(other, Vec2):
            return self.x * other.y - self.y * other.x
        raise TypeError('param (1) "other" is not of type "Vec2", cannot perform cross')

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


def cross_vec_float(v: Vec2, f: float) -> Vec2:
    """ Cross of Vec2 and float """
    if isinstance(v, Vec2) and isinstance(f, float):
        return Vec2(f * v.y, -f * v.x)
    raise TypeError('Parameter/s given are of an incorrect type')


def cross_float_vec(f: float, v: Vec2) -> Vec2:
    """ Cross of float and Vec2 """
    if isinstance(v, Vec2) and isinstance(f, float):
        return Vec2(-f * v.y, f * v.x)
    raise TypeError('Parameter/s given are of an incorrect type')
