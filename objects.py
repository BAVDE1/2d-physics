from constants import *


class Ball:
    def __init__(self, pos: Vec2):
        self.radius = 8
        self.pos = pos

    def circle_colliding(self, ball):
        r = self.radius + ball.radius
        x_dis = ball.pos.x - self.pos.x
        y_dis = ball.pos.y - self.pos.y
        return x_dis**2 + y_dis**2 <= r**2

    def render(self, screen: pg.Surface):
        pg.draw.circle(screen, Colours.WHITE, self.pos, self.radius)


class Box:
    def __init__(self, pos: Vec2):
        self.rect = pg.Rect(pos, (10, 10))

    def box_colliding(self, box):
        outside_x = self.rect.left > box.rect.right or self.rect.right < box.rect.left
        outside_y = self.rect.top > box.rect.bottom or self.rect.bottom < box.rect.top
        return not (outside_x or outside_y)

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, Colours.WHITE, self.rect)
