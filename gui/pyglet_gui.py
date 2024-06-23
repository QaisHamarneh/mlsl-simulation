import pyglet

from game_model.constants import *
from game_model.road_network import Point
from gui.helpful_functions import *


class CarsWindow(pyglet.window.Window):
    def __init__(self, game, controllers, segmentation=False, manual=False, debug=False, pause=False):
        super().__init__()
        self.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pos = Point(0, 0)
        self.pos.x, self.pos.y = self.get_location()
        self.set_location(self.pos.x - 300, self.pos.y - 200)

        self.game = game
        self.controllers = controllers
        self.segmentation = segmentation
        self.frames_count = 0
        self.manual = manual

        self.game_over = [False] * self.game.players
        self.pause = pause
        self.scores = [0] * self.game.players

        self.road_shapes = []
        self.goal_shapes = []
        self.car_shapes = []
        self.debug = debug

        for road in self.game.roads:
            self._draw_road(road)
        for road in self.game.roads:
            self._draw_lane_lines(road)

        self.event_loop = pyglet.app.EventLoop()

        pyglet.app.run(0.1)

    def on_draw(self):
        self.clear()
        if not self.pause and self.frames_count % FRAME_RATE == 0:
            self._update_game()
            self.frames_count = 0
        self._update_cars()
        self._update_goals()
        background = shapes.Rectangle(x=0, y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, color=PALE_GREEN)
        background.draw()
        for shape in self.road_shapes:
            shape.draw()
        for shape in self.goal_shapes:
            shape.draw()
        for shape in self.car_shapes:
            shape.draw()
        if not self.pause:
            self.frames_count += FRAME_RATE

    def _update_game(self):
        for player in range(self.game.players):
            if not self.game_over[player]:
                self.game_over[player], self.scores[player] = self.game.play_step(player,
                                                                                  self.controllers[player].get_action())
        if all(self.game_over):
            print(f"Game Over:")
            for player in range(self.game.players):
                print(f"player {player} score {self.scores[player]}")
            self.game_over = [False] * self.game.players
            self.game.reset()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            self.pause = not self.pause

    def _update_cars(self):
        self.car_shapes = []
        for player, car in enumerate(self.game.cars):
            car_rect = create_car_rect(car)
            car_tri = None
            car_res_box = None
            if car.res[0]["dir"] == Direction.RIGHT:

                car_tri = shapes.Triangle(car.pos.x + car.w, car.pos.y,
                                          car.pos.x + car.w, car.pos.y + car.h,
                                          car.pos.x + car.w + car.h // 4,
                                          car.pos.y + car.h // 2,
                                          car.color if not car.dead else DEAD_GREY)

                if car.changing_lane:
                    x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                    car_res_box = create_lines(x, y, x + car.get_braking_distance(), y,
                                               x + car.get_braking_distance() + h // 4,
                                               y + h // 2,
                                               x + car.get_braking_distance(), y + h,
                                               x, y + h, x, y,
                                               color=car.color, width=2)



            elif car.res[0]["dir"] == Direction.LEFT:

                car_tri = shapes.Triangle(car.pos.x, car.pos.y,
                                          car.pos.x, car.pos.y + car.h,
                                          car.pos.x - car.h // 4,
                                          car.pos.y + car.h // 2,
                                          car.color if not car.dead else DEAD_GREY)

                if car.changing_lane:
                    x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                    car_res_box = create_lines(x + w, y, x + w - car.get_braking_distance(), y,
                                               x + w - car.get_braking_distance() - h // 4,
                                               y + h // 2,
                                               x + w - car.get_braking_distance(), y + h,
                                               x + w, y + h, x + w, y,
                                               color=car.color, width=2)

            elif car.res[0]["dir"] == Direction.UP:

                car_tri = shapes.Triangle(car.pos.x, car.pos.y + car.h,
                                          car.pos.x + car.w, car.pos.y + car.h,
                                          car.pos.x + car.w // 2,
                                          car.pos.y + car.h + car.h // 4,
                                          car.color if not car.dead else DEAD_GREY)

                if car.changing_lane:
                    x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                    car_res_box = create_lines(x, y, x, y + car.get_braking_distance(),
                                               x + w // 2, y + car.get_braking_distance() + w // 4,
                                               x + w, y + car.get_braking_distance(),
                                               x + w, y, x, y,
                                               color=car.color, width=2)

            elif car.res[0]["dir"] == Direction.DOWN:

                car_tri = shapes.Triangle(car.pos.x, car.pos.y,
                                          car.pos.x + car.w, car.pos.y,
                                          car.pos.x + car.w // 2,
                                          car.pos.y - car.h // 4,
                                          car.color if not car.dead else DEAD_GREY)

                if car.changing_lane:
                    x, y, w, h = car.return_updated_position(car.reserved_segment[1])
                    car_res_box = create_lines(x, y + h, x, y - car.get_braking_distance() + h,
                                               x + w // 2, y - car.get_braking_distance() - w // 4 + h,
                                               x + w, y - car.get_braking_distance() + h,
                                               x + w, y + h, x, y + h,
                                               color=car.color, width=2)

            if self.debug and car.changing_lane:
                self.pause = True

            self.car_shapes.append(car_rect)

            brake_box_points = brake_box(car, self.debug)

            self.car_shapes.append(car_tri)
            self.car_shapes += brake_box_points
            if car_res_box is not None:
                self.car_shapes += car_res_box

    def _update_goals(self):
        self.goal_shapes = []
        for goal in self.game.goals:
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 2, color=goal.color))
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 3, color=ROAD_BLUE))
            self.goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 4, color=goal.color))

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

    """
                if self.segmentation:
                    for segment in car.get_size_segments():
                        if isinstance(segment["seg"], LaneSegment):
                            begin_x = segment["seg"].begin + segment["begin"] if segment["seg"].lane.road.horizontal \
                                else segment["seg"].lane.top
                            begin_y = segment["seg"].lane.top if segment["seg"].lane.road.horizontal \
                                else segment["seg"].begin + segment["begin"]
                            end_x = segment["seg"].begin + segment["end"] if segment["seg"].lane.road.horizontal \
                                else segment["seg"].lane.top + BLOCK_SIZE
                            end_y = segment["seg"].lane.top + BLOCK_SIZE if segment["seg"].lane.road.horizontal \
                                else segment["seg"].begin + segment["end"]
                        else:
                            if true_direction[segment["dir"]]:
                                begin_x = segment["seg"].vert_lane.top + segment["begin"] if horiz_direction[segment["dir"]] \
                                    else segment["seg"].vert_lane.top
                                begin_y = segment["seg"].horiz_lane.top if horiz_direction[segment["dir"]] \
                                    else segment["seg"].horiz_lane.top + segment["begin"]
                                end_x = segment["seg"].vert_lane.top + segment["end"] if horiz_direction[segment["dir"]] \
                                    else segment["seg"].vert_lane.top + BLOCK_SIZE
                                end_y = segment["seg"].horiz_lane.top + BLOCK_SIZE if horiz_direction[segment["dir"]] \
                                    else segment["seg"].horiz_lane.top + segment["end"]
                            else:
                                begin_x = segment["seg"].vert_lane.top + BLOCK_SIZE + segment["begin"] if horiz_direction[segment["dir"]] \
                                    else segment["seg"].vert_lane.top
                                begin_y = segment["seg"].horiz_lane.top if horiz_direction[segment["dir"]] \
                                    else segment["seg"].horiz_lane.top + BLOCK_SIZE + segment["begin"]
                                end_x = segment["seg"].vert_lane.top + BLOCK_SIZE + segment["end"] if horiz_direction[segment["dir"]] \
                                    else segment["seg"].vert_lane.top + BLOCK_SIZE
                                end_y = segment["seg"].horiz_lane.top + BLOCK_SIZE if horiz_direction[segment["dir"]] \
                                    else segment["seg"].horiz_lane.top + BLOCK_SIZE + segment["end"]
    
                        self.car_shapes.append(shapes.Rectangle(
                            x=min(begin_x, end_x), y=min(begin_y, end_y),
                            width=abs(end_x - begin_x), height=abs(end_y - begin_y),
                            color=car.color if not car.dead else DEAD_GREY))
                else:"""
