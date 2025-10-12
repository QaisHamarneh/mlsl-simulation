import os
import optuna

from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_timeline
from stable_baselines3 import PPO 
from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement, EvalCallback
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from reinforcement_learning.hyperparameters.sample_ppo_params import sample_ppo_params
from reinforcement_learning.rl_constants import HYPERPARAMS_TRAINING_TIMESTEPS, PPO_MODEL
from reinforcement_learning.rl_io import save_params_path

class OptunaSearch:
    def __init__(self, env: MlslEnv):
        self.env = env

        self.sampler = TPESampler(n_startup_trials=10, multivariate=True)
        self.pruner = MedianPruner(n_startup_trials=10, n_warmup_steps=10)

    def search_params(self):
        study = optuna.create_study(
            sampler=self.sampler,
            pruner=self.pruner,
            load_if_exists=True,
            direction='maximize',
        )

        study.optimize(self.objective, n_jobs=1, n_trials=128)

        study.trials_dataframe().to_csv(save_params_path(PPO_MODEL, 'report.csv'))

        fig1 = plot_optimization_history(study)
        fig2 = plot_param_importances(study)
        fig3 = plot_timeline(study)

        fig1.write_html(save_params_path(PPO_MODEL, 'optuna_optimization_history.html'))
        fig2.write_html(save_params_path(PPO_MODEL, 'optuna_param_importances.html'))
        fig3.write_html(save_params_path(PPO_MODEL, 'optuna_timeline.html'))

    def objective(self, trial: optuna.Trial):
        sampled_hyperparams = sample_ppo_params(trial)

        self.model = PPO("MlpPolicy", env=self.env, verbose=0, **sampled_hyperparams)

        stop_callback = StopTrainingOnNoModelImprovement(max_no_improvement_evals=30, min_evals=50, verbose=1)
        eval_callback = EvalCallback(self.env,
                                     callback_after_eval=stop_callback,
                                     eval_freq=500,
                                     render=False)
        
        self.model.learn(total_timesteps=HYPERPARAMS_TRAINING_TIMESTEPS, callback=eval_callback, progress_bar=True)

        return eval_callback.best_mean_reward

        
        