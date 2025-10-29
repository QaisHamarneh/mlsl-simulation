from game_model.constants import WINDOW_WIDTH, BLOCK_SIZE, WINDOW_HEIGHT
from game_model.road_network import Road

LEFT_RIGHT_OVERTAKE = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("h1", True, 330, 3, 3),
    ],
    "segmentation": False,
    "players": 2,
    "scenario_name": "left_right_overtake"
}

LEFT_RIGHT_OVERTAKE_2 = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("v1", False, 330, 1, 1),
        Road("h1", True, 330, 3, 3),
    ],
    "segmentation": False,
    "players": 6,
    "scenario_name": "left_right_overtake_2"
}

UP_DOWN_OVERTAKE = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("v1", False, 680, 3, 3),
    ],
    "segmentation": False,
    "players": 2,
    "scenario_name": "up_down_overtake"
}

BIG_SCENARIO = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - 1 * BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - 1 * BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        # Road("h1", True, WINDOW_HEIGHT // 2 - 2 * BLOCK_SIZE, 2, 2),
        # Road("v1", False, WINDOW_WIDTH // 2 - 2 * BLOCK_SIZE, 2, 2)
        Road("h1", True, WINDOW_HEIGHT // 4 - 1 * BLOCK_SIZE, 0, 2),
        Road("h2", True, WINDOW_HEIGHT // 2 - 2 * BLOCK_SIZE, 2, 2),
        Road("h3", True, 3 * WINDOW_HEIGHT // 4 - 1 * BLOCK_SIZE, 2, 0),
        Road("v1", False, WINDOW_WIDTH // 4 - 1 * BLOCK_SIZE, 0, 2),
        Road("v2", False, WINDOW_WIDTH // 2 - 2 * BLOCK_SIZE, 2, 2),
        Road("v3", False, 3 * WINDOW_WIDTH // 4 - 1 * BLOCK_SIZE, 2, 0)
    ],
    "segmentation": False,
    "players": 80,
    "scenario_name": "big_scenario"
}

STARTING_SCENARIO = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("h1", True, WINDOW_HEIGHT // 4 - 1 * BLOCK_SIZE, 0, 2),
        Road("h2", True, WINDOW_HEIGHT // 2 - 3 * BLOCK_SIZE, 3, 3),
        Road("h3", True, 3 * WINDOW_HEIGHT // 4 - 1 * BLOCK_SIZE, 2, 0),
        Road("v1", False, WINDOW_WIDTH // 4 - 1 * BLOCK_SIZE, 0, 2),
        Road("v2", False, WINDOW_WIDTH // 2 - 3 * BLOCK_SIZE, 3, 3),
        Road("v3", False, 3 * WINDOW_WIDTH // 4 - 1 * BLOCK_SIZE, 2, 0)
    ],
    "segmentation": False,
    "players": 21,
    "scenario_name": "starting_scenario"
}
TWO_CROSSING = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("h1", True, 5 * BLOCK_SIZE, 2, 2),
        Road("h2", True, 14 * BLOCK_SIZE, 2, 2),
        Road("v1", False, 9 * BLOCK_SIZE, 3, 3),
        Road("v2", False, 23 * BLOCK_SIZE, 3, 4)
    ],
    "segmentation": False,
    "players": 22,
    "scenario_name": "two_crossings"
}

ONE_CROSSING = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("v1", False, WINDOW_WIDTH // 2 - 3 * BLOCK_SIZE, 1, 1),
        Road("h1", True, WINDOW_HEIGHT // 2 - 3 * BLOCK_SIZE, 1, 1),
    ],
    "segmentation": False,
    "players": 16,
    "scenario_name": "one_crossing"
}

ONE_ROAD = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("r1", True, 400, 6, 0)
    ],
    "segmentation": False,
    "players": 5,
    "scenario_name": "one_road"
}

HORIZONTAL_VERTICAL = {
    "roads": [
        Road("h1", True, 180, 3, 3),
        Road("v1", False, 190, 2, 2),
        Road("v2", False, 540, 2, 2)
    ],
    "segmentation": False,
    "players": 25,
    "scenario_name": "horizontal_vertical"
}

CIRCUIT = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
    ],
    "segmentation": False,
    "players": 3,
    "scenario_name": "circuit"
}

JUST_ONE_CAR = STARTING_SCENARIO.copy()
JUST_ONE_CAR["players"] = 1
JUST_ONE_CAR["name"] = "just_one_car"