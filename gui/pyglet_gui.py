from game_model.Tester import SimulationTester

import pyglet
from typing import List

from controller.astar_car_controller import AstarCarController
from game_model.game_model import TrafficEnv
from game_model.road_network import Point, Road
from gui.helpful_functions import *




class CarsWindow(pyglet.window.Window):
    def __init__(self, game: 'TrafficEnv', controllers: List['AstarCarController'], segmentation: bool = False, manual: bool = False, debug: bool = False, pause: bool = False,
                 test:bool = False, test_mode: List[str] = None ) -> None:
        """
        Initialize the CarsWindow.

        Args:
            game (TrafficEnv): The game environment.
            controllers (List[AstarCarController]): List of car controllers.
            segmentation (bool, optional): Flag for segmentation. Defaults to False.
            manual (bool, optional): Flag for manual control. Defaults to False.
            debug (bool, optional): Flag for debug mode. Defaults to False.
            pause (bool, optional): Flag for pause state. Defaults to False.
            test (bool, optional): Flag for test mode. Defaults to False.
            test_mode (List[str], optional): List of debug modes. Defaults to None.
        """
        super().__init__()
        self.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pos: Point = Point(0, 0)
        self.pos.x, self.pos.y = self.get_location()
        self.set_location(self.pos.x - 300, self.pos.y - 200)

        self.game: TrafficEnv = game
        self.controllers: List[AstarCarController] = controllers
        self.segmentation: bool = segmentation
        self.frames_count: int = 0
        self.manual: bool = manual

        self.batch = pyglet.graphics.Batch()

        self.game_over: List[bool]= [False] * self.game.players
        self.pause: bool = pause
        self.scores: List[int] = [0] * self.game.players

        self.road_shapes = []
        self.goal_shapes = []
        self.car_shapes = []

        self.debug: bool = debug
        self.test = test
        self.tester = SimulationTester(self.game, self.controllers, test_mode)
        self.test_shape = None
        self.test_params = find_greatest_gap(self.game.roads)

        self.flash_count = 0

        for road in self.game.roads:
            self._draw_road(road)
        for road in self.game.roads:
            self._draw_lane_lines(road)

        self.event_loop = pyglet.app.EventLoop()
        pyglet.app.run(TIME_PER_FRAME)

    def on_draw(self) -> None:
        """
        Handle the draw event to update the window content.
        """
        pyglet.gl.glClearColor(*[c / 255 for c in PALE_GREEN], 1)
        self.clear()
        if not self.pause and self.frames_count % (int(1/TIME_PER_FRAME)) == 0:
            self._update_game()
            self.frames_count = 0
        self._update_cars()
        self._update_goals()
        for road in self.road_shapes:
            road.batch = self.batch
        for goal in self.goal_shapes:
            goal.batch = self.batch
        for car in self.car_shapes:
            car.batch = self.batch
        if self.test_shape is not None:
            self.test_shape.batch = self.batch
        self.batch.draw()
        if not self.pause:
            self.frames_count += int(1/TIME_PER_FRAME)


    def _update_game(self) -> None:
        """
        Update the game state for each player.
        Runs all wanted tests.
        Checks for game over state.
        """
        for player in range(self.game.players):
            if not self.game_over[player]:
                self.game_over[player], self.scores[player] = self.game.play_step(player,
                                                                                  self.controllers[player].get_action())
        if self.test:
            test_results = self.tester.run()
            if test_results is not None:
                self.test_shape = create_test_result_shape(test_results, *self.test_params)

        if all(self.game_over):
            print(f"Game Over:")
            for player in range(self.game.players):
                print(f"player {player} score {self.scores[player]}")
            self.game_over = [False] * self.game.players
            self.game.reset()

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

    def _update_cars(self) -> None:
        """
        Update the car shapes for rendering.
        """
        self.car_shapes = []
        for car in self.game.cars:
            car_rect = create_car_rect(car, self.flash_count)

            if not self.pause:
                self.flash_count += TIME_PER_FRAME if not self.flash_count >= FLASH_CYCLE else -self.flash_count

            if not car.dead:
                car_res_box = None
                if car.res[0]["dir"] == Direction.RIGHT:

                    if car.changing_lane:
                        x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                        car_res_box = create_lines(x, y, x + car.get_braking_distance(), y,
                                                x + car.get_braking_distance(), y + h,
                                                x, y + h, x, y,
                                                color=car.color, width=2)

                elif car.res[0]["dir"] == Direction.LEFT:

                    if car.changing_lane:
                        x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                        car_res_box = create_lines(x + w, y, x + w - car.get_braking_distance(), y,
                                                x + w - car.get_braking_distance(), y + h,
                                                x + w, y + h, x + w, y,
                                                color=car.color, width=2)

                elif car.res[0]["dir"] == Direction.UP:
                    if car.changing_lane:
                        x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                        car_res_box = create_lines(x, y, x, y + car.get_braking_distance(),
                                                x + w, y + car.get_braking_distance(),
                                                x + w, y, x, y,
                                                color=car.color, width=2)

                elif car.res[0]["dir"] == Direction.DOWN:
                    if car.changing_lane:
                        x, y, w, h = car.return_updated_position(car.reserved_segment[1])
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
            else:
                self.car_shapes.append(car_rect)

    def _update_goals(self) -> None:
        """
        Update the goal shapes for rendering.
        """
        self.goal_shapes = []
        for goal in self.game.goals:
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 2, color=goal.color))
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 3, color=ROAD_BLUE))
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 4, color=goal.color))

    def _draw_road(self, road: 'Road') -> None:
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

    def _draw_lane_lines(self, road: 'Road') -> None:
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
