from gymnasium import Env
from gymnasium import spaces
from typing import Tuple, Dict
from game_model.game_model import TrafficEnv
from game_model.constants import MAX_ACC, MAX_DEC, TIME_PER_FRAME, RENDER_MODES
from gui.pyglet_gui import GameWindow
from reinforcement_learning.gymnasium_env.abstract_observation import Observation
import pyglet
import time

class MlslEnv(Env):

    def __init__(self, 
                 game_model: TrafficEnv,
                 observation_model: Observation,
                 render_mode: None | str = None):
        
        self.render_mode = render_mode

        self.game_model: TrafficEnv = game_model
        self.game_window: None | GameWindow = GameWindow(self.game_model) if self.render_mode == 'human' else None

        self.agent_score: int = self.game_model.agent_car.score

        self.observation_model = observation_model

        # accelaration = [-MAX_DEC, MAX_ACC] and lange changes = [-1, 0, 1]
        self.action_space = spaces.MultiDiscrete([MAX_ACC + MAX_DEC, 3])
        self.observation_space = self.observation_model.space()

    def reset(self, seed: None | int = None, options: None | Dict = None) -> Tuple[spaces.Space, Dict[str, any]]:
        self.game_model.reset()
        return (self.observation_model.observe(), self._get_info())
    
    def step(self, actions: Tuple[int, int]):
        decoded_action = (actions[0] - MAX_DEC, actions[1] - 1)

        result = self.game_model.play_step(action=decoded_action)

        observation = self.observation_model.observe()

        reward = self._compute_reward()

        done = False
        truncated = False

        if result == 'game_over':
            done = True
        elif result == 'deadlock':
            truncated = True

        info = self._get_info() # for debugging

        return observation, reward, done, truncated, info
    
    def render(self):
        if self.game_window:
            self._render_frame()
            time.sleep(1.0 / TIME_PER_FRAME)

    def _render_frame(self):
        self.game_window.dispatch_events()
        self.game_window.on_draw()
        pyglet.clock.tick()
        self.game_window.flip()

    def _compute_reward(self):
        if self.game_model.agent_car.score > self.agent_score:
            self.agent_score = self.game_model.agent_car.score
            return 1
        elif self.game_model.agent_car.illegal_move:
            self.game_model.agent_car.illegal_move = False
            return -1
        elif self.game_model.agent_car.dead:
            return -10
        else:
            return 0
    
    def _get_info(self) -> Dict:
        """Compute auxiliary information for debugging.

        Returns:
            dict:
        """
        return {}