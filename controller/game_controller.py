from typing import List
from game_model.constants import TIME_PER_FRAME, RENDER_MODES, TRAINING_TIMESTEPS
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
        elif self.render_mode == 'human':
            self.frame_count = 0
            self._run_gui()    
        else:
            self._run_headless()

        self.game_model.current_state()

    def _train_model(self):
        self.observation_model: Observation = NumbericObservation(self.game_model)
        self.env: MlslEnv = MlslEnv(game_model=self.game_model, observation_model=self.observation_model, render_mode=self.render_mode)

        self.model = PPO("MultiInputPolicy", self.env, verbose=1)
        self.model.learn(total_timesteps=TRAINING_TIMESTEPS)

        self.vec_env = self.model.get_env()

    def _run_model(self):
        self.observation = self.vec_env.reset()

        while not self.done:
            action, _ = self.model.predict(self.observation, deterministic=True)

            self.observation, self.reward, self.done, self.info = self.vec_env.step(actions=action)
            self.vec_env.render()

    def _run_gui(self) -> None:
        self._start_new_game()
        pyglet.app.run()

    def _start_new_game(self) -> None:
        self.game_model.reset()
        self.done = False
        self.frame_count = 0

        if hasattr(self, 'window') and self.window:
            self.window.reset_model(self.game_model)
        else:
            self.window = GameWindow(game_model=self.game_model, debug=self.debug)

        pyglet.clock.unschedule(self._update_gui)
        pyglet.clock.schedule_interval(self._update_gui, (1 / TIME_PER_FRAME))

    def _update_gui(self, delta_time: float) -> None:
        obs = NumbericObservation(self.game_model)
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0

            self.done = self.game_model.play_step()
            obs.observe()

            if not self.done == None:
                self.window.pause = True
                while self.window.pause:
                    pass
                self._start_new_game()

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME

    def _run_headless(self) -> None:
        while self.done == None:
            self.done = self.game_model.play_step()
