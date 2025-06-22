from scenarios.scenarios import *
from controller.game_controller import GameController


def main(players, roads, segmentation, gui=True, debug=False, test_mode=None):
    controller = GameController(gui=gui, roads=roads, players=players, debug=debug, test_mode=test_mode)
    controller.start()

if __name__ == '__main__':
    main(**TWO_CROSSING, gui=True, debug=False, test_mode=['all'])
