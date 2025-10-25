from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from reinforcement_learning.gymnasium_env.reward_types import RewardType
from reinforcement_learning.gymnasium_env.reward_registry import register_reward_model

@register_reward_model(RewardType.INITIAL_REWARD)
class InitialReward(MlslEnv):
    def compute_reward(self):
        if self.game_model.agent_car.score > self.agent_score:
            self.agent_score = self.game_model.agent_car.score
            return 1
        elif self.game_model.agent_car.illegal_move:
            self.game_model.agent_car.illegal_move = False
            return -1
        elif self.result == "deadlock":
            return -5
        elif self.game_model.agent_car.dead:
            return -10
        else:
            return 0