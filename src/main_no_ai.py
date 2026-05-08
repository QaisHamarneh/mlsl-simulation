from mlsl_simulation.scenarios.scenarios import load_scenario
from mlsl_simulation.game_model.controller.abstract_game_controller import AbstractGameController
from mlsl_simulation.game_model.controller.game_controller import GameController
from mlsl_simulation.gui.render_mode import RenderMode

if __name__ == '__main__':
    
    scenario = load_scenario("TWO_CROSSINGS_PREDEFINED")

    controller: AbstractGameController = GameController(
        roads=scenario["roads"],
        players=scenario["players"],
        render_mode=RenderMode.GUI,
        show_reservation=True,
        predefined_cars=scenario["predefined_cars"],
    )
    
    controller.run()