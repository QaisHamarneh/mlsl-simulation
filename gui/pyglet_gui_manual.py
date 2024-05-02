import pyglet
from pyglet import shapes

from game_model.constants import *
from game_model.game_model import TrafficEnv
from game_model.road_network import Direction, Point, LaneSegment, Road
from gui.helpful_functions import draw_arrow, draw_dash_line


class CarsWindowManual(pyglet.window.Window):
    def __init__(self, game):
        super().__init__()
        self.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_minimum_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pos = Point(0, 0)
        self.pos.x, self.pos.y = self.get_location()
        self.set_location(self.pos.x - 300, self.pos.y - 200)

        self.game = game
        self.frames_count = 0

        self.game_over = [False] * self.game.players
        self.pause = False
        self.scores = [0] * self.game.players

        self.road_shapes = []
        self.goal_shapes = []
        self.car_shapes = []
        self.actions = {"turn": 0, "accelerate": 0, "lane-change": 0}

        for road in self.game.roads:
            self._draw_road(road)
        for road in self.game.roads:
            self._draw_lane_lines(road)

        self.event_loop = pyglet.app.EventLoop()
        pyglet.app.run(1 / FRAME_RATE)

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
            self.frames_count += FRAME_RATE // 10
        self.actions = {"turn": 0, "accelerate": 0, "lane-change": 0}

    def _update_game(self):
        for player in range(self.game.players):
            if not self.game_over[player]:
                self.game_over[player], self.scores[player] = self.game.play_step(player, self.actions)
        if all(self.game_over):
            print(f"Game Over:")
            for player in range(self.game.players):
                print(f"player {player} score {self.scores[player]}")
            self.game_over = [False] * self.game.players
            self.game.reset()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            self.pause = not self.pause
        if symbol == pyglet.window.key.RIGHT:
            if isinstance(self.game.cars[0].res[-1], LaneSegment):
                self.actions["lane-change"] = 1
            else:
                self.actions["turn"] = 1
        elif symbol == pyglet.window.key.LEFT:
            if isinstance(self.game.cars[0].res[-1], LaneSegment):
                self.actions["lane-change"] = -1
            else:
                self.actions["turn"] = 2
        elif symbol == pyglet.window.key.UP:
            self.actions["accelerate"] = 1
        elif symbol == pyglet.window.key.DOWN:
            self.actions["accelerate"] = -1

    def _update_cars(self):
        self.car_shapes = []
        for player, car in enumerate(self.game.cars):
            self.car_shapes.append(shapes.Rectangle(
                x=car.pos.x, y=car.pos.y,
                width=car.w, height=car.h,
                color=car.color if not car.dead else DEAD_GREY))
            if car.res[0]["dir"] == Direction.RIGHT:
                self.car_shapes.append(shapes.Triangle(car.pos.x + car.w, car.pos.y,
                                                       car.pos.x + car.w, car.pos.y + car.h,
                                                       car.pos.x + car.w + car.h // 6,
                                                       car.pos.y + car.h // 2,
                                                       car.color if not car.dead else DEAD_GREY))
            elif car.res[0]["dir"] == Direction.LEFT:
                self.car_shapes.append(shapes.Triangle(car.pos.x, car.pos.y,
                                                       car.pos.x, car.pos.y + car.h,
                                                       car.pos.x - car.h // 6,
                                                       car.pos.y + car.h // 2,
                                                       car.color if not car.dead else DEAD_GREY))
            if car.res[0]["dir"] == Direction.UP:
                self.car_shapes.append(shapes.Triangle(car.pos.x, car.pos.y + car.h,
                                                       car.pos.x + car.w, car.pos.y + car.h,
                                                       car.pos.x + car.w // 2,
                                                       car.pos.y + car.h + car.w // 6,
                                                       car.color if not car.dead else DEAD_GREY))
            if car.res[0]["dir"] == Direction.DOWN:
                self.car_shapes.append(shapes.Triangle(car.pos.x, car.pos.y,
                                                       car.pos.x + car.w, car.pos.y,
                                                       car.pos.x + car.w // 2,
                                                       car.pos.y - car.w // 6,
                                                       car.color if not car.dead else DEAD_GREY))

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
    game = TrafficEnv(players=players, roads=roads)

    CarsWindowManual(game)
