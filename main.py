import logging

from scenarios.scenarios import CIRCUIT, STARTING_SCENARIO, TWO_CROSSING
from game_model.abstract_game_controller import AbstractGameController
from game_model.game_controller import GameController
from game_model.rl_game_controller import RLGameController
from gui.render_mode import RenderMode
from reinforcement_learning.rl_modes import RLMode
from reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType
from reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
from reinforcement_learning.gymnasium_env.reward_types import RewardType

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(message)s')

def main(
        players, 
        roads, 
        segmentation,
        scenario_name, 
        render_mode: RenderMode,
        show_reservation: bool, 
        rl_mode: None | RLMode = None, 
        rl_algorithm_type: None | RLAlgorithmType = None,
        observation_model_type: None | ObservationModelType = None,
        reward_type: None | RewardType = None,
        id_model: None | str = None,
        id_hyperparams: None | str = None,
        ):
    
    if not rl_mode:
        controller: AbstractGameController = GameController(
            roads,
            players,
            render_mode,
            show_reservation,
        )
    else:
        controller: AbstractGameController = RLGameController(
            scenario_name,
            roads,
            players,
            render_mode,
            rl_mode,
            rl_algorithm_type,
            observation_model_type,
            reward_type,
            id_model,
            id_hyperparams,
        )
    
    controller.run()

if __name__ == '__main__':
    main(
        **TWO_CROSSING, 
        render_mode=RenderMode.GUI,
        show_reservation=True, 
        rl_mode=None, 
        rl_algorithm_type=RLAlgorithmType.PPO,
        observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
        reward_type=RewardType.INITIAL_REWARD,
        id_model="2025-10-29 18:26:52",
        id_hyperparams=None,
        )
