import os

# Multi-car traffic sim with MultiDiscrete actions, intersections, deadlock and
# crash dynamics. Episodes cap at MAX_EPISODE_STEPS=500, so 1M steps is ~2k
# episodes at worst — enough to see a learning signal beyond initial collisions.
TRAINING_TIMESTEPS = 1_000_000

# Per-trial budget. Needs to comfortably exceed PPO's default n_steps=2048 so
# several policy updates happen, and must allow at least 10 EvalCallback runs
# (see eval_freq = HYPERPARAMS_TRAINING_TIMESTEPS // 10 in optuna_serach.py) so
# StopTrainingOnNoModelImprovement(min_evals=5, max_no_improvement_evals=5) can
# actually trigger.
HYPERPARAMS_TRAINING_TIMESTEPS = 100_000
# TPESampler and MedianPruner both have n_startup_trials=10, so anything below
# ~20 trials is effectively random search with no pruning. 50 gives the TPE
# surrogate real signal and lets the pruner cull poor trials.
OPTUNA_TRIALS = 50
OPTUNA_PARALLEL_JOBS = 1 # currently only working with 1

# Hard cap on env steps per RL episode. Without this, evaluate_policy can
# hang when the agent dies but background NPCs keep running indefinitely.
MAX_EPISODE_STEPS = 500

# Reward magnitudes used by SafetyAwareReward.
REWARD_GOAL_REACHED = 50.0
REWARD_CRASH = -100.0
REWARD_UNSAFE_ACCELERATION = -1.0
REWARD_UNSAFE_LANE_CHANGE = -1.0
# Potential-based shaping coefficient: per-step reward is
# REWARD_PROGRESS_COEF * (prev_dist - cur_dist), where distance is the
# pixel-space Euclidean distance from the agent to its current goal. Positive
# when the agent moves toward the goal, negative when it moves away. Keep
# small so it does not dominate REWARD_GOAL_REACHED on a successful approach.
REWARD_PROGRESS_COEF = 0.01