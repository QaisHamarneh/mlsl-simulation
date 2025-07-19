from gymnasium import Env
from gymnasium import spaces
from typing import List, Tuple, Union
from game_model.car import Car
from game_model.game_model import TrafficEnv
from game_model.constants import LANE_MAX_SPEED, MAX_ACC, MAX_DEC, WINDOW_HEIGHT, WINDOW_WIDTH
from gui.game_drawer import GameDrawer
from gui.renderer import Renderer
from dataclasses import dataclass
import numpy as np
import pyglet
from pyglet import shapes

@dataclass
class ObservationState():
    car_x: int
    car_y: int
    speed: int
    direction: int
    goal_x: int
    goal_y: int
    dist_to_goal: float

class MlslEnv(Env):
    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(self, 
                 game_model: TrafficEnv, 
                 gui: bool = True, ):
        
        self.game_model = game_model
        self.renderer = Renderer()
        self.map_shapes: List[Union[shapes.Line, shapes.Rectangle]] = GameDrawer.draw_map(self.game_model.roads)

        self.flash_count = 0

        self.action_space = spaces.Tuple((
            # accelaration = [-MAX_DEC, MAX_ACC]
            spaces.Discrete(n=(MAX_ACC + MAX_DEC), start=(-MAX_DEC)),
            # lange changes = [-1, 0, 1]
            spaces.Discrete(n=3, start=-1)
        ))
        self.observation_space = self._make_observation_space()

    def _make_observation_space(self):
        return spaces.Dict({
            "car_x": spaces.Box(low=0, high=WINDOW_WIDTH, shape=(), dtype=np.int32),
            "car_y": spaces.Box(low=0, high=WINDOW_HEIGHT, shape=(), dtype=np.int32),
            "speed": spaces.Box(low=0, high=LANE_MAX_SPEED, shape=(), dtype=np.int32),
            "direction": spaces.Discrete(2),
            "goal_x": spaces.Box(low=0, high=WINDOW_WIDTH, shape=(), dtype=np.int32),
            "goal_y": spaces.Box(low=0, high=WINDOW_HEIGHT, shape=(), dtype=np.int32),
            "dist_to_goal": spaces.Box(low=0.0, high=100, shape=(), dtype=np.float32),
        })

    def reset(self, *, seed = None, options = None) -> List[ObservationState]:
        self.game_model.reset()
        return self._get_obs()
    
    def step(self, actions: List[Tuple[int, int]]):
        done = self.game_model.play_step(actions=actions)
        obs = self._get_obs()
        reward = self._compute_reward()
        return obs, reward, done
    
    def render(self, gui=True):
        game_shapes = []
        game_shapes += self.map_shapes
        game_shapes += GameDrawer.draw_goals(self.game_model.cars)
        game_shapes += GameDrawer.draw_cars(self.game_model.cars, self.flash_count)
        self.renderer.render(game_shapes)

    def close(self):
        self.renderer.close()

    def _get_obs(self) -> List[ObservationState]:
        observation_states = []
        
        for car in self.game_model.agent_cars:
            state = ObservationState(
                car_x = car.pos.x,
                car_y = car.pos.y,
                speed = car.speed,
                direction = car.direction.value,
                goal_x = car.goal.pos.x,
                goal_y = car.goal.pos.y,
                dist_to_goal = np.linalg.norm([car.pos.x - car.goal.pos.x, car.pos.y - car.goal.pos.y]))
            observation_states.append(state)

        return observation_states

    def _compute_reward(self):
        pass