from typing import Dict
from stable_baselines3 import PPO
from controller.rl_algo_registry import register_rl_algorithm
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType

@register_rl_algorithm(RLAlgorithmType.PPO)
class PPOAlgorithm(RLAlgorithm):
    def create_algorithm(self) -> PPO:
        if self.params == None:
            return PPO("MlpPolicy", self.env)
        else:
            return PPO("MlpPlolicy", self.env, **self.params)