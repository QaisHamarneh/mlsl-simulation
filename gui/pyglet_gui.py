import pyglet
from typing import List, Optional

from game_model.road_network import Point, Road
from gui.helpful_functions import *


class CarsWindow(pyglet.window.Window):
    def __init__(self, debug: bool = False) -> None:
        """
        Initialize the CarsWindow.

        Args:
            game (TrafficEnv): The game environment.
            debug (bool, optional): Flag for debug mode. Defaults to False.
            test_mode (List[str], optional): List of debug modes. Defaults to None.
        """
        super().__init__()
        self.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pos: Point = Point(0, 0)
        self.pos.x, self.pos.y = self.get_location()
        self.set_location(self.pos.x - 300, self.pos.y - 200)

        self.batch = pyglet.graphics.Batch()

        self.pause: bool = False
        self.flash_count: int = 0

        self.road_shapes = []
        self.goal_shapes = []
        self.car_shapes = []

        self.debug: bool = debug
        self.test_shapes = None
        self.test_params = None

        self.event_loop = pyglet.app.EventLoop()

    def on_draw(self) -> None:
        """
        Handle the draw event to update the window content.
        """
        pyglet.gl.glClearColor(*[c / 255 for c in PALE_GREEN], 1)
        self.clear()
        for road in self.road_shapes:
            road.batch = self.batch
        for goal in self.goal_shapes:
            goal.batch = self.batch
        for car in self.car_shapes:
            car.batch = self.batch
        if self.test_shapes is not None:
            self.test_shapes = self.batch
        self.batch.draw()

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

    def render_test_results(self, roads: List[Road], test_results: Optional[List[Tuple[bool, str]]]):
        if self.test_params is None:
            self.test_params = find_greatest_gap(roads)

        if test_results is not None:
            self.test_shapes = create_test_result_shape(test_results, *self.test_params)

    def update_render_data(self, cars: List[Car]):
        self._render_cars(cars)
        self._render_goals(cars)

    def _render_cars(self, cars: List[Car]) -> None:
        """
        Update the car shapes for rendering.
        """
        self.car_shapes = []
        for car in cars:
            car_rect = create_car_rect(car, self.flash_count)

            if not self.pause:
                self.flash_count += TIME_PER_FRAME if not self.flash_count >= FLASH_CYCLE else -self.flash_count

            car_res_box = None
            if car.res[0].direction == Direction.RIGHT:

                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = create_lines(x, y, x + car.get_braking_distance(), y,
                                            x + car.get_braking_distance(), y + h,
                                            x, y + h, x, y,
                                            color=car.color, width=2)

            elif car.res[0].direction == Direction.LEFT:

                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = create_lines(x + w, y, x + w - car.get_braking_distance(), y,
                                            x + w - car.get_braking_distance(), y + h,
                                            x + w, y + h, x + w, y,
                                            color=car.color, width=2)

            elif car.res[0].direction == Direction.UP:
                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = create_lines(x, y, x, y + car.get_braking_distance(),
                                            x + w, y + car.get_braking_distance(),
                                            x + w, y, x, y,
                                            color=car.color, width=2)

            elif car.res[0].direction == Direction.DOWN:
                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = create_lines(x, y + h, x, y - car.get_braking_distance() + h,
                                            x + w, y - car.get_braking_distance() + h,
                                            x + w, y + h, x, y + h,
                                            color=car.color, width=2)

            if self.debug and car.changing_lane:
                self.pause = True

            self.car_shapes.append(car_rect)

            brake_box_points = brake_box(car, self.debug)
            self.car_shapes += brake_box_points
            if car_res_box is not None:
                self.car_shapes += car_res_box

    def _render_goals(self, cars: List[Car]) -> None:
        """
        Update the goal shapes for rendering.
        """
        self.goal_shapes = []
        game_goals = [car.goal for car in cars]
        for goal in game_goals:
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 2, color=goal.color))
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 3, color=ROAD_BLUE))
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 4, color=goal.color))

    def render_map(self, roads: List[Road]):
        for road in roads:
            self._render_roads(road)
        for road in roads:
            self._render_lane_lines(road) 

    def _render_roads(self, road: Road) -> None:
        """
        Draw the road shapes.

        Args:
            road (Road): The road to draw.
        """
        if road.horizontal:
            self.road_shapes.append(shapes.Rectangle(0, road.top, WINDOW_WIDTH, road.bottom - road.top,
                                                     color=ROAD_BLUE
                                                     ))
        else:
            self.road_shapes.append(shapes.Rectangle(road.top, 0, road.bottom - road.top, WINDOW_HEIGHT,
                                                     color=ROAD_BLUE
                                                     ))

    def _render_lane_lines(self, road: Road) -> None:
        """
        Draw the lane lines on the road.

        Args:
            road (Road): The road to draw lane lines on.
        """
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
