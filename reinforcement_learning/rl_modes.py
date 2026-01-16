from enum import Enum, auto

class RLMode(Enum):
    LOAD_HISTORY = auto()
    LOAD_TRAINED_MODEL = auto()
    TRAIN = auto()
    OPTIMIZE = auto()
    OPTIMIZE_AND_TRAIN = auto()
