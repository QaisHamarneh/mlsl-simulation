import os

TRAINING_TIMESTEPS = 1_000

HYPERPARAMS_TRAINING_TIMESTEPS = 1_000

PPO_MODEL = 'ppo'

RESULT_MODEL_PATH = os.path.join('reinforcement_learning', 'results', 'saved_trainings')

RESULT_PARAM_PATH = os.path.join('reinforcement_learning', 'results', 'optimized_parameters')

# car types
AGENT = "Agent"
NPC = "NPC"