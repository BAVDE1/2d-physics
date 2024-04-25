import math


class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def magnitude(self):
        """ length (using sqrt) """
        return math.sqrt((self.x ** 2) + (self.y ** 2))

    def normalise(self):
        """ The vector with a length of 1 """
        length = self.magnitude()
        return Vec2(self.x / length, self.y / length)

    def get(self):
        """ Tuple conversion of Vec2 """
        return self.x, self.y

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vec2(self.x * other.x, self.y * other.y)

    def __truediv__(self, other):
        return Vec2(self.x / other.x, self.y / other.y)

    def __repr__(self):
        return f'Vec2({self.x}, {self.y})'
