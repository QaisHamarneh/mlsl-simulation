from typing import Optional, List

from controller.astar_car_controller import AstarCarController
from game_model.game_model import TrafficEnv
from game_model.car import Car
from game_model.road_network import Road
from gui.pyglet_gui import CarsWindow

class GameController:
    def __init__(self, roads: List[Road], players: int, cars: Optional[List[Car]] = None, controllers: Optional[List[AstarCarController]] = None, 
                 debug: bool = False, test_mode: List[str] = None):
        
        self.game = TrafficEnv(roads=roads, players=players, cars=cars, controllers=controllers)
        self.game_over = False

    def start(self):
        pass

    def check_deadlock(self):
        deadlock = [True if car.speed == 0 else False for car in self.game.cars]
        return all(deadlock)

class GameControllerCLI(GameController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start(self):
        while not self.game_over:
            self.game_over = self.game.play_step()
            if not self.game_over:
                self.game_over = self.check_deadlock()

        print(f"Game Over:")
        for car in self.game.cars:
            print(f"car {car.name} score {car.score}")

class GameControllerGUI(GameController):
    def __init__(self, roads: List[Road], players: int, cars: Optional[List[Car]] = None, controllers: Optional[List[AstarCarController]] = None, 
                 debug: bool = False, test_mode: List[str] = None):
        super().__init__(roads, players, cars, controllers, debug, test_mode)
        self.debug = debug
        self.test_mode = test_mode

    def start(self):
        CarsWindow(game=self.game, debug=self.debug, test_mode=self.test_mode)