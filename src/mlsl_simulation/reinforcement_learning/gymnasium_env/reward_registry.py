from typing import Dict, Callable
from mlsl_simulation.reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from mlsl_simulation.reinforcement_learning.gymnasium_env.reward_types import RewardType

_reward_registry: Dict[RewardType, MlslEnv] = {}

def register_reward_model(model_type: RewardType) -> Callable[[MlslEnv], MlslEnv]:
    def decorator(model_class) -> MlslEnv:
        _reward_registry[model_type] = model_class
        return model_class
    return decorator

def get_reward_model(model_type: RewardType) -> MlslEnv:
    return _reward_registry.get(model_type)