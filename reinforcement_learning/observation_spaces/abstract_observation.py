from abc import ABC, abstractmethod
from game_model.game_model import TrafficEnv
from gymnasium import spaces

class Observation(ABC):
    def __init__(self, game_model: TrafficEnv) -> None:
        self.game_model = game_model

    @abstractmethod
    def space(self) -> spaces.Space:
        ...

    @abstractmethod
    def observe(self):
        ...