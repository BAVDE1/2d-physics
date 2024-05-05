import math
import random
import threading

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
        mp -= obj.size / 2  # middle of box

    max_f = Vec2(40, 40)
    force = Vec2(mp.x - obj.pos.x, mp.y - obj.pos.y) * Values.FPS / 60
    force.clamp_self(-max_f, max_f)
    force *= obj.mass

    obj.velocity *= Vec2(.85, .85)  # reduce natural velocity
    obj.apply_force(force * (obj.inv_mass * 100))


class Group:
    def __init__(self):
        self.layer_nums = {}  # amount of objects with layer x
        self.objects = []  # ordered by layers, low - high

    def add(self, o: Object):
        """ Add new layer to dict, insert object at end of objects' layer in list """
        if o.layer not in self.layer_nums:
            self.layer_nums[o.layer] = 0

        inx = 0
        for layer, amnt in self.layer_nums.items():
            if layer <= o.layer:
                inx += amnt

        self.objects.insert(inx, o)
        self.layer_nums[o.layer] += 1

    def add_mul(self, lis: list[Object]):
        for o in lis:
            self.add(o)

    def remove_at_index(self, inx, o=None):
        """ Fast method of removal """
        o: Object = o if o is not None else self.objects[inx]
        self.layer_nums[o.layer] -= 1

        if self.layer_nums[o.layer] <= 0:
            self.layer_nums.pop(o.layer)

        del self.objects[inx]
        return True

    def remove_obj(self, o: Object):
        """ Slow method of removal. Returns success on deletion """
        for i, obj in enumerate(self.objects):
            if obj == o:
                return self.remove_at_index(i, o=obj)
        return False


class Game:
    def __init__(self):
        self.running = True
        self.keys = pg.key.get_pressed()
        self.resolve_iterations = 8  # higher = more stable but less performant
        self.mp = get_mp()

        self.canvas_screen = pg.Surface(Vec2(Values.SCREEN_WIDTH, Values.SCREEN_HEIGHT).get())
        self.final_screen = pg.display.get_surface()

        self.water = Water(100, 50, 250)

        self.collisions: list[Manifold] = []

        # objects
        self.o1 = Ball(Vec2(10, 10), 10)
        self.o2 = Ball(Vec2(70, 60))
        self.o3 = Ball(Vec2(170, 10), 10)
        self.o4 = Ball(Vec2(130, 100), 20, layer=11)
        self.o5 = Box(Vec2(150, 60), Vec2(10, 10))
        self.o6 = Box(Vec2(132, 60), Vec2(10, 15))

        self.g1 = Box(Vec2(50, 160), size=Vec2(200, 10), static=True)
        self.g2 = Box(Vec2(50, 75), size=Vec2(10, 100), static=True)
        self.g3 = Box(Vec2(250, 75), size=Vec2(10, 100), static=True)

        self.objects_group = Group()
        self.objects_group.add_mul([self.o1, self.o2, self.o3, self.o4, self.o5, self.o6, self.g1, self.g2, self.g3])
        # self.objects = [self.o1, self.o2, self.o3, self.o4, self.o5, self.o6]
        # self.static_objects = [self.g1, self.g2, self.g3]
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

            if event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()

            # mouse
            if event.type == pg.MOUSEBUTTONDOWN and pg.mouse.get_pressed()[0]:
                self.particles.append(Particle(self.mp, velocity=Vec2(random.randrange(-50, 50), random.randrange(-100, -50))))

                for i in range(1):
                    b = Ball(Vec2(*self.mp.get()), 5, layer=2)
                    b.pos.y -= b.radius + 10
                    b.colour = [random.randrange(0, 255) for _ in range(3)]
                    self.objects_group.add(b)
                    print(len(self.objects_group.objects))

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

    def update_objects(self):
        self.collisions.clear()
        objects = self.objects_group.objects

        def should_ignore_collision(a: Object, b: Object):
            """ Checks whether both are static OR on different layers and neither are static """
            return (a.static and b.static) or ((a.layer != b.layer) and not (a.static or b.static))

        def init_collisions(objs, objs_b=None, identical_lists=True):
            objs_b = objs if objs_b is None else objs_b
            for ia, a in enumerate(objs):
                start = ia + 1 if identical_lists else 0  # avoid checking self if lists are identical

                for ib, b in enumerate(objs_b[start:]):
                    if should_ignore_collision(a, b):
                        continue

                    ch = Manifold(a, b)
                    ch.init_collision()

                    if ch.collision_count > 0:
                        self.collisions.append(ch)

        init_collisions(objects)

        # apply left-over velocity
        for obj in objects:
            obj.update_velocity(Values.DT)

        # resolve collisions, apply impulses
        for it in range(self.resolve_iterations):
            for coll in self.collisions:
                coll.resolve_collision()

        # apply velocity
        for obj in objects:
            obj.update(Values.DT)

        # correct positions
        for coll in self.collisions:
            coll.positional_correction()

        # conclusion
        for i, obj in enumerate(objects):
            obj.force.set(0, 0)

            if obj.is_out_of_bounds():
                self.objects_group.remove_at_index(i)

    def update_particles(self):
        for i, part in enumerate(self.particles):
            if part.should_del():
                del self.particles[i]
                continue
            part.update(Values.DT)

    def update(self):
        holding_object(self.o1, self.mp)

        self.water.update()

        self.update_particles()
        self.update_objects()
        print(self.objects_group.layer_nums)

    def render(self):
        self.final_screen.fill(Colours.BG_COL)
        self.canvas_screen.fill(Colours.BG_COL)

        # render here
        self.water.render(self.canvas_screen)

        for part in self.particles:
            part.render(self.canvas_screen)

        for obj in self.objects_group.objects:
            obj.render(self.canvas_screen)

        for coll in self.collisions:
            coll.render(self.canvas_screen)

        # outline
        pg.draw.rect(self.canvas_screen, Colours.BG_COL, pg.Rect((0, 0), (Values.SCREEN_WIDTH, Values.SCREEN_HEIGHT)), 5)
        pg.draw.rect(self.canvas_screen, Colours.WHITE, pg.Rect(1, 1, Values.SCREEN_WIDTH - 2, Values.SCREEN_HEIGHT - 2), 1)
        pg.draw.rect(self.canvas_screen, Colours.WHITE, pg.Rect(4, 4, Values.SCREEN_WIDTH - 8, Values.SCREEN_HEIGHT - 8), 2)

        # test renders
        self.rotate_screen_blit(self.img, self.img_rot, Vec2(50, 40))
        self.img_rot += 60 * Values.DT

        # final
        scaled = pg.transform.scale(self.canvas_screen, Vec2(Values.SCREEN_WIDTH * Values.RES_MUL, Values.SCREEN_HEIGHT * Values.RES_MUL).get())
        self.final_screen.blit(scaled, (0, 0))
        pg.display.flip()

    def main_loop(self):
        """ Called every on frame """
        self.mp = get_mp()

        self.events()
        self.update()
        self.render()
