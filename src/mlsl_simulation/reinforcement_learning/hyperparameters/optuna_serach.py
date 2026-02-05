import optuna

from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_timeline
from optuna.study import Study
from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement, EvalCallback
from mlsl_simulation.reinforcement_learning.algorithms.sample_ppo_params import sample_ppo_params
from mlsl_simulation.reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from mlsl_simulation.reinforcement_learning.rl_constants import HYPERPARAMS_TRAINING_TIMESTEPS, OPTUNA_TRIALS, OPTUNA_PARALLEL_JOBS

class OptunaSearch:
    """Hyperparameter optimization using Optuna.
    
    Automatically finds the best hyperparameters for an RL algorithm by training
    multiple agents with different settings and evaluating their performance.
    
    ## How It Works
    
    1. Create a study (optimization problem)
    2. For each trial (iteration):
        a. Sample hyperparameters intelligently
        b. Train agent briefly with these parameters
        c. Evaluate on validation environment
        d. Return performance score
        e. Pruner may stop bad trials early
    3. Return hyperparameters from best-performing trial
    
    ## Optuna Components
    
    - **Sampler**: Smart hyperparameter selection strategy
        - TPESampler: Tree-structured Parzen Estimator (learns from previous trials)
    - **Pruner**: Early stopping of unpromising trials
        - MedianPruner: Stops if worse than median performance so far
    - **Study**: The optimization session (collection of trials)
    - **Trial**: One training run with specific hyperparameters
    
    ## Output
    
    Returns an `optuna.Study` object containing:
    - Best hyperparameters found
    - Performance of each trial
    - Parameter importance analysis
    
    ## Configuration
    
    See `rl_constants.py`:
    - HYPERPARAMS_TRAINING_TIMESTEPS: Steps per trial (lower = faster but less reliable)
    - OPTUNA_TRIALS: Number of trials to run
    - OPTUNA_PARALLEL_JOBS: Parallel trials (currently must be 1)
    """
    
    def __init__(self, rl_algorithm: RLAlgorithm):
        """Initialize the hyperparameter search.
        
        Args:
            rl_algorithm (RLAlgorithm): The algorithm to optimize (PPO, etc.)
        """
        self.rl_algorithm = rl_algorithm

        self.sampler = TPESampler(n_startup_trials=10, multivariate=True)
        self.pruner = MedianPruner(n_startup_trials=10, n_warmup_steps=10)

    def search_params(self) -> Study:
        """Execute the hyperparameter optimization search.
        
        Runs multiple trials to find the best hyperparameters. Each trial trains
        an agent with different hyperparameters and evaluates performance.
        
        Returns:
            Study: Optuna study object containing:
                - best_params: Dict of best hyperparameters found
                - best_value: Best performance score (mean reward)
                - trials_dataframe(): DataFrame with all trial results
                - For visualization, use plot_optimization_history(study), etc.
        """
        study = optuna.create_study(
            sampler=self.sampler,
            pruner=self.pruner,
            direction="maximize",  # Maximize mean reward
        )

        study.optimize(self.objective, n_jobs=OPTUNA_PARALLEL_JOBS, n_trials=OPTUNA_TRIALS)

        return study

    def objective(self, trial: optuna.Trial) -> float:
        """Objective function for a single Optuna trial.
        
        This function is called for each trial. It samples hyperparameters, trains
        the agent, and returns the evaluation score. Optuna uses the returned value
        to decide which hyperparameters are better.
        
        Args:
            trial (optuna.Trial): The current Optuna trial. Used to suggest hyperparameters.
        
        Returns:
            float: The mean reward achieved during evaluation (higher is better).
                   Optuna may stop training early if performance is poor (pruning).
        
        Workflow:
            1. Sample hyperparameters from the trial
            2. Apply hyperparameters to algorithm
            3. Train for HYPERPARAMS_TRAINING_TIMESTEPS
            4. Evaluate on validation data
            5. Return mean reward
        """
        sampled_hyperparams = self.rl_algorithm.get_sample_params(trial)

        self.rl_algorithm.change_params(sampled_hyperparams)

        self.model = self.rl_algorithm.algorithm

        stop_callback = StopTrainingOnNoModelImprovement(max_no_improvement_evals=30, min_evals=50, verbose=1)
        eval_callback = EvalCallback(self.model.get_env(),
                                     callback_after_eval=stop_callback,
                                     eval_freq=500,
                                     render=False)
        
        self.model.learn(total_timesteps=HYPERPARAMS_TRAINING_TIMESTEPS, callback=eval_callback, progress_bar=True)

        return eval_callback.best_mean_reward

        
        