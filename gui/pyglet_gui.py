import pyglet
from typing import List
from game_model.game_model import TrafficEnv
from game_model.road_network import Point
from gui.renderer import Renderer
from gui.game_drawer import GameDrawer
from gui.helpful_functions import *


class CarsWindow(pyglet.window.Window):
    def __init__(self, game_model: TrafficEnv, debug: bool = False) -> None:
        """
        Initialize the CarsWindow.

        Args:
            game_model (TrafficEnv): The game environment.
            debug (bool, optional): Flag for debug mode. Defaults to False.
        """
        super().__init__()
        self.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pos: Point = Point(0, 0)
        self.pos.x, self.pos.y = self.get_location()
        self.set_location(self.pos.x - 300, self.pos.y - 200)
        self.renderer = Renderer(self)
        
        self.game_model = game_model
        self.map_shapes: List[Union[shapes.Line, shapes.Rectangle]] = GameDrawer.draw_map(self.game_model.roads)

        self.debug: bool = debug
        self._test_results = None

        self.pause: bool = False
        self.flash_count: int = 0

        self.event_loop = pyglet.app.EventLoop()

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
        game_shapes += GameDrawer.draw_goals(self.game_model.cars)
        game_shapes += GameDrawer.draw_cars(self.game_model.cars, self.flash_count, self.debug)
        game_shapes.append(GameDrawer.draw_test_results(self.game_model.roads, self.test_results))
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
