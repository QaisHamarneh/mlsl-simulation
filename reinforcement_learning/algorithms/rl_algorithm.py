from typing import Dict
from abc import ABC, abstractmethod
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from stable_baselines3.common.base_class import BaseAlgorithm

class RLAlgorithm(ABC):
    def __init__(self, env: MlslEnv, params: None | Dict = None):
        self.env = env
        self.params = params
        self.algorithm = self.create_algorithm()

    @abstractmethod
    def create_algorithm(self) -> BaseAlgorithm:
        ...

    def change_params(self, params: Dict) -> None:
        self.params = params
        self.algorithm = self.create_algorithm()