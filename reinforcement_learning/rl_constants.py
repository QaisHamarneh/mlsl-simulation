import os

TRAINING_TIMESTEPS = 100_000

# save models
PPO_PATH = os.path.join('reinforcement_learning/saved_trainings', 'saved_ppo_model')

# load models
LOAD_PPO_PATH = os.path.join('reinforcement_learning/saved_trainings', 'saved_ppo_model', 'best_model')

# car types
AGENT = "Agent"
NPC = "NPC"