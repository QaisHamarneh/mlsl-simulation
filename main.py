import logging

from scenarios.scenarios import CIRCUIT, STARTING_SCENARIO, STARTING_SCENARIO, TWO_CROSSING
from controller.game_controller import GameController
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
        name, 
        render_mode: RenderMode = RenderMode.GUI, 
        rl_mode: RLMode = RLMode.NO_AI, 
        rl_algorithm_type: None | RLAlgorithmType = None,
        observation_model_type: None | ObservationModelType = None,
        reward_type: None | RewardType = None
        ):

    controller = GameController(
        name,
        roads, 
        players, 
        render_mode,
        rl_mode,
        rl_algorithm_type,
        observation_model_type,
        reward_type,
        )
    
    controller.run()

if __name__ == '__main__':
    main(
        **STARTING_SCENARIO, 
        render_mode=RenderMode.GUI, 
        rl_mode=RLMode.NO_AI, 
        rl_algorithm_type=RLAlgorithmType.PPO,
        observation_model_type=ObservationModelType.NUMERIC,
        reward_type=RewardType.INITIAL
        )
