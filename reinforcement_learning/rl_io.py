import os
import datetime

RESULT_MODEL_PATH = os.path.join('reinforcement_learning', 'results', 'models')
RESULT_PARAM_PATH = os.path.join('reinforcement_learning', 'results', 'hyperparameters')

MODEL_FILE = "best_model"
BEST_PARAMS_FILE = "best_model.csv"
TRIALS_FILE = "trials.csv"
PARAM_IMPORTANCE_FILE = "param_importance.html"

# path models: scenario/rl_algo_timestamp/reward/best_model.zip
# path hyperparameters: scenario/rl_algo_timestamp/reward/stuff

def get_path(scenario: str, rl_algo: str, obs_model: str, reward_type: str, model: bool) -> str:
    if model:
        path = os.path.join(RESULT_MODEL_PATH, scenario, rl_algo, obs_model, reward_type, str(datetime.datetime.now().replace(microsecond=0)))
    else:
        path = os.path.join(RESULT_PARAM_PATH, scenario, rl_algo, obs_model, reward_type, str(datetime.datetime.now().replace(microsecond=0)))

    os.makedirs(path, exist_ok=True)
    return path

def load_model_path(scenario: str, rl_algo: str, obs_model: str, reward_type: str, id: str) -> str:
    return os.path.join(RESULT_MODEL_PATH, scenario, rl_algo, obs_model, reward_type, id, "best_model")