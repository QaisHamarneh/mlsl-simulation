from typing import List
from game_model.constants import TIME_PER_FRAME, FLASH_CYCLE
from game_model.game_model import TrafficEnv
from game_model.Tester import SimulationTester
from game_model.road_network import Road
from gui.pyglet_gui import CarsWindow
from gymnasium_env.mlsl_env import MlslEnv

import pyglet

class GameController:
    def __init__(self, 
                 gui: bool, 
                 roads: List[Road], 
                 npcs: int,
                 agents: int = 0,  
                 debug: bool = False, 
                 test_mode: List[str] = None):
        
        self.gui = gui

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, npcs=npcs, agents=agents)
        self.game_over: bool = False

        self.debug: bool = debug
        self.test_mode = test_mode
        if test_mode is not None:
            self.sim_tester: SimulationTester = SimulationTester(self.game_model, self.test_mode)

    def run_game(self) -> None:
        if self.game_model.agents > 0:
            self._run_gymnasium()
        elif self.gui:
            self.frame_count = 0
            self._run_gui()
        else:
            self._run_cli()

    def _run_gui(self) -> None:
        self.window = CarsWindow(debug=self.debug, game_model=self.game_model)
        pyglet.clock.schedule_interval(self._update_gui, (1 / TIME_PER_FRAME))
        pyglet.app.run()

    def _run_cli(self) -> None:
        while not self.game_over:
            self.game_over = self.game_model.play_step()

            if not self.game_over:
                self.game_over = self._check_deadlock()

        self._game_over_state(self.game_model)

    def _run_gymnasium(self) -> None:
        self.env = MlslEnv(game_model=self.game_model)
        pyglet.clock.schedule_interval(self._test, (1 / TIME_PER_FRAME))
        pyglet.app.run()

    def _test(self, delta_time: float) -> None:
        _, _, self.game_over = self.env.step([(1,0)])
        self.env.render()
        if self.game_over:
            self._game_over_state(self.game_model)
            pyglet.app.exit()

    def _update_gui(self, delta_time: float) -> None:
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0
            self.game_over = self.game_model.play_step()

            if self.test_mode is not None:
                test_results = self.sim_tester.run()
                self.window.test_results = test_results

            if not self.game_over:
                self.game_over = self._check_deadlock()

            if self.game_over:
                self._game_over_state(self.game_model)
                pyglet.app.exit()

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME
            self.window.flash_count += TIME_PER_FRAME if not self.window.flash_count >= FLASH_CYCLE else -self.window.flash_count

    def _check_deadlock(self) -> bool:
        deadlock = [True if car.speed == 0 else False for car in self.game_model.cars]
        if all(deadlock):
            print("___________________________________________________________________________")
            print("Deadlock between all cars.")
            print("___________________________________________________________________________")
            return True
        else:
            return False
        
    def _game_over_state(self, game_model: TrafficEnv) -> None:
        print(f"Game Over:")
        for car in game_model.cars:
            print(f"car {car.name} score {car.score}")
            #Todo: print reason, if car is dead
