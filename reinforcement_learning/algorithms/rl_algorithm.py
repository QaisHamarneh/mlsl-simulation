import optuna

from typing import Dict, Any
from abc import ABC, abstractmethod
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from stable_baselines3.common.base_class import BaseAlgorithm

class RLAlgorithm(ABC):
    """
    An abstract learning algorithm.

    To add new learning algorithms create a new RLAlgorithmType Enum (e.g. RLAlgorithm.example)
    and a new class which inherits from the RLAlgorithm class (e.g. ExampleAlgorithm(RLAlgorithm)).
    Use the rl_algo_registry to register the new class:

    @register_rl_algorithm(RLAlgorithmType.example)
    class ExampleAlgorithm(RLAlgorithm)

    """
    def __init__(self, env: MlslEnv, params: None | Dict[str, Any] = None):
        self.env = env
        self.algorithm = self.create_algorithm(params)

    @abstractmethod
    def create_algorithm(self, params: None | Dict[str, Any] = None) -> BaseAlgorithm:
        ...

    def change_params(self, params: Dict[str, Any]) -> None:
        self.algorithm = self.create_algorithm(params)

    @abstractmethod
    def get_sample_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        ...