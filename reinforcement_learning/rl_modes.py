from enum import Enum, auto

class RLMode(Enum):
    LOAD = auto()
    TRAIN = auto()
    OPTIMIZE = auto()
    OPTIMIZE_AND_TRAIN = auto()
