from typing import List
from game_model.constants import TIME_PER_FRAME, RENDER_MODES
from game_model.game_model import TrafficEnv
from game_model.Tester import SimulationTester
from game_model.road_network import Road
from gui.pyglet_gui import GameWindow
from gymnasium_env.mlsl_env import MlslEnv
from gymnasium_env.abstract_observation import Observation
from gymnasium_env.numeric_observation import NumbericObservation
from gymnasium_env.rl_constants import NULL, LOAD, TRAIN, TRAINING_TIMESTEPS, PPO_PATH, LOAD_PPO_PATH
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EvalCallback
import pyglet

class GameController:
    def __init__(self, 
                 roads: List[Road], 
                 players: int,
                 render_mode: None | str = None, 
                 rl_mode: int = NULL, 
                 debug: bool = False, 
                 test_mode: List[str] = None):
        
        assert render_mode is None or render_mode in RENDER_MODES
        self.render_mode = render_mode
        self.rl_mode = rl_mode

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, players=players, rl_mode=self.rl_mode)

        if not rl_mode == NULL:
            self.observation_model: Observation = NumbericObservation(self.game_model)
            self.env: MlslEnv = MlslEnv(game_model=self.game_model, observation_model=self.observation_model, render_mode=self.render_mode)

        self.done = None

        self.debug: bool = debug
        self.test_mode = test_mode
        if test_mode is not None:
            self.sim_tester: SimulationTester = SimulationTester(self.game_model, self.test_mode)

    def run(self) -> None:
        if self.rl_mode == TRAIN:
            self._train_model()
        elif self.rl_mode == LOAD:
            self._load_model()
        elif self.render_mode == 'human':
            self.frame_count = 0
            self._run_gui()    
        else:
            self._run_headless()

        self.game_model.current_state()

    def _train_model(self):
        # Used to save the best model
        eval_callback = EvalCallback(self.env, 
                                     best_model_save_path=PPO_PATH,
                                     eval_freq=500,
                                     deterministic=True, 
                                     render=False)
        
        #todo: Figure out network size/structure, parameters (which ones are optimized and not) 
        self.model = PPO("MultiInputPolicy", self.env, verbose=0)

        # Train the agent
        self.model.learn(total_timesteps=TRAINING_TIMESTEPS, callback=eval_callback, progress_bar=True)
        evaluate_policy(self.model, self.env, n_eval_episodes=1, render=True)

    def _load_model(self):
        self.model = PPO.load(LOAD_PPO_PATH, self.env)
        evaluate_policy(self.model, self.env, n_eval_episodes=1, render=True)

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
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0

            self.done = self.game_model.play_step()

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
