import math
import random

from constants import *
import time

from manifold import Manifold
from water import Water
from objects import Object, Ball, Box
from Vec2 import Vec2
from particle import Particle


def get_mp():
    """ Get mouse pos relative to the screen scale """
    return Vec2(*pg.mouse.get_pos()) / Values.RES_MUL


def holding_object(obj: Object, mp: Vec2):
    """ Reduce natural velocity and replace with a mouse force """
    if isinstance(obj, Box):
        mp -= obj.size / 2
    force = Vec2(mp.x - obj.pos.x, mp.y - obj.pos.y)

    obj.velocity *= Vec2(.8, .8)  # reduce natural velocity
    obj.apply_force(force * (obj.inv_mass * 100))


class Game:
    def __init__(self):
        self.running = True
        self.fps = 60
        self.clock = pg.time.Clock()
        self.keys = pg.key.get_pressed()
        self.prev_frame = self.delta_time = time.time()
        self.resolve_iterations = 2
        self.mp = get_mp()

        self.canvas_screen = pg.Surface(Vec2(Values.SCREEN_WIDTH, Values.SCREEN_HEIGHT).get())
        self.final_screen = pg.display.get_surface()

        self.water = Water(100, 50, 250)

        self.collisions: list[Manifold] = []

        self.o1 = Ball(Vec2(150, 50))
        self.o2 = Box(Vec2(170, 50))
        self.o3 = Ball(Vec2(180, 30))

        self.objects = [self.o1, self.o2, self.o3]
        self.particles: list[Particle] = []

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

                # reset objects
                if event.key == pg.K_r:
                    self.debug_reset()

            if event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()

            # mouse
            if event.type == pg.MOUSEBUTTONDOWN and pg.mouse.get_pressed()[0]:
                self.particles.append(Particle(self.mp, velocity=Vec2(random.randrange(-50, 50), random.randrange(-100, -50))))

            if event.type == pg.MOUSEBUTTONUP and not pg.mouse.get_pressed()[0]:
                pass

            # close game
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.running = False

    def debug_reset(self):
        self.o1 = Ball(Vec2(150, 50))
        self.o2 = Box(Vec2(170, 50))
        # self.o3 = Ball(Vec2(180, 30))
        self.objects = [self.o1, self.o2]

    def rotate_screen_blit(self, image, angle, pos: Vec2):
        rotated_image = pg.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=pos.get()).center)
        pg.draw.rect(self.canvas_screen, Colours.DARK_GREY, new_rect, 1)

        self.canvas_screen.blit(rotated_image, new_rect)

    def update_objects(self):
        self.collisions.clear()

        # init collisions
        for i, a in enumerate(self.objects):
            objs = list(self.objects)
            objs.pop(i)
            for b in objs:
                # ignore if both have inf mass
                if a.mass + b.mass == Forces.INF_MASS:
                    continue

                ch = Manifold(a, b)
                ch.init_collision()

                # new collision found, save
                if ch.collision_count > 0:
                    self.collisions.append(ch)

        # apply forces
        for obj in self.objects:
            obj.update_velocity(self.delta_time)

        # resolve collisions
        for it in range(self.resolve_iterations):
            for coll in self.collisions:
                coll.resolve_collision()

        # update objects
        for obj in self.objects:
            obj.update(self.delta_time)

        # correct positions
        for coll in self.collisions:
            coll.positional_correction()

        # clear forces
        for obj in self.objects:
            obj.force.set(0, 0)

    def update(self):
        self.water.update()

        # update particles
        for i, part in enumerate(self.particles):
            if part.should_del():
                del self.particles[i]
                continue
            part.update(self.delta_time)

        self.update_objects()

        # mouse object
        holding_object(self.o1, self.mp)

    def render(self):
        self.final_screen.fill(Colours.BG_COL)
        self.canvas_screen.fill(Colours.BG_COL)

        # render here
        self.water.render(self.canvas_screen)

        for part in self.particles:
            part.render(self.canvas_screen)

        for obj in self.objects:
            obj.render(self.canvas_screen)

        # outline
        pg.draw.rect(self.canvas_screen, Colours.WHITE, pg.Rect(1, 1, Values.SCREEN_WIDTH - 2, Values.SCREEN_HEIGHT - 2), 1)
        pg.draw.rect(self.canvas_screen, Colours.WHITE, pg.Rect(4, 4, Values.SCREEN_WIDTH - 8, Values.SCREEN_HEIGHT - 8), 2)

        # test renders
        self.rotate_screen_blit(self.img, self.img_rot, Vec2(50, 50))
        self.img_rot += 60 * self.delta_time

        # final
        scaled = pg.transform.scale(self.canvas_screen, Vec2(Values.SCREEN_WIDTH * Values.RES_MUL, Values.SCREEN_HEIGHT * Values.RES_MUL).get())
        self.final_screen.blit(scaled, (0, 0))
        pg.display.flip()

    def main_loop(self):
        while self.running:
            t = time.time()
            self.delta_time = t - self.prev_frame
            self.prev_frame = t
            self.mp = get_mp()

            self.events()
            self.update()
            self.render()

            self.clock.tick(self.fps)
            pg.display.set_caption("{} - fps: {:.2f}".format("2d physics", self.clock.get_fps()))
