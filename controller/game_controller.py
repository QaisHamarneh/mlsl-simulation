from typing import Optional, List
from multipledispatch import dispatch

from controller.astar_car_controller import AstarCarController
from game_model.game_model import TrafficEnv
from game_model.car import Car
from game_model.road_network import Goal, Road
from gui.pyglet_gui import CarsWindow

class GameController:
    def __init__(self, roads: List[Road], players: int, cars: Optional[List[Car]] = None, controllers: Optional[List[AstarCarController]] = None, 
                 goals: Optional[List[Goal]] = None, segmentation: bool = False, manual: bool = False, debug: bool = False, pause: bool = False, test:bool = False, test_mode: List[str] = None):
        
        self.game = TrafficEnv(roads=roads, players=players, cars=cars, controllers=controllers, goals=goals)

        def start(self):
            pass

class GameControllerCLI(GameController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start(self):
        self.game_over = [False] * self.game.players
        self.scores = [0] * self.game.players
        
        while not all(self.game_over):
            self.game_over, self.scores = self.game.play_step()

        print(f"Game Over:")
        for player in range(self.game.players):
            print(f"player {player} score {self.scores[player]}")
        self.game_over = [False] * self.game.players
        self.game.reset()

class GameControllerGUI(GameController):
    def __init__(self, roads: List[Road], players: int, cars: Optional[List[Car]] = None, controllers: Optional[List[AstarCarController]] = None, 
                 goals: Optional[List[Goal]] = None, segmentation: bool = False, manual: bool = False, debug: bool = False, pause: bool = False, test:bool = False, test_mode: List[str] = None):
        super().__init__(roads, players, cars, controllers, goals, segmentation, manual, debug, pause, test, test_mode)
        self.segmentation = segmentation
        self.manual = manual
        self.debug = debug
        self.pause = pause
        self.test = test
        self.test_mode = test_mode

    def start(self):
        CarsWindow(game=self.game, segmentation=self.segmentation, manual=self.manual, debug=self.debug, pause=self.pause, test=self.test, test_mode=self.test_mode)