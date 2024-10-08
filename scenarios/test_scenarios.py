from typing import List, Tuple

from controller.astar_car_controller import AstarCarController
from game_model.car import Car
from game_model.constants import *
from game_model.game_model import TrafficEnv
from game_model.road_network import Goal
from game_model.road_network import Road, LaneSegment
from gui.pyglet_gui import CarsWindow
from scenarios.scenarios import *


def setup_2_car_scenarios(
    env: List[Road],
    car1_seg: int,
    car1_loc: int,
    car2_seg: int,
    car2_loc: int,
    goal1_seg: int,
    goal2_seg: int,
    car1_size: int,
    car2_size: int,
    car1_color: Tuple[int, int, int],
    car2_color: Tuple[int, int, int],
    car1_speed: int,
    car2_speed: int,
    car1_max_speed: int,
    car2_max_speed: int,
    change: int
) -> None:
    """
    Set up a traffic environment with two cars and their respective goals.

    Args:
        env (List[Road]): List of roads in the environment.
        car1_seg (int): Segment index for car 1.
        car1_loc (int): Location of car 1 within its segment.
        car2_seg (int): Segment index for car 2.
        car2_loc (int): Location of car 2 within its segment.
        goal1_seg (int): Segment index for the goal of car 1.
        goal2_seg (int): Segment index for the goal of car 2.
        car1_size (int): Size of car 1.
        car2_size (int): Size of car 2.
        car1_color (Tuple[int, int, int]): Color of car 1 in RGB format.
        car2_color (Tuple[int, int, int]): Color of car 2 in RGB format.
        car1_speed (int): Initial speed of car 1.
        car2_speed (int): Initial speed of car 2.
        car1_max_speed (int): Maximum speed of car 1.
        car2_max_speed (int): Maximum speed of car 2.
        change (int): Lane change value for car 1.

    Returns:
        None
    """
    game = TrafficEnv(players=2, roads=env)
    for i, seg in enumerate(game.segments):
        if isinstance(seg, LaneSegment):
            print(i, seg.begin, seg.end, seg.lane.top, seg.lane.direction)
    game.cars[1] = Car("car1", car1_loc, game.segments[car1_seg], car1_speed, car1_size, car1_color, car1_max_speed)
    game.cars[0] = Car("car2", car2_loc, game.segments[car2_seg], car2_speed, car2_size, car2_color, car2_max_speed)
    game.goals[1] = Goal(game.segments[goal1_seg], car1_color)
    game.goals[0] = Goal(game.segments[goal2_seg], car2_color)
    game.players = 2
    controllers = [AstarCarController(game=game, player=i) for i in range(2)]
    game.cars[1].change_lane(change)
    CarsWindow(game, controllers, segmentation=False, debug=True, pause=True)


RIGHT_BEHIND_NO_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 10,
    "car1_loc": 5,
    "car2_seg": 13,
    "car2_loc": 10,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": -1
}

RIGHT_FRONT_NO_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 10,
    "car1_loc": 10,
    "car2_seg": 13,
    "car2_loc": 5,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": -1
}

RIGHT_CATCH_UP_NO_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 10,
    "car1_loc": 0,
    "car2_seg": 13,
    "car2_loc": 50,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 100,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 30,
    "car2_speed": 0,
    "car1_max_speed": 30,
    "car2_max_speed": 0,
    "change": -1

}

RIGHT_BEHIND_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 10,
    "car1_loc": 0,
    "car2_seg": 13,
    "car2_loc": 60,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 10,
    "car2_speed": 1,
    "car1_max_speed": 10,
    "car2_max_speed": 1,
    "change": -1
}

LEFT_BEHIND_NO_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 17,
    "car1_loc": -5,
    "car2_seg": 19,
    "car2_loc": -10,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": 1
}

LEFT_FRONT_NO_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 17,
    "car1_loc": -10,
    "car2_seg": 19,
    "car2_loc": -5,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": 1
}

