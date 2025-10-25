import pyglet
import optuna
import pandas as pd
import os

from typing import List, Callable, Dict
from game_model.constants import TIME_PER_FRAME
from game_model.game_model import TrafficEnv
from game_model.road_network import Road
from gui.pyglet_gui import GameWindow
from gui.render_mode import RenderMode
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from reinforcement_learning.gymnasium_env.reward_types import RewardType
from reinforcement_learning.gymnasium_env.reward_registry import get_reward_model
from reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
from reinforcement_learning.gymnasium_env.observation_spaces.abstract_observation import Observation
from reinforcement_learning.gymnasium_env.observation_spaces.observation_registry import get_observation_model
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType
from reinforcement_learning.algorithms.rl_algo_registry import get_rl_algo
from reinforcement_learning.rl_constants import TRAINING_TIMESTEPS, PPO_MODEL
from reinforcement_learning.rl_modes import RLMode
from reinforcement_learning.rl_io import get_path, load_model_path, BEST_PARAMS_FILE, TRIALS_FILE, PARAM_IMPORTANCE_FILE
from reinforcement_learning.hyperparameters.optuna_serach import OptunaSearch
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EvalCallback
from optuna.visualization import plot_param_importances

class GameController:
    mode_handlers: Dict[RLMode, Callable] = {}

    def __init__(
            self,
            scenario_name: str, 
            roads: List[Road], 
            players: int,
            render_mode: RenderMode = RenderMode.GUI, 
            rl_mode: RLMode = RLMode.NO_AI, 
            rl_algorithm_type: None | RLAlgorithmType = None,
            observation_model_type: None | ObservationModelType = None,
            reward_type: None | RewardType = None,
            id_model: None | str = None,
            id_hyperparams: None | str = None,
            ):
        
        self.scenario_name = scenario_name
        self.render_mode = render_mode

        self.rl_mode = rl_mode
        self.rl_algorithm_type = rl_algorithm_type
        self.observation_model_type = observation_model_type
        self.reward_type = reward_type
        self.id_model = id_model
        self.id_hyperparams = id_hyperparams

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, players=players, rl_mode=self.rl_mode)

        self.done = None

        # ------------------------------------------------------
        # This section is only needed for reinforcement learning 
        if not (
            rl_mode == RLMode.NO_AI 
            or observation_model_type == None 
            or reward_type == None
            or rl_algorithm_type == None
            ):

            observation_model_class: Observation = get_observation_model(self.observation_model_type)
            self.observation_model: Observation = observation_model_class(self.game_model)

            env_class: MlslEnv = get_reward_model(self.reward_type)
            self.env: MlslEnv = env_class(game_model=self.game_model, observation_model=self.observation_model, render_mode=self.render_mode)
            self.env = Monitor(self.env) # Used to know the episode reward, length, time and other data

            rl_algo_class: RLAlgorithm = get_rl_algo(self.rl_algorithm_type)
            self.rl_algorithm: RLAlgorithm = rl_algo_class(self.env)

            self.model_path = get_path(
                scenario=self.scenario_name,
                rl_algo=self.rl_algorithm_type.name,
                obs_model=self.observation_model_type.name,
                reward_type=self.reward_type.name,
                model=True
            )

            self.params_path = get_path(
                scenario=self.scenario_name,
                rl_algo=self.rl_algorithm_type.name,
                obs_model=self.observation_model_type.name,
                reward_type=self.reward_type.name,
                model=False
            )
        # ------------------------------------------------------

    def register_mode(mode_handlers, mode) -> Callable[[Callable], Callable]:
        def decorator(func) -> Callable:
            mode_handlers[mode] = func
            return func
        return decorator

    def run(self) -> None:
        handler = self.mode_handlers.get(self.rl_mode)
        if handler:
            handler(self)
        elif self.render_mode.value:
            self.frame_count = 0
            self._run_gui()    
        else:
            self._run_no_gui()

        self.game_model.current_state()

    @register_mode(mode_handlers, RLMode.TRAIN) # _train_model = register_mode(mode_handlers, RLMode.TRAIN)(_train_model)
    def _train_model(self):
        # Used to save the best model
        eval_callback = EvalCallback(self.env, 
                                     best_model_save_path=self.model_path,
                                     eval_freq=500,
                                     render=self.render_mode.value)

        # Train the agent
        self.rl_algorithm.algorithm.learn(total_timesteps=TRAINING_TIMESTEPS, callback=eval_callback, progress_bar=True)
        
        evaluate_policy(self.rl_algorithm.algorithm, self.env, n_eval_episodes=1, render=self.render_mode.value)

    @register_mode(mode_handlers, RLMode.LOAD)
    def _load_model(self):
        path = load_model_path(
            scenario=self.scenario_name,
            rl_algo=self.rl_algorithm_type.name,
            obs_model=self.observation_model_type.name,
            reward_type=self.reward_type.name,
            id=self.id_model,
            )
        
        model = self.rl_algorithm.algorithm.load(path, self.env)
        evaluate_policy(model, self.env, n_eval_episodes=1, render=self.render_mode.value)

    @register_mode(mode_handlers, RLMode.OPTIMIZE)
    def _optimize_hyperparams(self):
        optuna_search = OptunaSearch(self.rl_algorithm)
        study: optuna.Study = optuna_search.search_params()

        best_params_df = pd.DataFrame([study.best_params])
        best_params_path = os.path.join(self.params_path, BEST_PARAMS_FILE)
        best_params_df.to_csv(best_params_path, index=False)

        trials_path = os.path.join(self.params_path, TRIALS_FILE)
        study.trials_dataframe().to_csv(trials_path, index=False)

        fig_path = os.path.join(self.params_path, PARAM_IMPORTANCE_FILE)
        fig = plot_param_importances(study)
        fig.write_html(fig_path)

    @register_mode(mode_handlers, RLMode.OPTIMIZE_AND_TRAIN)
    def _optimize_and_train(self):
        self._optimize_hyperparams(self)
        self._train_model(self)

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
