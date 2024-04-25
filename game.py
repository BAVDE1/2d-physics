import math

from constants import *
from water import Water
from objects import Ball, Box
from Vec2 import Vec2


class Game:
    def __init__(self):
        self.running = True
        self.fps = 60
        self.clock = pg.time.Clock()
        self.keys = pg.key.get_pressed()

        self.canvas_screen = pg.Surface(Vec2(GameValues.SCREEN_WIDTH, GameValues.SCREEN_HEIGHT).get())
        self.final_screen = pg.display.get_surface()

        self.water = Water(100, 50, 250)

        self.o1 = Box(Vec2(50, 150), Vec2(10, 10))
        self.o2 = Box(Vec2(70, 150), Vec2(10, 10))

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

    def render(self):
        self.final_screen.fill(Colours.BG_COL)
        self.canvas_screen.fill(Colours.BG_COL)

        # render here
        self.water.render(self.canvas_screen)

        # outline
        pg.draw.rect(self.canvas_screen, Colours.WHITE,
                     pg.Rect(1, 1, GameValues.SCREEN_WIDTH - 2, GameValues.SCREEN_HEIGHT - 2), 1)
        pg.draw.rect(self.canvas_screen, Colours.WHITE,
                     pg.Rect(4, 4, GameValues.SCREEN_WIDTH - 8, GameValues.SCREEN_HEIGHT - 8), 2)

        # test renders
        self.rotate_screen_blit(self.img, self.img_rot, Vec2(50, 50))
        self.img_rot += 1

        self.o1.pos = Vec2(
            math.floor(pg.mouse.get_pos()[0] / GameValues.RES_MUL),
            math.floor(pg.mouse.get_pos()[1] / GameValues.RES_MUL)
        )
        self.o1.render(self.canvas_screen)
        self.o2.render(self.canvas_screen)
        # self.o1.box_colliding(self.o2)
        print(self.o1.box_colliding(self.o2))

        # final
        scaled = pg.transform.scale(self.canvas_screen, Vec2(GameValues.SCREEN_WIDTH * GameValues.RES_MUL, GameValues.SCREEN_HEIGHT * GameValues.RES_MUL).get())
        self.final_screen.blit(scaled, (0, 0))

        pg.display.flip()

    def main_loop(self):
        while self.running:
            self.events()
            self.update()
            self.render()

            self.clock.tick(self.fps)
            pg.display.set_caption("{} - fps: {:.2f}".format("2d physics", self.clock.get_fps()))
