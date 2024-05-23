import math
from typing import Self

from constants import *


class Mat2:
    def __init__(self, radians=0.0):
        # m00, m01
        # m10, m11
        self.m00: float = 0
        self.m01: float = 0
        self.m10: float = 0
        self.m11: float = 0

        self.radians: float = radians

        self.refresh_matrix()

    def refresh_matrix(self):
        """ Update matrix values """
        cos: float = math.cos(self.radians)
        sin: float = math.sin(self.radians)

        self.m00 = cos
        self.m01 = -sin
        self.m10 = sin
        self.m11 = cos

    def set_rad(self, rad: float):
        """ Set radians & update matrix (in place) """
        self.radians = rad
        self.refresh_matrix()

    def add_rad(self, rad: float):
        """ Add radians to self & update matrix (in place) """
        self.radians += rad
        self.refresh_matrix()

    def clone(self) -> Self:
        """ Returns a copy of self """
        return Mat2(self.radians)

    def abs_self(self):
        """ Absolute self (in place) """
        self.abs(self)

    def abs(self, mat: Self = None) -> Self:
        """ Absolute copy of this matrix """
        if mat is None:
            mat = self.clone()

        mat.m00 = abs(mat.m00)
        mat.m01 = abs(mat.m01)
        mat.m10 = abs(mat.m10)
        mat.m11 = abs(mat.m11)

        return mat

    def mul_vec(self, vec: Vec2) -> Vec2:
        """ Returns a new vector rotated my this matrix """
        return Vec2(
            x=(self.m00 * vec.x) + (self.m01 * vec.y),
            y=(self.m10 * vec.x) + (self.m11 * vec.y)
        )

    def mul_mat_self(self, mat: Self) -> Self:
        """ Multiply self by given matrix, return new matrix """
        return mul_mat(self, mat)

    def transpose_self(self) -> Self:
        """ Set matrix to its transpose (in place) """
        m01 = self.m01
        self.m01 = self.m10
        self.m10 = m01
        return self

    def transpose(self) -> Self:
        """ Return a new matrix that is a transpose of this """
        mat = self.clone()
        mat.m01 = self.m10
        mat.m10 = self.m01
        return mat


def mul_mat(mat_a: Mat2, mat_b: Mat2) -> Mat2:
    """ Multiply matrix a by matrix b, and return new matrix """
    if isinstance(mat_a, Mat2) and isinstance(mat_b, Mat2):
        mat = Mat2()
        mat.m00 = (mat_a.m00 * mat_b.m00) + (mat_a.m01 * mat_b.m10)
        mat.m01 = (mat_a.m00 * mat_b.m01) + (mat_a.m01 * mat_b.m11)
        mat.m10 = (mat_a.m10 * mat_b.m00) + (mat_a.m11 * mat_b.m10)
        mat.m11 = (mat_a.m10 * mat_b.m01) + (mat_a.m11 * mat_b.m11)
        return mat
    else:
        raise TypeError("Given param\\s are not of type 'Mat22'")
