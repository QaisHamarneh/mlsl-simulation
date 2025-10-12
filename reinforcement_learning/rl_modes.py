from enum import Enum, auto

class RLMode(Enum):
    NULL = auto()
    LOAD = auto()
    TRAIN = auto()
    OPTUNA = auto()
