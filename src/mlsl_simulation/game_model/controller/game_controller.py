import pyglet

from typing import List
from mlsl_simulation.game_model.controller.abstract_game_controller import AbstractGameController
from mlsl_simulation.game_model.constants import TIME_PER_FRAME
from mlsl_simulation.game_model.game_model import TrafficEnv
from mlsl_simulation.game_model.road_network.road_network import Road
from mlsl_simulation.gui.pyglet_gui import GameWindow
from mlsl_simulation.gui.render_mode import RenderMode

class GameController(AbstractGameController):
    def __init__(
            self, 
            roads: List[Road], 
            players: int,
            render_mode: RenderMode,
            show_reservation: bool, 
            ):
        
        super().__init__(roads, players, render_mode, show_reservation) 

        self.game_model: TrafficEnv = TrafficEnv(roads=self.roads, players=self.players)
        self.done = None


    def run(self) -> None:
        if self.render_mode.value:
            self.frame_count = 0
            self._run_gui()    
        else:
            self._run_no_gui()

        self.game_model.current_state()


    def _run_gui(self) -> None:
        self._start_new_game()
        pyglet.app.run()


    def _start_new_game(self) -> None:
        self.game_model.reset()
        self.done = None
        self.frame_count = 0

        if hasattr(self, 'window') and self.window:
            self.window.reset_model(self.game_model.cars, self.game_model.roads)
        else:
            self.window = GameWindow(self.game_model.cars, self.game_model.roads, self.game_model.reservation_management, show_reservations=self.show_reservation)

        pyglet.clock.unschedule(self._update_gui)
        pyglet.clock.schedule_interval(self._update_gui, (1 / TIME_PER_FRAME))


    def _update_gui(self, delta_time: float) -> None:
        if not self.window.pause and not self.done == None:
            self._start_new_game()
        elif not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0

            self.done = self.game_model.play_step()

            if not self.done == None:
                self.window.pause = True

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME


    def _run_no_gui(self) -> None:
        while self.done == None:
            self.done = self.game_model.play_step()
