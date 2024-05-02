import time

from game import Game
from constants import *

game: Game | None = None


def main():
    global game

    pg.init()
    pg.display.set_mode(pg.Vector2(Values.SCREEN_WIDTH * Values.RES_MUL, Values.SCREEN_HEIGHT * Values.RES_MUL))

    game = Game()

    accumulator = 0
    frame_start = time.time()
    current_fps = 0

    # time stepping for deterministic physics
    while game.running:
        t = time.time()

        accumulator += t - frame_start
        frame_start = t

        # avoid spiral of death
        if accumulator > .2:
            accumulator = .2

        while accumulator >= Values.DT:
            current_fps = Values.FPS / ((accumulator - (t - frame_start)) * Values.FPS)
            pg.display.set_caption("{} - fps: {:.3f}".format("2d physics", current_fps))

            accumulator -= Values.DT
            game.main_loop()

    pg.quit()


if __name__ == "__main__":
    main()
