"""
Very simple integration test that creates a Stable Baselines3 PPO agent
and trains it for a few timesteps on the MLSL gymnasium environment.

Usage:
    python run_tests.py               # if test_train.py is imported there
    pytest tests/test_train.py -v   # directly via pytest
"""
import os
import sys

# Ensure src/ is on the path (mirrors other tests in this repo)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gymnasium
import numpy as np

from stable_baselines3 import PPO

from mlsl_simulation.scenarios.scenarios import SCENARIOS
from mlsl_simulation.game_model.game_model import TrafficEnv
from mlsl_simulation.reinforcement_learning.rl_modes import RLMode
from mlsl_simulation.reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
from mlsl_simulation.reinforcement_learning.gymnasium_env.observation_spaces.observation_registry import get_observation_model
from mlsl_simulation.reinforcement_learning.gymnasium_env.reward_types import RewardType
from mlsl_simulation.reinforcement_learning.gymnasium_env.reward_registry import get_reward_model


def _build_env(scenario_key: str = "CIRCUIT"):
    """Construct a small MLSL gymnasium env ready for RL."""
    scenario = SCENARIOS[scenario_key]
    roads = scenario["roads"]
    players = scenario["players"]

    # The underlying traffic simulation
    game_model = TrafficEnv(
        roads=roads,
        players=players,
        rl_mode=RLMode.TRAIN,
    )

    # Observation model (must import the submodule so decorators run)
    # NumericObservation is registered automatically when its module is imported.
    from mlsl_simulation.reinforcement_learning.gymnasium_env.observation_spaces import numeric_observation  # noqa: F401
    obs_model_cls = get_observation_model(ObservationModelType.NUMERIC_OBSERVATION)
    obs_model = obs_model_cls(game_model)

    # Reward model env (subclass of MlslEnv)
    # InitialReward is registered automatically when its module is imported.
    from mlsl_simulation.reinforcement_learning.gymnasium_env import initial_reward  # noqa: F401
    env_cls = get_reward_model(RewardType.INITIAL_REWARD)
    env = env_cls(
        game_model=game_model,
        observation_model=obs_model,
        render_mode=None,
        show_reservation=False,
    )
    return env


class TestSimplePPOTraining:
    """Sanity-check that the MLSL env is compatible with Stable Baselines3 PPO."""

    def test_env_compatibility(self):
        """Reset + random steps must return correct Gymnasium tuples."""
        env = _build_env("CIRCUIT")
        obs, info = env.reset(seed=42)

        assert isinstance(obs, np.ndarray)
        assert obs.dtype == np.float32
        assert env.observation_space.contains(obs)

        for _ in range(5):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            assert isinstance(obs, np.ndarray)
            assert env.observation_space.contains(obs)
            assert isinstance(reward, (int, float))
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)

            if terminated or truncated:
                obs, info = env.reset()

        env.close()

    def test_ppo_runs(self):
        """Instantiate PPO and train for a handful of timesteps."""
        env = _build_env("CIRCUIT")
        model = PPO(
            "MlpPolicy",
            env,
            n_steps=8,
            batch_size=8,
            n_epochs=1,
            verbose=0,
        )
        model.learn(total_timesteps=20)
        env.close()

        # Basic sanity: model exists and has policy weights
        assert model.policy is not None

    def test_ppo_predict(self):
        """Train a tiny bit, then predict deterministic + stochastic actions."""
        env = _build_env("CIRCUIT")
        model = PPO(
            "MlpPolicy",
            env,
            n_steps=8,
            batch_size=8,
            n_epochs=1,
            verbose=0,
        )
        model.learn(total_timesteps=16)

        obs, _ = env.reset()
        action, _states = model.predict(obs, deterministic=True)
        assert env.action_space.contains(action)

        action, _states = model.predict(obs, deterministic=False)
        assert env.action_space.contains(action)

        env.close()


if __name__ == "__main__":
    # Quick self-test when executed directly
    t = TestSimplePPOTraining()
    t.test_env_compatibility()
    print("test_env_compatibility passed")

    t.test_ppo_runs()
    print("test_ppo_runs passed")

    t.test_ppo_predict()
    print("test_ppo_predict passed")

    print("\nAll basic Stable Baselines3 integration tests passed.")
