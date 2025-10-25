import optuna

from typing import Dict, Any
from abc import ABC, abstractmethod
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from stable_baselines3.common.base_class import BaseAlgorithm

class RLAlgorithm(ABC):
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