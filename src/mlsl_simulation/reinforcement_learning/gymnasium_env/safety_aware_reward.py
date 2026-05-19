import math
from typing import Dict, Tuple

from gymnasium import spaces

from mlsl_simulation.controller.safety_controller import SafetyController
from mlsl_simulation.reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from mlsl_simulation.reinforcement_learning.gymnasium_env.reward_registry import register_reward_model
from mlsl_simulation.reinforcement_learning.gymnasium_env.reward_types import RewardType
from mlsl_simulation.reinforcement_learning.rl_constants import (
    REWARD_CRASH,
    REWARD_GOAL_REACHED,
    REWARD_PROGRESS_COEF,
    REWARD_UNSAFE_ACCELERATION,
    REWARD_UNSAFE_LANE_CHANGE,
)


@register_reward_model(RewardType.SAFETY_AWARE_REWARD)
class SafetyAwareReward(MlslEnv):
    """Reward that consults a SafetyController for the agent car.

    Per-step reward is the sum of:
      - REWARD_CRASH if the agent died this step (collision).
      - REWARD_GOAL_REACHED * (goals reached this step) when the agent's
        score increased.
      - REWARD_UNSAFE_ACCELERATION if the chosen acceleration exceeds
        SafetyController.get_max_acceleration().
      - REWARD_UNSAFE_LANE_CHANGE if the chosen lane change is marked
        unsafe by SafetyController.get_safe_lane_change(). Staying in
        the current lane is always considered safe.
      - REWARD_PROGRESS_COEF * (prev_dist - cur_dist): potential-based
        shaping on Euclidean distance from the agent to its current goal.
        Skipped on the step a goal is reached (the goal pointer swaps, so
        the delta would be meaningless) and on the crash step.

    Safety advice is captured *before* the simulation advances; reward
    is computed *after* the step completes.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.safety_controller: SafetyController = self._build_safety_controller()
        self.last_max_acc: int = 0
        self.last_safe_lane_change: list[bool] = [True, True, True]
        self.prev_goal_dist: float = self._goal_distance()

    def reset(self, seed: None | int = None, options: None | Dict = None) -> Tuple[spaces.Space, Dict[str, any]]:
        obs, info = super().reset(seed=seed, options=options)
        self.agent_score = self.game_model.agent_car.score
        self.safety_controller = self._build_safety_controller()
        self.last_max_acc = 0
        self.last_safe_lane_change = [True, True, True]
        self.prev_goal_dist = self._goal_distance()
        return obs, info

    def _build_safety_controller(self) -> SafetyController:
        return SafetyController(
            car=self.game_model.agent_car,
            cars=self.game_model.cars,
            reservation_management=self.game_model.reservation_management,
        )

    def _pre_step(self, decoded_action: Tuple[int, int]) -> None:
        agent = self.game_model.agent_car
        if agent is None or agent.get_death_status():
            self.last_max_acc = decoded_action[0]
            self.last_safe_lane_change = [True, True, True]
            return

        self.last_max_acc = self.safety_controller.get_max_acceleration()
        reservations = self.game_model.reservation_management.get_car_reservations(agent.id)
        self.last_safe_lane_change = self.safety_controller.get_safe_lane_change(
            reservations, decoded_action[0]
        )

    def compute_reward(self) -> float:
        agent = self.game_model.agent_car

        if agent is not None and agent.get_death_status():
            self.prev_goal_dist = self._goal_distance()
            return REWARD_CRASH

        reward = 0.0
        goal_reached_this_step = False

        if agent is not None and agent.score > self.agent_score:
            goal_reached_this_step = True
            reward += (agent.score - self.agent_score) * REWARD_GOAL_REACHED
            self.agent_score = agent.score

        decoded_acc, decoded_lane = self.last_decoded_action

        if decoded_acc > self.last_max_acc:
            reward += REWARD_UNSAFE_ACCELERATION

        # decoded_lane is in {-1, 0, 1}; safe_lane_change indexed [right, stay, left].
        if not self.last_safe_lane_change[decoded_lane + 1]:
            reward += REWARD_UNSAFE_LANE_CHANGE

        # Potential-based progress shaping. Re-anchor on goal swap so the
        # discontinuity is not charged as a backwards step.
        cur_dist = self._goal_distance()
        if not goal_reached_this_step:
            reward += REWARD_PROGRESS_COEF * (self.prev_goal_dist - cur_dist)
        self.prev_goal_dist = cur_dist

        return reward

    def _goal_distance(self) -> float:
        """Euclidean distance (in pixel units) from the agent to its current
        goal. Returns 0.0 if either is unavailable."""
        agent = self.game_model.agent_car
        if agent is None or agent.goal is None:
            return 0.0
        return math.hypot(
            agent.goal.pos.x - agent.pos.x,
            agent.goal.pos.y - agent.pos.y,
        )
