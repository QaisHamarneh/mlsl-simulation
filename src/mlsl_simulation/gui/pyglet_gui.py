import pyglet
from pyglet import shapes
from typing import List, Union
from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.road_network.road_network import Point, Road
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from mlsl_simulation.gui.renderer import Renderer
from mlsl_simulation.gui.game_drawer import GameDrawer
from mlsl_simulation.gui.helpful_functions import *


class GameWindow(pyglet.window.Window):
    def __init__(
            self, 
            cars: List[Car],
            roads: List[Road],
            reservation_management: ReservationManagement,
            show_reservations: bool, 
            debug: bool = False
            ) -> None:
        """
        Initialize the CarsWindow.

        Args:
            game_model (TrafficEnv): The game environment.
            debug (bool, optional): Flag for debug mode. Defaults to False.
        """
        super().__init__()
        scale = self.get_pixel_ratio()
        
        logical_width = int(WINDOW_WIDTH / scale)
        logical_height = int(WINDOW_HEIGHT / scale)
        
        self.set_size(logical_width, logical_height)
        self.set_minimum_size(logical_width, logical_height)
        self.set_location(0, 0)
        self.renderer = Renderer(self)
        
        self.cars = cars
        self.roads = roads
        self.map_shapes: List[Union[shapes.Line, shapes.Rectangle]] = GameDrawer.draw_map(self.roads)

        self.reservation_management = reservation_management

        self.show_reservations: bool = show_reservations

        self.debug: bool = debug
        self._test_results = None

        self.pause: bool = False
        self.flash_count: int = 0

    def reset_model(self, cars: List[Car], roads: List[Road]) -> None:
        self.cars = cars
        self.roads = roads
        self.map_shapes = GameDrawer.draw_map(self.roads)
        self.flash_count = 0
        self.pause = False
        self._test_results = None

    @property
    def test_results(self) -> None | List[Tuple[bool, str]]:
        return self._test_results
    
    @test_results.setter
    def test_results(self, value: None | List[Tuple[bool, str]]) -> None:
        if value is not None:
            self._test_results = value

    def on_draw(self) -> None:
        """
        Handle the draw event to update the window content.
        """
        self.flash_count += TIME_PER_FRAME if not self.flash_count >= FLASH_CYCLE else -self.flash_count
        
        game_shapes = []
        game_shapes += self.map_shapes
        game_shapes += GameDrawer.draw_goals(self.cars)
        game_shapes += GameDrawer.draw_cars(self.cars, self.flash_count, self.show_reservations, self.reservation_management, self.debug)
        game_shapes.append(GameDrawer.draw_test_results(self.roads, self.test_results))
        self.renderer.render(game_shapes)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """
        Handle key press events.
        Space key toggles pause state.

        Args:
            symbol (int): The key symbol pressed.
            modifiers (int): The modifier keys pressed.
        """
        if symbol == pyglet.window.key.SPACE:
            self.pause = not self.pause
