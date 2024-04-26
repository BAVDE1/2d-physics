from game import Game
from constants import *

game: Game | None = None


def main():
    global game

    pg.init()
    pg.display.set_mode(pg.Vector2(Values.SCREEN_WIDTH * Values.RES_MUL, Values.SCREEN_HEIGHT * Values.RES_MUL))

    game = Game()
    game.main_loop()

    pg.quit()


if __name__ == "__main__":
    main()
