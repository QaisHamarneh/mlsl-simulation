from scenarios.scenarios import *
from controller.game_controller import GameController


def main(players, roads, segmentation, gui: bool=True, agent: bool=False, debug=False, test_mode=None):
    controller = GameController(gui=gui, roads=roads, npcs=players, agent=agent, debug=debug, test_mode=test_mode)
    controller.run_game()

if __name__ == '__main__':
    main(**STARTING_SCENARIO, gui=True, agent=False, debug=False, test_mode=['all'])
