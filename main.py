from scenarios.scenarios import *
from controller.game_controller import GameController


def main(players, roads, segmentation, gui=True, debug=False, test_mode=None):
    controller = GameController(gui=gui, roads=roads, npcs=players, agents=2, debug=debug, test_mode=test_mode)
    controller.run_game()

if __name__ == '__main__':
    main(**CIRCUIT, gui=True, debug=False, test_mode=['all'])
