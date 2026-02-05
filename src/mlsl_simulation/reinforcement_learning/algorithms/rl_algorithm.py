import optuna

from typing import Dict, Any
from abc import ABC, abstractmethod
from mlsl_simulation.reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from stable_baselines3.common.base_class import BaseAlgorithm

class RLAlgorithm(ABC):
    """Abstract base class for reinforcement learning algorithms.
    
    This class provides a unified interface for different RL algorithms.
    It manages algorithm instantiation, parameter changes, and Optuna integration for
    hyperparameter optimization.
    
    ## How to Add a New Algorithm
    
    1. Create an `RLAlgorithmType` enum variant:
        ```python
        class RLAlgorithmType(Enum):
            PPO = auto()
            DQN = auto()  # New algorithm
        ```
    
    2. Create a class inheriting from `RLAlgorithm`:
        ```python
        @register_rl_algorithm(RLAlgorithmType.DQN)
        class DQNAlgorithm(RLAlgorithm):
            def create_algorithm(self, params=None):
                # Return a Stable Baselines3 DQN instance
            
            def get_sample_params(self, trial):
                # Sample hyperparameters for this algorithm
        ```
    
    3. The decorator automatically registers it with `rl_algo_registry`.
    
    ## Key Concepts
    
    - **Algorithm**: Stable Baselines3 BaseAlgorithm instance that implements training
    - **Hyperparameters**: Configuration values that affect learning (learning rate, etc.)
    - **Optuna Trial**: Provides hyperparameter sampling for optimization
    
    ## Attributes
        env (MlslEnv): The Gymnasium environment to train on
        algorithm (BaseAlgorithm): The underlying learning algorithm implementation
    """
    
    def __init__(self, env: MlslEnv, params: None | Dict[str, Any] = None):
        """Initialize the RL algorithm.
        
        Args:
            env (MlslEnv): The environment for the algorithm to learn from.
            params (None | Dict[str, Any]): Optional hyperparameters. If None,
                default hyperparameters are used.
        """
        self.env = env
        self.algorithm = self.create_algorithm(params)

    @abstractmethod
    def create_algorithm(self, params: None | Dict[str, Any] = None) -> BaseAlgorithm:
        """Create and return a learning algorithm instance.
        
        Implemented by subclasses to instantiate the specific algorithm (PPO, DQN, etc.)
        with the given hyperparameters.
        
        Args:
            params (None | Dict[str, Any]): Hyperparameters for the algorithm.
                If None, use default hyperparameters.
        
        Returns:
            BaseAlgorithm: A Stable Baselines3 algorithm instance ready for training.
        """
        ...

    def change_params(self, params: Dict[str, Any]) -> None:
        """Change algorithm hyperparameters and recreate the algorithm.
        
        This is called during Optuna optimization to test different hyperparameter
        combinations. Creates a fresh algorithm with the new parameters.
        
        Args:
            params (Dict[str, Any]): New hyperparameters to use.
        """
        self.algorithm = self.create_algorithm(params)

    @abstractmethod
    def get_sample_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Sample hyperparameters using an Optuna trial.
        
        Called by Optuna's objective function to generate hyperparameters to test.
        Subclasses implement algorithm-specific sampling logic.
        
        Args:
            trial (optuna.Trial): The Optuna trial object for suggesting values.
        
        Returns:
            Dict[str, Any]: Sampled hyperparameters for this algorithm.
        
        Example:
            >>> def get_sample_params(self, trial):
            ...     return {
            ...         'learning_rate': trial.suggest_float('lr', 1e-5, 1),
            ...         'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128])
            ...     }
        """
        ...