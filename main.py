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

    # time stepping for deterministic physics
    while game.running:
        t = time.time()

        accumulator += t - frame_start
        frame_start = t

        # avoid spiral of death
        if accumulator > 1:
            accumulator = 1

        while accumulator >= Values.DT:
            accumulator -= Values.DT
            game.main_loop()

    pg.quit()


if __name__ == "__main__":
    main()
