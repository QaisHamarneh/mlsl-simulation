from typing import Optional, List

from controller.astar_car_controller import AstarCarController
from game_model.constants import TIME_PER_FRAME
from game_model.game_model import TrafficEnv
from game_model.Tester import SimulationTester
from game_model.car import Car
from game_model.road_network import Road
from gui.pyglet_gui import CarsWindow

import pyglet

class GameController:
    def __init__(self, gui: bool, roads: List[Road], players: int, cars: Optional[List[Car]] = None, controllers: Optional[List[AstarCarController]] = None, 
                 debug: bool = False, test_mode: List[str] = None):
        
        self.gui = gui

        self.game: TrafficEnv = TrafficEnv(roads=roads, players=players, cars=cars, controllers=controllers)
        self.game_over: bool = False

        self.debug: bool = debug
        self.test_mode = test_mode
        if test_mode is not None:
            self.sim_tester: SimulationTester = SimulationTester(self.game, self.test_mode)

    def start(self) -> None:
        if self.gui:
            self.frame_count = 0
            self._start_gui()
        else:
            self._start_cli()

    def _start_gui(self) -> None:
        self.window = CarsWindow(debug=self.debug)
        self.window.render_map(roads=self.game.roads)
        pyglet.clock.schedule_interval(self._update, (1 / TIME_PER_FRAME))
        pyglet.app.run()

    def _update(self, delta_time: float) -> None:
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0
            self.game_over = self.game.play_step()
            self.window.update_render_data(self.game.cars)

            if self.test_mode is not None:
                test_results = self.sim_tester.run()
                self.window.render_test_results(self.game.roads, test_results)

            if not self.game_over:
                self.game_over = self._check_deadlock()

            if self.game_over:
                self._game_over_state(self.game)
                pyglet.app.exit()

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME

    def _start_cli(self) -> None:
        while not self.game_over:
            self.game_over = self.game.play_step()

            if not self.game_over:
                self.game_over = self._check_deadlock()

        self._game_over_state(self.game)

    def _check_deadlock(self) -> bool:
        deadlock = [True if car.speed == 0 else False for car in self.game.cars]
        if all(deadlock):
            print("___________________________________________________________________________")
            print("Deadlock between all cars.")
            print("___________________________________________________________________________")
            return True
        else:
            return False
        
    def _game_over_state(self, game: TrafficEnv) -> None:
        print(f"Game Over:")
        for car in game.cars:
            print(f"car {car.name} score {car.score}")
            #Todo: print reason, if car is dead