from stable_baselines3.common.callbacks import BaseCallback
from mlsl_simulation.reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from mlsl_simulation.reinforcement_learning.rl_io import create_game_history

class GameHistoryCallback(BaseCallback):
    def __init__(self, env: MlslEnv, model_history_save_path: str, verbose = 0):
        super().__init__(verbose)
        self.env = env
        self.model_history_save_path = model_history_save_path

    def _on_step(self):
        if self.env.done or self.env.truncated:
            create_game_history(
                self.model_history_save_path,
                self.env.map_history,
                self.env.car_history,
                self.env.action_history,
                self.env.action_length_history,
                )

        return True