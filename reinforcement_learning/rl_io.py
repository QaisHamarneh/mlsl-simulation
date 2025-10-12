import os

from reinforcement_learning.rl_constants import RESULT_MODEL_PATH, RESULT_PARAM_PATH

def save_params_path(model_type: str, file_name: str) -> str:
    return os.path.join(RESULT_PARAM_PATH, model_type, file_name)

def save_model_path(model_type: str) -> str:
    return os.path.join(RESULT_MODEL_PATH, model_type)

def load_model_path(model_type: str) -> str:
    return os.path.join(RESULT_MODEL_PATH, model_type, 'best_model')