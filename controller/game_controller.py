import pyglet

from typing import List, Callable
from game_model.constants import TIME_PER_FRAME
from game_model.game_model import TrafficEnv
from game_model.road_network import Road
from gui.pyglet_gui import GameWindow
from gui.render_mode import RenderMode
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from reinforcement_learning.gymnasium_env.reward_types import RewardType
from controller.reward_registry import get_reward_model
from reinforcement_learning.observation_spaces.observation_model_types import ObservationModelType
from reinforcement_learning.observation_spaces.abstract_observation import Observation
from controller.observation_registry import get_observation_model
from reinforcement_learning.rl_constants import TRAINING_TIMESTEPS, PPO_MODEL
from reinforcement_learning.rl_modes import RLMode
from reinforcement_learning.rl_io import save_model_path, load_model_path
from reinforcement_learning.hyperparameters.optuna_serach import OptunaSearch
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EvalCallback

class GameController:
    mode_handlers = {}

    def __init__(self, 
                 roads: List[Road], 
                 players: int,
                 render_mode: RenderMode = RenderMode.GUI, 
                 rl_mode: RLMode = RLMode.NO_AI, 
                 observation_model_type: None | ObservationModelType = None,
                 reward_type: None | RewardType = None):
        
        self.render_mode = render_mode
        self.rl_mode = rl_mode

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, players=players, rl_mode=self.rl_mode)

        if not (rl_mode == RLMode.NO_AI or observation_model_type == None or reward_type == None):
            observation_model_class: Observation = get_observation_model(observation_model_type)
            self.observation_model: Observation = observation_model_class(self.game_model)

            env_class: MlslEnv = get_reward_model(reward_type)
            self.env: MlslEnv = env_class(game_model=self.game_model, observation_model=self.observation_model, render_mode=self.render_mode)
            self.env = Monitor(self.env) # Used to know the episode reward, length, time and other data

            self.model = PPO("MlpPolicy", self.env, verbose=0)

        self.done = None

    def register_mode(mode_handlers, mode) -> Callable[[Callable], Callable]:
        def decorator(func) -> Callable:
            mode_handlers[mode] = func
            return func
        return decorator

    def run(self) -> None:
        handler = self.mode_handlers.get(self.rl_mode)
        if handler:
            handler(self)
        elif self.render_mode == RenderMode.GUI:
            self.frame_count = 0
            self._run_gui()    
        else:
            self._run_no_gui()

        self.game_model.current_state()

    @register_mode(mode_handlers, RLMode.TRAIN) # _train_model = register_mode(mode_handlers, RLMode.TRAIN)(_train_model)
    def _train_model(self):
        # Used to save the best model
        eval_callback = EvalCallback(self.env, 
                                     best_model_save_path=save_model_path(PPO_MODEL),
                                     eval_freq=500,
                                     render=False)

        # Train the agent
        self.model.learn(total_timesteps=TRAINING_TIMESTEPS, callback=eval_callback, progress_bar=True)
        
        evaluate_policy(self.model, self.env, n_eval_episodes=1, render=True)

    @register_mode(mode_handlers, RLMode.LOAD)
    def _load_model(self):
        self.model = PPO.load(load_model_path(PPO_MODEL), self.env)
        evaluate_policy(self.model, self.env, n_eval_episodes=1, render=True)

    @register_mode(mode_handlers, RLMode.OPTIMIZE)
    def _optimize_hyperparams(self):
        optuna_search = OptunaSearch(self.env)
        optuna_search.search_params()

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
            self.window = GameWindow(game_model=self.game_model)

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

    def _run_no_gui(self) -> None:
        while self.done == None:
            self.done = self.game_model.play_step()
