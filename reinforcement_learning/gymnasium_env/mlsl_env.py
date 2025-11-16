import pyglet
import time

from abc import ABC, abstractmethod
from gymnasium import Env
from gymnasium import spaces
from typing import Tuple, Dict, List
from game_model.game_model import TrafficEnv
from game_model.constants import MAX_ACC, MAX_DEC, TIME_PER_FRAME
from gui.pyglet_gui import GameWindow
from reinforcement_learning.gymnasium_env.observation_spaces.abstract_observation import Observation

class MlslEnv(Env, ABC):
    """
    An abstract gymnasium env.

    To add a new environment create a RewardType Enum (e.g. RewardType.example) and
    a new class which inherits from MlslEnv (e.g. ExampleEnv(MlslEnv)). Use the 
    reward_registry to register the new env:

    @register_reward_model(RewardType.example)
    class ExampleEnv(MlslEnv):

    """

    def __init__(self, 
                 game_model: TrafficEnv,
                 observation_model: Observation,
                 render_mode: None | str = None):
        
        self.render_mode = render_mode

        self.game_model: TrafficEnv = game_model
        self.game_window: None | GameWindow = GameWindow(self.game_model) if self.render_mode == 'human' else None

        self.agent_score: int = self.game_model.agent_car.score

        self.observation_model: Observation = observation_model

        # accelaration = [0, MAX_DEC + MAX_ACC - 1] and lange changes = [0, 2]
        self.action_space = spaces.MultiDiscrete([MAX_ACC + MAX_DEC, 3])
        self.observation_space = self.observation_model.space()

        self.done: bool = False
        self.truncated: bool = False

        self.map_history = self.game_model.game_history.map.copy()
        self.car_history = self.game_model.game_history.list_of_cars.copy()
        self.action_history = self.game_model.game_history.action_history_dict.copy()
        self.action_length_history = self.game_model.game_history.action_length

    def reset(self, seed: None | int = None, options: None | Dict = None) -> Tuple[spaces.Space, Dict[str, any]]:
        self.game_model.reset()
        return (self.observation_model.observe(), self._get_info())
    
    def step(self, actions: Tuple[int, int]):
        # accelaration = [-MAX_DEC, MAX_ACC] and lange changes = [-1, 0, 1]
        if actions[0] > MAX_DEC - 1:
            decoded_action = (actions[0] - MAX_DEC + 1, actions[1] - 1)
        else:
            decoded_action = (actions[0] - MAX_DEC, actions[1] - 1)

        self.result = self.game_model.play_step(action=decoded_action)

        observation = self.observation_model.observe()

        reward = self.compute_reward()

        self.done = False
        self.truncated = False

        if self.result == "game_over":
            self.done = True
        elif self.result == "deadlock":
            self.truncated = True

        info = self._get_info() # for debugging

        if self.done or self.truncated:
            self.map_history = self.game_model.game_history.map.copy()
            self.car_history = self.game_model.game_history.list_of_cars.copy()
            self.action_history = self.game_model.game_history.action_history_dict.copy()
            self.action_length_history = self.game_model.game_history.action_length

        return observation, reward, self.done, self.truncated, info
    
    def render(self):
        if self.game_window:
            self._render_frame()
            time.sleep(1.0 / TIME_PER_FRAME)

    def _render_frame(self):
        self.game_window.dispatch_events()
        self.game_window.on_draw()
        pyglet.clock.tick()
        self.game_window.flip()

    @abstractmethod
    def compute_reward(self):
        ...
    
    def _get_info(self) -> Dict:
        """Compute auxiliary information for debugging.

        Returns:
            dict:
        """
        return {}