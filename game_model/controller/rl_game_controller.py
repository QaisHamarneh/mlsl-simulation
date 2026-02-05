import optuna
import pandas as pd
import datetime

from typing import List, Callable, Dict
from game_model.controller.abstract_game_controller import AbstractGameController
from game_model.game_model import TrafficEnv
from game_model.road_network.road_network import Road
from game_model.game_history import GameHistory
from gui.render_mode import RenderMode
from reinforcement_learning.gymnasium_env.mlsl_env import MlslEnv
from reinforcement_learning.gymnasium_env.callbacks.game_history_callback import GameHistoryCallback
from reinforcement_learning.gymnasium_env.reward_types import RewardType
from reinforcement_learning.gymnasium_env.reward_registry import get_reward_model
from reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
from reinforcement_learning.gymnasium_env.observation_spaces.abstract_observation import Observation
from reinforcement_learning.gymnasium_env.observation_spaces.observation_registry import get_observation_model
from reinforcement_learning.algorithms.rl_algorithm import RLAlgorithm
from reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType
from reinforcement_learning.algorithms.rl_algo_registry import get_rl_algo
from reinforcement_learning.rl_constants import TRAINING_TIMESTEPS
from reinforcement_learning.rl_modes import RLMode
from reinforcement_learning.rl_io import get_path_center, get_complete_path, load_best_params, load_best_model, save_best_params, save_study_materials, load_game_history
from reinforcement_learning.hyperparameters.optuna_serach import OptunaSearch
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EvalCallback, CallbackList

class RLGameController(AbstractGameController):
    mode_handlers: Dict[RLMode, Callable] = {}

    def __init__(
            self,
            scenario_name: str, 
            roads: List[Road], 
            players: int,
            render_mode: RenderMode, 
            rl_mode: RLMode, 
            rl_algorithm_type: RLAlgorithmType,
            observation_model_type: ObservationModelType,
            reward_type: RewardType,
            id_model: None | str = None,
            id_history: None | str = None,
            id_hyperparams: None | str = None,
            ):

            self.id_history = id_history

            self.game_model: TrafficEnv = TrafficEnv(roads=roads, players=players, rl_mode=rl_mode)

            self.scenario_name = scenario_name
            self.render_mode = render_mode

            self.rl_mode = rl_mode
            self.rl_algorithm_type = rl_algorithm_type
            self.observation_model_type = observation_model_type
            self.reward_type = reward_type
            self.id_model = id_model
            self.id_hyperparams = id_hyperparams

            self.path_center = get_path_center(
                scenario=self.scenario_name,
                rl_algo=self.rl_algorithm_type.name,
                obs_model=self.observation_model_type.name,
                reward_type=self.reward_type.name,
            )
            self.model_path = get_complete_path(self.path_center, str(datetime.datetime.now().replace(microsecond=0)), True)
            self.hyperparams_path = get_complete_path(self.path_center, str(datetime.datetime.now().replace(microsecond=0)), False)

            observation_model_class: Observation = get_observation_model(self.observation_model_type)
            self.observation_model: Observation = observation_model_class(self.game_model)

            env_class: MlslEnv = get_reward_model(self.reward_type)
            self.env: MlslEnv = env_class(game_model=self.game_model, observation_model=self.observation_model, render_mode=self.render_mode)
            self.env = Monitor(self.env) # Used to know the episode reward, length, time and other data

            rl_algo_class: RLAlgorithm = get_rl_algo(self.rl_algorithm_type)
            self.rl_algorithm: RLAlgorithm = rl_algo_class(self.env)


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


    def register_mode(mode_handlers, mode) -> Callable[[Callable], Callable]:
        def decorator(func) -> Callable:
            mode_handlers[mode] = func
            return func
        return decorator


    """
    To add new reinforcement learning modes create a new RLMode Enum (e.g. RLMode.example)
    and a new function in this class (e.g. def _example_fnc(self)). Use the register_mode function
    to add the function to the mode_handlers dictionary. The function then should look like this:

    @register_mode(mode_handlers, RLMode.example)
    def _example_fnc(self):

    """

    @register_mode(mode_handlers, RLMode.TRAIN) # _train_model = register_mode(mode_handlers, RLMode.TRAIN)(_train_model)
    def _train_model(self):
        if self.id_hyperparams != None:
            hyperparams = load_best_params(self.path_center, self.id_hyperparams)
            self.rl_algorithm.change_params(hyperparams)

        # Used to save the best model
        eval_callback = EvalCallback(self.env, 
                                     best_model_save_path=self.model_path,
                                     eval_freq=500,
                                     render=self.render_mode.value)
        
        history_callback = GameHistoryCallback(self.env.unwrapped, self.model_path)

        # Train the agent
        self.rl_algorithm.algorithm.learn(total_timesteps=TRAINING_TIMESTEPS, callback=CallbackList([eval_callback, history_callback]), progress_bar=True)
        
        evaluate_policy(self.rl_algorithm.algorithm, self.env, n_eval_episodes=1, render=self.render_mode.value)


    @register_mode(mode_handlers, RLMode.LOAD_TRAINED_MODEL)
    def _load_model(self):
        model = load_best_model(self.path_center, self.id_model, self.rl_algorithm, self.env)
        evaluate_policy(model, self.env, n_eval_episodes=1, render=self.render_mode.value)


    @register_mode(mode_handlers, RLMode.LOAD_HISTORY)
    def _load_history(self):
        if self.id_history is not None:
            map_history, car_history, action_history = load_game_history(self.path_center, self.id_model, self.id_history)

            game_history = GameHistory()
            game_history.set_map(map_history)
            game_history.set_list_of_cars(car_history)
            game_history.set_action_history_dict(action_history)

            game_history.history_playback(False)
            # play history_playback


    @register_mode(mode_handlers, RLMode.OPTIMIZE)
    def _optimize_hyperparams(self):
        optuna_search = OptunaSearch(self.rl_algorithm)
        study: optuna.Study = optuna_search.search_params()

        best_params = study.best_params.copy()
        best_params.pop("lr_schedule")

        best_params_df = pd.DataFrame([best_params])
        save_best_params(best_params_df, self.hyperparams_path)
        save_study_materials(study, self.hyperparams_path)

        return best_params


    @register_mode(mode_handlers, RLMode.OPTIMIZE_AND_TRAIN)
    def _optimize_and_train(self):
        best_params = self._optimize_hyperparams()

        self.rl_algorithm.change_params(best_params)
        self.id_hyperparams = None # needed if id_hyperparams parameter is not None
        self._train_model()
        