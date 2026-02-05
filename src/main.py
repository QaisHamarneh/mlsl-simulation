import logging

from mlsl_simulation.scenarios.scenarios import SCENARIOS
from mlsl_simulation.game_model.controller.abstract_game_controller import AbstractGameController
from mlsl_simulation.game_model.controller.game_controller import GameController
from mlsl_simulation.gui.render_mode import RenderMode
from mlsl_simulation.reinforcement_learning.rl_modes import RLMode
try:
    from mlsl_simulation.game_model.controller.rl_game_controller import RLGameController
    from mlsl_simulation.reinforcement_learning.algorithms.rl_algorithm_types import RLAlgorithmType
    from mlsl_simulation.reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
    from mlsl_simulation.reinforcement_learning.gymnasium_env.reward_types import RewardType
except ImportError:
    print("Requirements for reinfocement learning are missing.")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(message)s')

def main(
        players, 
        roads, 
        segmentation,
        scenario_name, 
        render_mode: RenderMode,
        show_reservation: bool, 
        rl_mode: None | RLMode = None, 
        rl_algorithm_type: None = None,
        observation_model_type: None = None,
        reward_type: None = None,
        id_model: None | str = None,
        id_history: None | str = None,
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
            id_history,
            id_hyperparams,
        )
    
    controller.run()

if __name__ == '__main__':
    main(
        **SCENARIOS["CIRCUIT"], 
        render_mode=RenderMode.GUI,
        show_reservation=True, 
        rl_mode=RLMode.OPTIMIZE_AND_TRAIN, 
        rl_algorithm_type=RLAlgorithmType.PPO,
        observation_model_type=ObservationModelType.NUMERIC_OBSERVATION,
        reward_type=RewardType.INITIAL_REWARD,
        id_model="2026-02-05 20:02:23",
        id_history="19:47:27_1345.pkl",
        id_hyperparams=None,
        )
