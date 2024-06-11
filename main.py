import random

from game_model.car import Car
from game_model.constants import *
from controller.astar_car_controller import AstarCarController
from game_model.game_model import TrafficEnv
from game_model.road_network import Direction, Goal
from gui.pyglet_gui import CarsWindow
from scenarios import RIGHT_OVERTAKE, STARTING_SCENARIO, ONE_ROAD, HORIZONTAL_VERTICAL


def main(players, roads, segmentation, debug=False):
    game = TrafficEnv(players=players, roads=roads)
    controllers = [AstarCarController(game=game, player=i) for i in range(players)]

    CarsWindow(game, controllers, segmentation=segmentation, debug=debug)


if __name__ == '__main__':
    main(**STARTING_SCENARIO, debug=True)
