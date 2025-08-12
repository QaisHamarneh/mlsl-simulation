from gymnasium import Env
from gymnasium import spaces
from typing import List, Tuple, Union, Dict
from game_model.car import Car
from game_model.game_model import TrafficEnv
from game_model.constants import LANE_MAX_SPEED, MAX_ACC, MAX_DEC, WINDOW_HEIGHT, WINDOW_WIDTH
from gui.game_drawer import GameDrawer
from gui.renderer import Renderer
from dataclasses import dataclass
from gymnasium_env.abstract_observation import Observation
import numpy as np
import pyglet
from pyglet import shapes

class MlslEnv(Env):

    def __init__(self, 
                 game_model: TrafficEnv,
                 observation_model: Observation):
        
        self.game_model = game_model
        self.map_shapes: List[Union[shapes.Line, shapes.Rectangle]] = GameDrawer.draw_map(self.game_model.roads)
        self.agent_score: int = self.game_model.agent_cars[0].score

        self.observation_model = observation_model

        # accelaration = [-MAX_DEC, MAX_ACC] and lange changes = [-1, 0, 1]
        self.action_space = spaces.MultiDiscrete([MAX_ACC + MAX_DEC, 3])
        self.observation_space = self.observation_model.space()

    def reset(self, seed: None | int = None, options: None | Dict = None) -> Tuple[spaces.Space, Dict[str, any]]:
        self.game_model.reset()
        return (self.observation_model.observe(), self._get_info())
    
    def step(self, actions: Tuple[int, int]):
        decoded_action = (actions[0] - MAX_DEC, actions[1] - 1)
        done = self.game_model.play_step(action=decoded_action)

        observation = self.observation_model.observe()

        reward = self._compute_reward()

        # We don't use truncation in this environment
        # (could add a step limit here if desired)
        truncated = False

        info = self._get_info() # for debugging

        return observation, reward, done, truncated, info

    def _compute_reward(self):
        if self.game_model.agent_cars[0].score > self.agent_score:
            self.agent_score = self.game_model.agent_cars[0].score
            return 1
        elif self.game_model.agent_cars[0].dead:
            return -10
        else:
            return 0
    
    def _get_info(self) -> Dict:
        """Compute auxiliary information for debugging.

        Returns:
            dict:
        """
        return {}