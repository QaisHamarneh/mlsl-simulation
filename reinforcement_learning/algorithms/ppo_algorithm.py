import optuna

from typing import Dict, Any
from stable_baselines3 import PPO
from reinforcement_learning.algorithms.rl_algo_registry import register_rl_algorithm
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType
from reinforcement_learning.algorithms.sample_ppo_params import sample_ppo_params

@register_rl_algorithm(RLAlgorithmType.PPO)
class PPOAlgorithm(RLAlgorithm):
    def create_algorithm(self, params: Dict[str, Any] | None = None) -> PPO:
        if params == None:
            return PPO("MlpPolicy", self.env)
        else:
            return PPO("MlpPolicy", self.env, **params)
        
    def get_sample_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        return sample_ppo_params(trial)