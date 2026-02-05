import optuna

from typing import Dict, Any
from stable_baselines3 import PPO
from reinforcement_learning.algorithms.rl_algo_registry import register_rl_algorithm
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType
from reinforcement_learning.algorithms.sample_ppo_params import sample_ppo_params

@register_rl_algorithm(RLAlgorithmType.PPO)
class PPOAlgorithm(RLAlgorithm):
    """Proximal Policy Optimization algorithm implementation. 
    
    ## Key PPO Hyperparameters
    
    - **learning_rate**: Controls optimization step size. Higher = faster learning but less stable
    - **n_steps**: Number of steps per rollout before updating policy
    - **batch_size**: Number of transitions per gradient update (must be ≤ n_steps)
    - **n_epochs**: Number of passes over collected data
    - **gamma**: Discount factor (0.99 = future rewards matter a lot, 0.9 = near-term focus)
    - **gae_lambda**: Generalized Advantage Estimation parameter (0.95-0.99 typical)
    - **clip_range**: PPO clipping range (prevents drastic policy changes)
    - **ent_coef**: Entropy coefficient (encourages exploration)
    
    ## References
    
    - Schulman et al., 2017: "Proximal Policy Optimization Algorithms"
    - Stable Baselines3: https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
    """
    
    def create_algorithm(self, params: Dict[str, Any] | None = None) -> PPO:
        """Create a PPO algorithm instance.
        
        Initializes a PPO agent with the given environment and hyperparameters.
        Uses "MlpPolicy" (neural network) as the policy function.
        
        Args:
            params (Dict[str, Any] | None): PPO hyperparameters. If None, uses Stable
                Baselines3 defaults (which are reasonable starting points).
        
        Returns:
            PPO: A Stable Baselines3 PPO instance.
        
        Example:
            >>> params = {
            ...     'learning_rate': 0.0003,
            ...     'n_steps': 2048,
            ...     'batch_size': 64,
            ...     'n_epochs': 10,
            ...     'gamma': 0.99
            ... }
            >>> algo = PPOAlgorithm(env, params)
        """
        if params == None:
            return PPO("MlpPolicy", self.env)
        else:
            print(params)
            return PPO("MlpPolicy", self.env, **params)
        
    def get_sample_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Sample PPO hyperparameters for Optuna optimization.
        
        Generates random hyperparameter combinations within sensible ranges
        to be tested during hyperparameter optimization.
        
        Args:
            trial (optuna.Trial): The Optuna trial for suggesting values.
        
        Returns:
            Dict[str, Any]: A complete set of PPO hyperparameters sampled for this trial.
        """
        return sample_ppo_params(trial)