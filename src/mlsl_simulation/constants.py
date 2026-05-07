# Size
BLOCK_SIZE = 40
LANE_DISPLACEMENT = 2
WINDOW_WIDTH = 40 * BLOCK_SIZE
WINDOW_HEIGHT = 24 * BLOCK_SIZE
BUFFER = BLOCK_SIZE // 2

LANE_MAX_SPEED = BLOCK_SIZE // 2
CROSSING_MAX_SPEED = LANE_MAX_SPEED // 2
MINIMAL_SPEED = CROSSING_MAX_SPEED // 2

WINNING_SCORE = 100

# GUI Only
TIME_PER_FRAME = 60 
FLASH_CYCLE = 60 * TIME_PER_FRAME

LANECHANGE_TIME_STEPS = 3
CLAIMTIME = 5

MAX_ACC = BLOCK_SIZE // 4
MAX_DEC = BLOCK_SIZE // 4
JUMP_TIME_STEPS = 1

# lane change
NO_LANE_CHANGE = 0
LEFT_LANE_CHANGE = 1
RIGHT_LANE_CHANGE = -1

# A* congestion penalty: per-car multiplier on a crossing segment's time-cost,
# applied to (cars currently on the 4 crossing cells of the intersection +
# cars queued on its approach lane segments). 0 disables the penalty.
ASTAR_CONGESTION_ALPHA = 0.25
