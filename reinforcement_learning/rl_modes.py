from enum import Enum, auto

class RLMode(Enum):
    NO_AI = auto()
    LOAD = auto()
    TRAIN = auto()
    OPTIMIZE = auto()
    OPTIMIZE_AND_TRAIN = auto()
