from typing import Dict, Callable
from reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
from reinforcement_learning.gymnasium_env.observation_spaces.abstract_observation import Observation

_observation_registry: Dict[ObservationModelType, Observation] = {}

def register_observation_model(model_type: ObservationModelType) -> Callable[[Observation], Observation]:
    def decorator(model_class) -> Observation:
        _observation_registry[model_type] = model_class
        return model_class
    return decorator

def get_observation_model(model_type: ObservationModelType) -> Observation:
    return _observation_registry.get(model_type)