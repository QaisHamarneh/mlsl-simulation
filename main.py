from game_model.game_model import TrafficEnv
from gui.pyglet_gui import CarsWindow
from scenarios.scenarios import STARTING_SCENARIO, JUST_ONE_CAR, BIG_SCENARIO, TWO_CROSSING, LEFT_RIGHT_OVERTAKE_2
from controller.game_controller import GameControllerCLI, GameControllerGUI


def main(players, roads, segmentation, gui=True, debug=False, test=False, test_mode=None):
    if gui:
        controller = GameControllerGUI(players=players, roads=roads, segmentation=segmentation, debug=debug, test=test, test_mode=test_mode)
    else:
        controller = GameControllerCLI(players=players, roads=roads)
    controller.start()

if __name__ == '__main__':
    main(**TWO_CROSSING, gui=True, debug=False, test=False, test_mode=["all"])
