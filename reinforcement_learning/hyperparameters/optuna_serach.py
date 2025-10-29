import optuna

from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_timeline
from optuna.study import Study
from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement, EvalCallback
from reinforcement_learning.algorithms.sample_ppo_params import sample_ppo_params
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.rl_constants import HYPERPARAMS_TRAINING_TIMESTEPS, OPTUNA_TRIALS, OPTUNA_PARALLEL_JOBS

class OptunaSearch:
    def __init__(self, rl_algorithm: RLAlgorithm):
        self.rl_algorithm = rl_algorithm

        self.sampler = TPESampler(n_startup_trials=10, multivariate=True)
        self.pruner = MedianPruner(n_startup_trials=10, n_warmup_steps=10)

    def search_params(self) -> Study:
        study = optuna.create_study(
            sampler=self.sampler,
            pruner=self.pruner,
            direction="maximize",
        )

        study.optimize(self.objective, n_jobs=OPTUNA_PARALLEL_JOBS, n_trials=OPTUNA_TRIALS)

        return study

    def objective(self, trial: optuna.Trial):
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

        
        