from controller.astar_car_controller import AstarCarController
from game_model.game_model import TrafficEnv
from gui.pyglet_gui import CarsWindow
from scenarios.scenarios import STARTING_SCENARIO, JUST_ONE_CAR


def main(players, roads, segmentation, debug=False, test=False, test_mode=None):
    game = TrafficEnv(players=players, roads=roads)
    controllers = [AstarCarController(game=game, player=i) for i in range(players)]

    CarsWindow(game, controllers, segmentation=segmentation, debug=debug, test=test, test_mode=test_mode)


if __name__ == '__main__':
    main(**JUST_ONE_CAR, debug=True, test=True, test_mode=["all"])
