import math
from constants import *
import time

from collisionhandler import CollisionHandler
from water import Water
from objects import Ball, Box
from Vec2 import Vec2


class Game:
    def __init__(self):
        self.running = True
        self.fps = 60
        self.clock = pg.time.Clock()
        self.keys = pg.key.get_pressed()
        self.prev_frame = self.delta_time = time.time()

        self.canvas_screen = pg.Surface(Vec2(Values.SCREEN_WIDTH, Values.SCREEN_HEIGHT).get())
        self.final_screen = pg.display.get_surface()

        self.water = Water(100, 50, 250)

        self.collisions: list[CollisionHandler] = []

        self.o1 = Ball(Vec2(150, 50))
        self.o2 = Ball(Vec2(170, 50))

        # TESTING STUFF
        self.img = pg.Surface((40, 40), pg.SRCALPHA)
        c = Colours.DARKER_GREY
        pg.draw.circle(self.img, c, (20, 20), 15, 7)
        pg.draw.rect(self.img, c, pg.Rect((self.img.get_width() / 2) - 5, 0, 10, 10))
        pg.draw.rect(self.img, c, pg.Rect((self.img.get_width() / 2) - 5, 30, 10, 10))
        pg.draw.rect(self.img, c, pg.Rect(0, (self.img.get_height() / 2) - 5, 10, 10))
        pg.draw.rect(self.img, c, pg.Rect(30, (self.img.get_height() / 2) - 5, 10, 10))
        self.img_rot = 0

    def events(self):
        for event in pg.event.get():
            # key input
            if event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()

            if event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()

            # mouse
            if event.type == pg.MOUSEBUTTONDOWN and pg.mouse.get_pressed()[0]:
                pass

            if event.type == pg.MOUSEBUTTONUP and not pg.mouse.get_pressed()[0]:
                pass

            # close game
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.running = False

    def rotate_screen_blit(self, image, angle, pos: Vec2):
        rotated_image = pg.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=pos.get()).center)
        pg.draw.rect(self.canvas_screen, Colours.DARK_GREY, new_rect, 1)

        self.canvas_screen.blit(rotated_image, new_rect)

    def update(self):
        self.water.update()

        # get collision info
        self.collisions.clear()
        objects = [self.o1, self.o2]
        for a_i in range(len(objects) - 1):
            a = objects[a_i]
            for b_i in range(len(objects) - 1):
                b = objects[b_i + a_i + 1]  # skip object a_i

                # ignore if both are static
                if a.mass == 0 and b.mass == 0:
                    continue

                ch = CollisionHandler(a, b)
                ch.solve_collision()

                # new collision found
                if ch.collision_count > 0:
                    self.collisions.append(ch)

        # apply forces
        for obj in objects:
            obj.update_velocity(self.delta_time)

        # resolve collisions
        for it in range(1):
            for coll in self.collisions:
                print(coll)
                coll.resolve_collision()

        # apply vel to pos
        for obj in objects:
            obj.update(self.delta_time)

        # correct positions

        # clear forces
        for obj in objects:
            obj.force.set(0, 0)

        m = Vec2(pg.mouse.get_pos()[0] / Values.RES_MUL, pg.mouse.get_pos()[1] / Values.RES_MUL)
        # force = Vec2(m.x - self.o1.pos.x, m.y - self.o1.pos.y)
        # self.o1.apply_force(force * 100)
        self.o1.pos = m

    def render(self):
        self.final_screen.fill(Colours.BG_COL)
        self.canvas_screen.fill(Colours.BG_COL)

        # render here
        self.water.render(self.canvas_screen)

        # outline
        pg.draw.rect(self.canvas_screen, Colours.WHITE,
                     pg.Rect(1, 1, Values.SCREEN_WIDTH - 2, Values.SCREEN_HEIGHT - 2), 1)
        pg.draw.rect(self.canvas_screen, Colours.WHITE,
                     pg.Rect(4, 4, Values.SCREEN_WIDTH - 8, Values.SCREEN_HEIGHT - 8), 2)

        objects = [self.o1, self.o2]
        for obj in objects:
            obj.render(self.canvas_screen)

        # test renders
        self.rotate_screen_blit(self.img, self.img_rot, Vec2(50, 50))
        self.img_rot += 1

        # final
        scaled = pg.transform.scale(self.canvas_screen, Vec2(Values.SCREEN_WIDTH * Values.RES_MUL, Values.SCREEN_HEIGHT * Values.RES_MUL).get())
        self.final_screen.blit(scaled, (0, 0))

        pg.display.flip()

    def main_loop(self):
        while self.running:
            t = time.time()
            self.delta_time = t - self.prev_frame
            self.prev_frame = t

            self.events()
            self.update()
            self.render()

            self.clock.tick(self.fps)
            pg.display.set_caption("{} - fps: {:.2f}".format("2d physics", self.clock.get_fps()))
