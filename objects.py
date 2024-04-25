from constants import *
from Vec2 import Vec2


class Object:
    def __init__(self, pos: Vec2):
        self.pos = pos

        self.velocity = Vec2(0, 0)


class Ball(Object):
    def __init__(self, pos: Vec2, radius=7):
        super().__init__(pos)
        self.radius = radius

    def ball_colliding(self, ball):
        r = self.radius + ball.radius
        x_dis = ball.pos.x - self.pos.x
        y_dis = ball.pos.y - self.pos.y
        return x_dis**2 + y_dis**2 <= r**2

    def box_colliding(self, box):
        pass

    def render(self, screen: pg.Surface):
        pg.draw.circle(screen, Colours.WHITE, self.pos.get(), self.radius)


class Box(Object):
    def __init__(self, pos: Vec2, size: Vec2):
        super().__init__(pos)
        self.size = size

    @property
    def lower_pos(self):
        return self.pos + self.size

    def box_colliding(self, box):
        outside_x = self.pos.x > box.lower_pos.x or self.lower_pos.x < box.pos.x
        outside_y = self.pos.y > box.lower_pos.y or self.lower_pos.y < box.pos.y
        return not (outside_x or outside_y)

    def ball_colliding(self, ball):
        pass

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, Colours.WHITE, pg.Rect(self.pos.get(), self.size.get()))
