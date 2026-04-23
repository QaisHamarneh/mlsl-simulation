import pyglet
from pyglet import shapes

from mlsl_simulation.game_model.constants import *
from mlsl_simulation.game_model.create_items.create_segments import create_segments
from mlsl_simulation.game_model.road_network.road_network import Direction, Point, LaneSegment, CrossingSegment, true_direction, Road
from mlsl_simulation.gui.colors import colors
from mlsl_simulation.gui.game_drawer import GameDrawer
from mlsl_simulation.gui.map_colors import *


class CarsWindowManual(pyglet.window.Window):
    def __init__(self, roads):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Get the display scale factor (2.0 on Retina, 1.0 on standard displays)
        scale = self.get_pixel_ratio()
        
        scaled_width = int(WINDOW_WIDTH / scale)
        scaled_height = int(WINDOW_HEIGHT / scale)
        
        self.set_size(scaled_width, scaled_height)
        self.set_minimum_size(scaled_width, scaled_height)

        # Center the window on the screen
        screen = self.display.get_default_screen()
        x = (screen.width - scaled_width) // 2
        y = (screen.height - scaled_height) // 2
        self.set_location(x, y)

        self.roads = roads
        self.background = shapes.Rectangle(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, color=PALE_GREEN)

        create_segments(self.roads)

        self.frames_count = 0

        self.road_shapes = []
        self.seg = roads[0].right_lanes[0].segments[0]

        self.drawer = GameDrawer()

        self.car = shapes.Rectangle(x=self.seg.vert_lane.top, y=self.seg.horiz_lane.top,
                                    width=BLOCK_SIZE, height=BLOCK_SIZE,
                                    color=colors["red1"])

        for road in self.roads:
            self._draw_road(road)
        for road in self.roads:
            self._draw_lane_lines(road)

        self.event_loop = pyglet.app.EventLoop()
        pyglet.app.run(1 / TIME_PER_FRAME)

    def on_draw(self):
        self.clear()
        self.background.draw()
        for shape in self.road_shapes:
            shape.draw()
        self.car.draw()

    def _manual_update_game(self):
        if isinstance(self.seg, CrossingSegment):
            x = self.seg.vert_lane.top
            y = self.seg.horiz_lane.top
        else:
            if self.seg.lane.road.horizontal:
                x = self.seg.begin if true_direction[self.seg.lane.direction] else self.seg.begin - BLOCK_SIZE
                y = self.seg.lane.top
            else:
                x = self.seg.lane.top
                y = self.seg.begin if true_direction[self.seg.lane.direction] else self.seg.begin - BLOCK_SIZE

        self.car.x = x
        self.car.y = y

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.RIGHT:
            match self.seg:
                case LaneSegment():
                    if self.seg.lane.road.horizontal:
                        if self.seg.lane.direction == Direction.RIGHT:
                            if self.seg.end_crossing is not None:
                                self.seg = self.seg.end_crossing
                case CrossingSegment():
                    if self.seg.connected_segments[Direction.RIGHT] is not None:
                        self.seg = self.seg.connected_segments[Direction.RIGHT]
        if symbol == pyglet.window.key.LEFT:
            match self.seg:
                case LaneSegment():
                    if self.seg.lane.road.horizontal:
                        if self.seg.lane.direction == Direction.LEFT:
                            if self.seg.end_crossing is not None:
                                self.seg = self.seg.end_crossing
                case CrossingSegment():
                    if self.seg.connected_segments[Direction.LEFT] is not None:
                        self.seg = self.seg.connected_segments[Direction.LEFT]
        elif symbol == pyglet.window.key.DOWN:
            match self.seg:
                case LaneSegment():
                    if not self.seg.lane.road.horizontal:
                        if self.seg.lane.direction == Direction.DOWN:
                            if self.seg.end_crossing is not None:
                                self.seg = self.seg.end_crossing
                case CrossingSegment():
                    if self.seg.connected_segments[Direction.DOWN] is not None:
                        self.seg = self.seg.connected_segments[Direction.DOWN]
        elif symbol == pyglet.window.key.UP:
            match self.seg:
                case LaneSegment():
                    if not self.seg.lane.road.horizontal:
                        if self.seg.lane.direction == Direction.UP:
                            if self.seg.end_crossing is not None:
                                self.seg = self.seg.end_crossing
                case CrossingSegment():
                    if self.seg.connected_segments[Direction.UP] is not None:
                        self.seg = self.seg.connected_segments[Direction.UP]

        self._manual_update_game()

    def _draw_road(self, road):
        if road.horizontal:
            self.road_shapes.append(shapes.Rectangle(0, road.top, WINDOW_WIDTH, road.bottom - road.top,
                                                     color=ROAD_BLUE
                                                     ))
        else:
            self.road_shapes.append(shapes.Rectangle(road.top, 0, road.bottom - road.top, WINDOW_HEIGHT,
                                                     color=ROAD_BLUE
                                                     ))

    def _draw_lane_lines(self, road):
        for i, lane in enumerate(road.right_lanes + road.left_lanes):
            if road.horizontal:
                if i == len(road.right_lanes) - 1 and len(road.left_lanes) > 0:
                    self.road_shapes.append(shapes.Line(0, lane.top + BLOCK_SIZE,
                                                        WINDOW_WIDTH, lane.top + BLOCK_SIZE,
                                                        LANE_DISPLACEMENT, color=WHITE))
                elif i < len(road.right_lanes + road.left_lanes) - 1:
                    dashed_lines = self.drawer.draw_dash_line(Point(0, lane.top + BLOCK_SIZE),
                                                  Point(WINDOW_WIDTH, lane.top + BLOCK_SIZE))
                    for line in dashed_lines:
                        self.road_shapes.append(line)
                arrow = self.drawer.draw_arrow(Point(1.5 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2),
                                   Point(3 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2), True, lane.direction)
                for line in arrow:
                    self.road_shapes.append(line)
            else:
                if i == len(road.right_lanes) - 1 and len(road.left_lanes) > 0:
                    self.road_shapes.append(shapes.Line(lane.top + BLOCK_SIZE, 0,
                                                        lane.top + BLOCK_SIZE, WINDOW_HEIGHT,
                                                        color=WHITE))
                elif i < len(road.right_lanes + road.left_lanes) - 1:
                    dashed_lines = self.drawer.draw_dash_line(Point(lane.top + BLOCK_SIZE, 0),
                                                  Point(lane.top + BLOCK_SIZE, WINDOW_HEIGHT))
                    for line in dashed_lines:
                        self.road_shapes.append(line)
                arrow = self.drawer.draw_arrow(Point(lane.top + BLOCK_SIZE // 2, 1.5 * BLOCK_SIZE),
                                   Point(lane.top + BLOCK_SIZE // 2, 3 * BLOCK_SIZE), False, lane.direction)
                for line in arrow:
                    self.road_shapes.append(line)


