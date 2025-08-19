from typing import List
from game_model.constants import TIME_PER_FRAME, FLASH_CYCLE
from game_model.game_model import TrafficEnv
from game_model.Tester import SimulationTester
from game_model.road_network import Road
from gui.pyglet_gui import CarsWindow
from gymnasium_env.mlsl_env import MlslEnv
from gymnasium_env.abstract_observation import Observation
from gymnasium_env.numeric_observation import NumbericObservation
from stable_baselines3 import PPO
import numpy as np
import pyglet

class GameController:
    def __init__(self, 
                 gui: bool, 
                 roads: List[Road], 
                 npcs: int,
                 agent: bool = False,  
                 debug: bool = False, 
                 test_mode: List[str] = None):
        
        self.gui = gui

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, npcs=npcs, agent=agent)
        self.observation_model: Observation = NumbericObservation(self.game_model)
        self.env: MlslEnv = MlslEnv(game_model=self.game_model, observation_model=self.observation_model)

        self.model = PPO("MultiInputPolicy", self.env, verbose=1)
        self.model.learn(10)

        self.vec_env = self.model.get_env()

        self.done: bool = False

        self.debug: bool = debug
        self.test_mode = test_mode
        if test_mode is not None:
            self.sim_tester: SimulationTester = SimulationTester(self.game_model, self.test_mode)

    def run_game(self) -> None:
        self.obs = self.vec_env.reset()

        if self.gui:
            self.frame_count = 0
            self._run_gui()
        else:
            self._run_headless()

    def _run_headless(self) -> None:
        while not self.done:

            action, _ = self.model.predict(self.obs, deterministic=True)

            self.obs, self.reward, self.done, self.info = self.vec_env.step(actions=action)

        self._game_over_state(self.game_model)

    def _run_gui(self) -> None:
        self.window = CarsWindow(debug=self.debug, game_model=self.game_model)

        pyglet.clock.schedule_interval(self._update_gui, (1 / TIME_PER_FRAME))
        pyglet.app.run()

    def _update_gui(self, delta_time: float) -> None:
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0

            action, _ = self.model.predict(self.obs, deterministic=True)
            self.obs, self.reward, self.done, self.info  = self.vec_env.step(actions=action)

            if self.done:
                self._game_over_state(self.game_model)
                self.window.pause = True

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME

    def _train(self) -> None:
        pass
        
    def _game_over_state(self, game_model: TrafficEnv) -> None:
        print(f"Game Over:")
        for car in game_model.cars:
            print(f"car {car.name} score {car.score}")
            #Todo: print reason, if car is dead
