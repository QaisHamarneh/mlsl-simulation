import pyglet
from pyglet import shapes
from pyglet import text
from pyglet.window import Window
from typing import List, Union
from game_model.constants import *
from gui.map_colors import *
from game_model.road_network import Point

class Renderer():
    def __init__(self, window: None | Window = None):
        if window is None:
            display = pyglet.display.get_display()
            screen = display.get_default_screen()
            config = screen.get_best_config()
            context = config.create_context(None)
            window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT, config=config, context=context)
            pos = Point(0, 0)
            pos.x, pos.y = window.get_location()
            window.set_location(pos.x - 300, pos.y - 200)
        self.window = window
        self.batch = pyglet.graphics.Batch()

    def render(self, shapes: List[Union[shapes.Line, shapes.Rectangle, shapes.Circle, text.Label]]) -> None:
        pyglet.gl.glClearColor(*[c / 255 for c in PALE_GREEN], 1)
        self.window.clear()

        for shape in shapes:
            shape.batch = self.batch

        self.batch.draw()

    def close(self):
        self.window.close()