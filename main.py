from game_model.game_model import TrafficEnv
from gui.pyglet_gui import CarsWindow
from scenarios.scenarios import *
from controller.game_controller import GameControllerCLI, GameControllerGUI


def main(players, roads, segmentation, gui=True, debug=False, test_mode=None):
    if gui:
        controller = GameControllerGUI(players=players, roads=roads, debug=debug, test_mode=test_mode)
    else:
        controller = GameControllerCLI(players=players, roads=roads)
    controller.start()

if __name__ == '__main__':
    main(**TWO_CROSSING, gui=False, debug=False)
