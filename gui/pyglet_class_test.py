import pyglet
from pyglet import shapes

from game_model.constants import *
from game_model.helper_functions import create_segments
from game_model.road_network import Direction, Point, LaneSegment, CrossingSegment, true_direction, Road
from gui.colors import colors
from gui.helpful_functions import draw_dash_line, draw_arrow
from gui.map_colors import *


class CarsWindowTest(pyglet.window.Window):
    def __init__(self, roads):
        super().__init__()
        self.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pos = Point(0, 0)
        self.pos.x, self.pos.y = self.get_location()
        self.set_location(self.pos.x - 300, self.pos.y - 200)

        self.roads = roads
        self.background = shapes.Rectangle(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, color=PALE_GREEN)

        create_segments(self.roads)

        self.frames_count = 0

        self.road_shapes = []
        self.seg = roads[0].right_lanes[0].segments[0]

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
                    dashed_lines = draw_dash_line(Point(0, lane.top + BLOCK_SIZE),
                                                  Point(WINDOW_WIDTH, lane.top + BLOCK_SIZE))
                    for line in dashed_lines:
                        self.road_shapes.append(line)
                arrow = draw_arrow(Point(1.5 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2),
                                   Point(3 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2), True, lane.direction)
                for line in arrow:
                    self.road_shapes.append(line)
            else:
                if i == len(road.right_lanes) - 1 and len(road.left_lanes) > 0:
                    self.road_shapes.append(shapes.Line(lane.top + BLOCK_SIZE, 0,
                                                        lane.top + BLOCK_SIZE, WINDOW_HEIGHT,
                                                        color=WHITE))
                elif i < len(road.right_lanes + road.left_lanes) - 1:
                    dashed_lines = draw_dash_line(Point(lane.top + BLOCK_SIZE, 0),
                                                  Point(lane.top + BLOCK_SIZE, WINDOW_HEIGHT))
                    for line in dashed_lines:
                        self.road_shapes.append(line)
                arrow = draw_arrow(Point(lane.top + BLOCK_SIZE // 2, 1.5 * BLOCK_SIZE),
                                   Point(lane.top + BLOCK_SIZE // 2, 3 * BLOCK_SIZE), False, lane.direction)
                for line in arrow:
                    self.road_shapes.append(line)


if __name__ == '__main__':

    road_bottom = Road("bottom", True, 0, 1, 0)
    road_right = Road("right", False, WINDOW_WIDTH - BLOCK_SIZE, 0, 1)
    road_top = Road("top", True, WINDOW_HEIGHT - BLOCK_SIZE, 0, 1)
    road_left = Road("left", False, 0, 1, 0)

    road_h1 = Road("h1", True, 145, 0, 2)
    road_h2 = Road("h2", True, 330, 3, 3)
    road_h3 = Road("h3", True, 675, 2, 0)
    road_v1 = Road("v1", False, 320, 0, 2)
    road_v2 = Road("v2", False, 680, 3, 3)
    road_v3 = Road("v3", False, 1200, 2, 0)

    # one_road = Road("r1", True, 400, 3, 3)

    roads = [road_top, road_bottom, road_left, road_right, road_h1, road_h2, road_h3, road_v1, road_v2, road_v3]
    # roads = [road_top, road_bottom, road_left, road_right, one_road]
    players = 1

    CarsWindowTest(roads)
