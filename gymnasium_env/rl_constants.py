import os

TRAINING_TIMESTEPS = 100_000

# modes
NULL = 0
LOAD = 1
TRAIN = 2

# save models
PPO_PATH = os.path.join('training', 'saved_ppo_model')

# load models
LOAD_PPO_PATH = os.path.join('training', 'saved_ppo_model', 'best_model')

# car types
AGENT = "Agent"
NPC = "NPC"