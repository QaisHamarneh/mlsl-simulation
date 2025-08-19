from typing import List
from game_model.constants import TIME_PER_FRAME, FLASH_CYCLE, RENDER_MODES
from game_model.game_model import TrafficEnv
from game_model.Tester import SimulationTester
from game_model.road_network import Road
from gui.pyglet_gui import GameWindow
from gymnasium_env.mlsl_env import MlslEnv
from gymnasium_env.abstract_observation import Observation
from gymnasium_env.numeric_observation import NumbericObservation
from stable_baselines3 import PPO
import pyglet

class GameController:
    def __init__(self, 
                 roads: List[Road], 
                 players: int,
                 render_mode: None | str = None, 
                 ai: bool = False, 
                 debug: bool = False, 
                 test_mode: List[str] = None):
        
        assert render_mode is None or render_mode in RENDER_MODES
        self.render_mode = render_mode

        self.ai = ai

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, players=players, ai=self.ai)

        self.done = None

        self.debug: bool = debug
        self.test_mode = test_mode
        if test_mode is not None:
            self.sim_tester: SimulationTester = SimulationTester(self.game_model, self.test_mode)

    def run(self) -> None:
        if self.ai:
            self._train_model()
            self._run_model()
        elif self.render_mode is 'human':
            self.frame_count = 0
            self._run_gui()
        else:
            self._run_headless()

        self.game_model.current_state()

    def _train_model(self):
        self.observation_model: Observation = NumbericObservation(self.game_model)
        self.env: MlslEnv = MlslEnv(game_model=self.game_model, observation_model=self.observation_model, render_mode=self.render_mode)

        self.model = PPO("MultiInputPolicy", self.env, verbose=1)
        self.model.learn(10_000)

        self.vec_env = self.model.get_env()

    def _run_model(self):
        self.observation = self.vec_env.reset()

        while self.done == None:
            action, _ = self.model.predict(self.observation, deterministic=True)

            self.observation, self.reward, self.done, self.info = self.vec_env.step(actions=action)
            self.vec_env.render()

    def _run_gui(self) -> None:
        self.window = GameWindow(game_model=self.game_model, debug=self.debug)

        pyglet.clock.schedule_interval(self._update_gui, (1 / TIME_PER_FRAME))
        pyglet.app.run()

    def _update_gui(self, delta_time: float) -> None:
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0

            self.done = self.game_model.play_step()

            if not self.done == None:
                self.window.pause = True

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME

    def _run_headless(self) -> None:
        while self.done == None:
            self.done = self.game_model.play_step()
