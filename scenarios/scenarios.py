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
    "players": 2
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
    "players": 2
}

STARTING_SCENARIO = {
    "roads": [
        Road("bottom", True, 0, 1, 0),
        Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1),
        Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left", False, 0, 1, 0),
        Road("h1", True, 145, 0, 2),
        Road("h2", True, 330, 3, 3),
        Road("h3", True, 675, 2, 0),
        Road("v1", False, 320, 0, 2),
        Road("v2", False, 680, 3, 3),
        Road("v3", False, 1200, 2, 0)
    ],
    "segmentation": False,
    "players": 10
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
    "players": 25
}

HORIZONTAL_VERTICAL = {
    "roads": [
        Road("h1", True, 180, 3, 3),
        Road("v1", False, 190, 2, 2),
        Road("v2", False, 540, 2, 2)
    ],
    "segmentation": False,
    "players": 25
}

JUST_ONE_CAR = STARTING_SCENARIO.copy()
JUST_ONE_CAR["players"] = 1