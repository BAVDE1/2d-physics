from game import Game
from constants import *

game: Game | None = None


def main():
    global game

    pg.init()
    pg.display.set_mode(pg.Vector2(GameValues.SCREEN_WIDTH * GameValues.RES_MUL, GameValues.SCREEN_HEIGHT * GameValues.RES_MUL))

    game = Game()
    game.main_loop()

    pg.quit()


if __name__ == "__main__":
    main()
