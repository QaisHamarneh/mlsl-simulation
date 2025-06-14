from game_model.game_model import TrafficEnv
from gui.pyglet_gui import CarsWindow
from scenarios.scenarios import STARTING_SCENARIO, JUST_ONE_CAR, BIG_SCENARIO, TWO_CROSSING, LEFT_RIGHT_OVERTAKE_2


def main(players, roads, segmentation, debug=False, test=False, test_mode=None):
    game = TrafficEnv(players=players, roads=roads)

    CarsWindow(game, segmentation=segmentation, debug=debug, test=test, test_mode=test_mode)


if __name__ == '__main__':
    main(**TWO_CROSSING, debug=False, test=False, test_mode=["all"])
