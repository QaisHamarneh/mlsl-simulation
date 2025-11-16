from abc import ABC, abstractmethod
from game_model.game_model import TrafficEnv
from gymnasium import spaces

class Observation(ABC):
    """
    An abstract observation model.

    To add a new observation model create a new ObservationModelType Enum (e.g. ObservationModelType.example)
    and a new class which inherits from Observation (e.g. ExampleObservation(Observation)).
    Use the observation_registry to register the new observation model:

    @register_observation_model(ObservationModelType.example)
    class ExampleObservation(Observation):

    """
    def __init__(self, game_model: TrafficEnv) -> None:
        self.game_model = game_model

    @abstractmethod
    def space(self) -> spaces.Space:
        ...

    @abstractmethod
    def observe(self):
        ...