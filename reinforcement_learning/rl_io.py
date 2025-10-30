import os
import datetime
import pandas as pd
import optuna

from typing import Dict, Any
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from stable_baselines3.common.base_class import BaseAlgorithm
from optuna.visualization import plot_param_importances
from optuna.study import Study

RESULT_MODEL_PATH = os.path.join('reinforcement_learning', 'results', 'models')
RESULT_PARAM_PATH = os.path.join('reinforcement_learning', 'results', 'hyperparameters')

BEST_MODEL_FILE = "best_model"
BEST_PARAMS_FILE = "best_params.parquet"
TRIALS_FILE = "trials.csv"
PARAM_IMPORTANCE_FILE = "param_importance.html"

def get_path_center(scenario: str, rl_algo: str, obs_model: str, reward_type: str) -> str:
    return os.path.join(scenario, rl_algo, obs_model, reward_type)


def get_complete_path(path_center: str, id:str, model: bool) -> str:
    if model:
        path = os.path.join(RESULT_MODEL_PATH, path_center, id)
    else:
        path = os.path.join(RESULT_PARAM_PATH, path_center, id)
    return path


def load_best_model(path_center: str, id: str, rl_algorithm: RLAlgorithm, env: MlslEnv) -> BaseAlgorithm:
    path = os.path.join(RESULT_MODEL_PATH, path_center, id, BEST_MODEL_FILE)

    return rl_algorithm.algorithm.load(path, env)


def save_best_params(best_params_df: pd.DataFrame, path: str) -> None:
    os.makedirs(path, exist_ok=True)

    best_params_path = os.path.join(path, BEST_PARAMS_FILE)
    best_params_df.to_parquet(best_params_path)


def save_study_materials(study: Study, path: str) -> None:
    os.makedirs(path, exist_ok=True)

    trials_path = os.path.join(path, TRIALS_FILE)
    study.trials_dataframe().to_csv(trials_path, index=False)

    param_importance_path = os.path.join(path, PARAM_IMPORTANCE_FILE)
    fig = plot_param_importances(study)
    fig.write_html(param_importance_path)


def load_best_params(path_center: str, id: str) -> Dict[str, Any]:
    path = os.path.join(RESULT_PARAM_PATH, path_center, id, BEST_PARAMS_FILE)
    best_params = pd.read_parquet(path).iloc[0].to_dict()
    return best_params