LEFT_CATCH_UP_NO_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 17,
    "car1_loc": -100,
    "car2_seg": 19,
    "car2_loc": -150,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 100,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 30,
    "car2_speed": 5,
    "car1_max_speed": 30,
    "car2_max_speed": 5,
    "change": 1
}

LEFT_BEHIND_CHANGE = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 17,
    "car1_loc": -50,
    "car2_seg": 19,
    "car2_loc": -110,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 10,
    "car2_speed": 1,
    "car1_max_speed": 10,
    "car2_max_speed": 1,
    "change": 1
}

UP_BEHIND_NO_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 19,
    "car1_loc": 5,
    "car2_seg": 21,
    "car2_loc": 10,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": 1
}

UP_FRONT_NO_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 19,
    "car1_loc": 10,
    "car2_seg": 21,
    "car2_loc": 5,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": 1
}

UP_CATCH_UP_NO_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 19,
    "car1_loc": 0,
    "car2_seg": 21,
    "car2_loc": 60,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 100,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 30,
    "car2_speed": 5,
    "car1_max_speed": 30,
    "car2_max_speed": 5,
    "change": 1
}

UP_BEHIND_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 19,
    "car1_loc": 0,
    "car2_seg": 21,
    "car2_loc": 60,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 10,
    "car2_speed": 1,
    "car1_max_speed": 10,
    "car2_max_speed": 1,
    "change": 1
}

DOWN_BEHIND_NO_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 13,
    "car1_loc": -5,
    "car2_seg": 15,
    "car2_loc": -10,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": -1
}

DOWN_FRONT_NO_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 13,
    "car1_loc": -10,
    "car2_seg": 15,
    "car2_loc": -5,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": -1
}

DOWN_CATCH_UP_NO_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 13,
    "car1_loc": -100,
    "car2_seg": 15,
    "car2_loc": -150,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 100,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 30,
    "car2_speed": 5,
    "car1_max_speed": 30,
    "car2_max_speed": 5,
    "change": -1
}

DOWN_BEHIND_NO_CHANGE_2 = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 13,
    "car1_loc": -50,
    "car2_seg": 15,
    "car2_loc": -110,
    "goal1_seg": 13,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": RED,
    "car2_color": BLUE,
    "car1_speed": 10,
    "car2_speed": 1,
    "car1_max_speed": 10,
    "car2_max_speed": 1,
    "change": -1
}

DOWN_BEHIND_CHANGE = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 13,
    "car1_loc": -5,
    "car2_seg": 15,
    "car2_loc": -50,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 0,
    "car1_max_speed": 1,
    "car2_max_speed": 0,
    "change": -1
}

CHANGE_TO_RIGHT_LANESEGMENT_DOWN = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 17,
    "car1_loc": -5,
    "car2_seg": 8,
    "car2_loc": 50,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 0,
    "car1_max_speed": 1,
    "car2_max_speed": 0,
    "change": 0
}

CHANGE_TO_RIGHT_LANESEGMENT_UP = {
    "env": UP_DOWN_OVERTAKE["roads"],
    "car1_seg": 19,
    "car1_loc": 5,
    "car2_seg": 8,
    "car2_loc": 50,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 0,
    "car1_max_speed": 1,
    "car2_max_speed": 0,
    "change": 0
}

CHANGE_TO_RIGHT_LANESEGMENT_LEFT_AND_RIGHT = {
    "env": LEFT_RIGHT_OVERTAKE["roads"],
    "car1_seg": 17,
    "car1_loc": -5,
    "car2_seg": 15,
    "car2_loc": 50,
    "goal1_seg": 10,
    "goal2_seg": 1,
    "car1_size": 20,
    "car2_size": 20,
    "car1_color": BLUE,
    "car2_color": RED,
    "car1_speed": 1,
    "car2_speed": 1,
    "car1_max_speed": 1,
    "car2_max_speed": 1,
    "change": 0
}

