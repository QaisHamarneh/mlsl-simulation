# Size
from gui.colors import GREEN

BLOCK_SIZE = 40
LANE_DISPLACEMENT = 2
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 920
# WINDOW_WIDTH = 890
# WINDOW_HEIGHT = 600
BUFFER = BLOCK_SIZE // 2
MID_LANE = BLOCK_SIZE // 2

LANE_CHANGE_STEPS = 3
LANE_CHANGE_LIMIT = 10
CROSSING_LIMIT = 5 * BLOCK_SIZE

# GUI Only
TIME_PER_FRAME = 1/20

BLACK = (0, 0, 0)
PALE_GREEN = (144, 215, 164)
WHITE = (255, 255, 255)
ROAD_BLUE = (102, 153, 204)
DEAD_GREY = (110, 110, 110)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK_RGBA = (0, 0, 0, 255)

LANECHANGE_TIME_STEPS = 3
CLAIMTIME = 5

max_acc_a = 3
max_decc_b = 20
JUMP_TIME_STEPS = 2

# lane change
NO_LANE_CHANGE = 0
LEFT_LANE_CHANGE = 1
RIGHT_LANE_CHANGE = -1

MAX_STAGNATION_TIME = 10

N_ACTIONS = 3