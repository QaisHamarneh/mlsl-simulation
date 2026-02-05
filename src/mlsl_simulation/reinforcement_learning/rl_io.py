import os
import datetime
import pandas as pd
import pickle

from typing import Dict, Any, Tuple, List
from mlsl_simulation.game_model.game_history import GameHistory
from mlsl_simulation.reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from mlsl_simulation.reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from stable_baselines3.common.base_class import BaseAlgorithm
from optuna.visualization import plot_param_importances
from optuna.study import Study

RESULT_MODEL_PATH = os.path.join('rl_results', 'models')
RESULT_PARAM_PATH = os.path.join('rl_results', 'hyperparameters')

BEST_MODEL_FILE = "best_model"
BEST_PARAMS_FILE = "best_params.parquet"
TRIALS_FILE = "trials.csv"
PARAM_IMPORTANCE_FILE = "param_importance.html"

def get_path_center(scenario: str, rl_algo: str, obs_model: str, reward_type: str) -> str:
    """Build the path center common to both model and hyperparameter results.
    
    The path center represents the configuration: which scenario, algorithm, observation
    model, and reward function were used.
    
    Args:
        scenario (str): Map/scenario name (e.g., 'circuit', 'two_crossings')
        rl_algo (str): Algorithm name (e.g., 'PPO')
        obs_model (str): Observation model name (e.g., 'NUMERIC_OBSERVATION')
        reward_type (str): Reward function type (e.g., 'INITIAL_REWARD')
    
    Returns:
        str: Path center like 'circuit/PPO/NUMERIC_OBSERVATION/INITIAL_REWARD'
    """
    return os.path.join(scenario, rl_algo, obs_model, reward_type)


def get_complete_path(path_center: str, id: str, model: bool) -> str:
    """Get the complete path to a result directory.
    
    Args:
        path_center (str): Configuration path from get_path_center()
        id (str): Experiment ID (typically timestamp like '2025-10-29 18:26:52')
        model (bool): If True, returns path to models/. If False, returns path to hyperparameters/
    
    Returns:
        str: Complete absolute path to the result directory
    """
    if model:
        path = os.path.join(RESULT_MODEL_PATH, path_center, id)
    else:
        path = os.path.join(RESULT_PARAM_PATH, path_center, id)
    return path


def load_best_model(path_center: str, id: str, rl_algorithm: RLAlgorithm, env: MlslEnv) -> BaseAlgorithm:
    """Load a previously trained model from disk.
    
    Args:
        path_center (str): Configuration path from get_path_center()
        id (str): Experiment ID (typically timestamp)
        rl_algorithm (RLAlgorithm): The algorithm instance (determines algorithm type)
        env (MlslEnv): The environment to load the model into
    
    Returns:
        BaseAlgorithm: Trained model ready for inference/further training
    """
    path = os.path.join(RESULT_MODEL_PATH, path_center, id, BEST_MODEL_FILE)

    return rl_algorithm.algorithm.load(path, env)


def save_best_params(best_params_df: pd.DataFrame, path: str) -> None:
    """Save best hyperparameters to a parquet file.
    
    Args:
        best_params_df (pd.DataFrame): DataFrame containing the best hyperparameters
        path (str): Directory to save the parameters to (created if not exists)
    """
    os.makedirs(path, exist_ok=True)

    best_params_path = os.path.join(path, BEST_PARAMS_FILE)
    best_params_df.to_parquet(best_params_path)


def save_study_materials(study: Study, path: str) -> None:
    """Save Optuna study results and analysis.
    
    Saves:
    - trials.csv: All trial results in tabular format
    - param_importance.html: Interactive visualization of hyperparameter importance
    
    Args:
        study (optuna.Study): The completed Optuna study
        path (str): Directory to save results to (created if not exists)
    """
    os.makedirs(path, exist_ok=True)

    trials_path = os.path.join(path, TRIALS_FILE)
    study.trials_dataframe().to_csv(trials_path, index=False)

    param_importance_path = os.path.join(path, PARAM_IMPORTANCE_FILE)
    fig = plot_param_importances(study)
    fig.write_html(param_importance_path)


def load_best_params(path_center: str, id: str) -> Dict[str, Any]:
    """Load best hyperparameters from disk.
    
    Args:
        path_center (str): Configuration path from get_path_center()
        id (str): Experiment ID (typically timestamp)
    
    Returns:
        Dict[str, Any]: Dictionary of hyperparameters ready to use with algorithm
    """
    path = os.path.join(RESULT_PARAM_PATH, path_center, id, BEST_PARAMS_FILE)
    best_params = pd.read_parquet(path).iloc[0].to_dict()
    return best_params


def create_game_history(path: str, map_history, car_history, action_history, action_length_history) -> None:
    """Save a game episode to disk for later replay.
    
    Creates a pickle file containing the complete episode state, allowing
    recreation of the exact game sequence.
    
    Args:
        path (str): Directory to save history to (created if not exists)
        map_history: Map state throughout the episode
        car_history: Car states throughout the episode
        action_history: Actions taken by the agent
        action_length_history: Total number of actions
    """
    action_length = action_length_history / len(car_history)
    name = str(datetime.datetime.now().strftime("%H:%M:%S")) + "_" + str(int(action_length)) + ".pkl"

    os.makedirs(os.path.join(path, "history"), exist_ok=True)

    file = os.path.join(path, "history", name)

    with open(file, 'wb') as f:
        pickle.dump(map_history, f)
        pickle.dump(car_history, f)
        pickle.dump(action_history, f)


def load_game_history(path_center: str, id_model: str, id_history: str) -> Tuple[List, List, Dict]:
    """Load a previously saved game episode.
    
    Args:
        path_center (str): Configuration path from get_path_center()
        id_model (str): Experiment ID where the model was saved
        id_history (str): History filename (like "HH:MM:SS_steps.pkl")
    
    Returns:
        Tuple[List, List, Dict]: (map_history, car_history, action_history)
    """
    path = os.path.join(RESULT_MODEL_PATH, path_center, id_model, "history", id_history)

    with open(path, 'rb') as f:
        map_history = pickle.load(f)
        car_history = pickle.load(f)
        action_history = pickle.load(f)

    return map_history, car_history, action_history