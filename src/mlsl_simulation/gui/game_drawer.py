from pyglet import shapes
from pyglet import text
from typing import List, Tuple, Union
from mlsl_simulation.game_model.road_network.road_network import Color, Road, Point, Direction, LaneSegment, CrossingSegment, horiz_direction, true_direction
from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.constants import *
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from mlsl_simulation.gui.map_colors import *
from mlsl_simulation.gui.helpful_functions import get_xy_crossingseg
import mlsl_simulation.gui.map_colors

class GameDrawer():

    @classmethod
    def draw_cars(cls, 
                  cars: List[Car], 
                  flash_count: int, 
                  show_reservations: bool, 
                  reservation_management: ReservationManagement) -> List[shapes.Rectangle]:
        
        car_shapes = []

        for car in cars:
            color = car.color if not car.get_death_status() or flash_count <= FLASH_CYCLE / 2 else DEAD_GREY

            car_rect = GameDrawer.draw_car_rect(car, color)
            car_shapes.append(car_rect)


            if show_reservations:
                car_shapes += GameDrawer.draw_brake_line(car, color, reservation_management)

        return car_shapes
    
    @classmethod
    def draw_goals(cls, cars: List[Car]) -> List[shapes.Circle]:
        goal_shapes = []

        game_goals = [car.goal for car in cars]
        for goal in game_goals:
            if goal is not None:
                goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 2, color=goal.color))
                goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 3, color=ROAD_BLUE))
                goal_shapes.append(shapes.Circle(goal.pos.x, goal.pos.y, BLOCK_SIZE // 4, color=goal.color))

        return goal_shapes

    @classmethod
    def draw_map(cls, roads: List[Road]) -> List[Union[shapes.Line, shapes.Rectangle]]:
        map_shapes = []

        for road in roads:
            map_shapes += GameDrawer.draw_road(road)

        for road in roads:
            map_shapes += GameDrawer.draw_lane_lines(road)

        return map_shapes

    @classmethod
    def draw_road(cls, road: Road) -> List[shapes.Rectangle]:
        road_shapes = []

        if road.horizontal:
            road_shapes.append(shapes.Rectangle(0, road.top, WINDOW_WIDTH, road.bottom - road.top,
                                                     color=ROAD_BLUE
                                                     ))
        else:
            road_shapes.append(shapes.Rectangle(road.top, 0, road.bottom - road.top, WINDOW_HEIGHT,
                                                     color=ROAD_BLUE
                                                     ))
            
        return road_shapes

    @classmethod
    def draw_lane_lines(cls, road: Road) -> List[shapes.Line]:
        lane_shapes = []

        for i, lane in enumerate(road.right_lanes + road.left_lanes):
            if road.horizontal:
                if i == len(road.right_lanes) - 1 and len(road.left_lanes) > 0:
                    lane_shapes.append(shapes.Line(0, lane.top + BLOCK_SIZE - LANE_DISPLACEMENT // 2,
                                                        WINDOW_WIDTH, lane.top + BLOCK_SIZE - LANE_DISPLACEMENT // 2,
                                                        LANE_DISPLACEMENT, color=WHITE))
                elif i < len(road.right_lanes + road.left_lanes) - 1:
                    dashed_lines = GameDrawer.draw_dash_line(Point(0, lane.top + BLOCK_SIZE),
                                                  Point(WINDOW_WIDTH, lane.top + BLOCK_SIZE))
                    for line in dashed_lines:
                        lane_shapes.append(line)
                arrow = GameDrawer.draw_arrow(Point(3 * BLOCK_SIZE // 2, lane.top + BLOCK_SIZE // 2),
                                   Point(3 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2), True, lane.direction)
                for line in arrow:
                    lane_shapes.append(line)
            else:
                if i == len(road.right_lanes) - 1 and len(road.left_lanes) > 0:
                    lane_shapes.append(shapes.Line(lane.top + BLOCK_SIZE - LANE_DISPLACEMENT // 2, 0,
                                                        lane.top + BLOCK_SIZE - LANE_DISPLACEMENT // 2, WINDOW_HEIGHT,
                                                        color=WHITE))
                elif i < len(road.right_lanes + road.left_lanes) - 1:
                    dashed_lines = GameDrawer.draw_dash_line(Point(lane.top + BLOCK_SIZE, 0),
                                                  Point(lane.top + BLOCK_SIZE, WINDOW_HEIGHT))
                    for line in dashed_lines:
                        lane_shapes.append(line)
                arrow = GameDrawer.draw_arrow(Point(lane.top + BLOCK_SIZE // 2, 1.5 * BLOCK_SIZE),
                                   Point(lane.top + BLOCK_SIZE // 2, 3 * BLOCK_SIZE), False, lane.direction)
                for line in arrow:
                    lane_shapes.append(line)

        return lane_shapes

    @classmethod
    def draw_dash_line(cls, 
                       start, 
                       end, 
                       width: int = LANE_DISPLACEMENT,
                       color: Tuple[int, int, int] = WHITE, 
                       dash: int = 20) -> List[shapes.Line]:
        """
        Draws a dashed line between two points.

        Args:
            start (shapes.Point): The starting point of the dashed line.
            end (shapes.Point): The ending point of the dashed line.
            width (int, optional): The width of the dashed line. Defaults to LANE_DISPLACEMENT.
            color (Tuple[int, int, int], optional): The color of the dashed line. Defaults to WHITE.
            dash (int, optional): The length of each dash. Defaults to 20.

        Returns:
            List[shapes.Line]: A list of pyglet shapes representing the dashed line.
        """
        lines = []
        # Vertical
        if start.x == end.x:
            length = end.y - start.y
            steps = length // dash
            step_length = length // steps
            for i in range(steps):
                if i % 2 == 0:
                    lines.append(shapes.Line(start.x, start.y + i * step_length,
                                            start.x, start.y + (i + 1) * step_length,
                                            width, color=color))

        # Horizontal
        elif start.y == end.y:
            length = end.x - start.x
            steps = length // dash
            step_length = length // steps
            for i in range(steps):
                if i % 2 == 0:
                    lines.append(shapes.Line(start.x + i * step_length, start.y,
                                            start.x + (i + 1) * step_length, start.y,
                                            width, color=color))
        return lines
    
    @classmethod
    def draw_arrow(cls, 
                   begin, 
                   end, 
                   horizontal: bool, 
                   direction: Direction,
                   tip: int = BLOCK_SIZE // 4, 
                   width: int = LANE_DISPLACEMENT, 
                   color: Tuple[int, int, int] = WHITE) -> List[shapes.Line]:
        """
        Draws an arrow between two points.

        Args:
            begin (shapes.Point): The starting point of the arrow.
            end (shapes.Point): The ending point of the arrow.
            horizontal (bool): Whether the arrow is horizontal.
            direction (Direction): The direction of the arrow.
            tip (int, optional): The size of the arrow tip. Defaults to BLOCK_SIZE // 4.
            width (int, optional): The width of the arrow. Defaults to LANE_DISPLACEMENT.
            color (Tuple[int, int, int], optional): The color of the arrow. Defaults to WHITE.

        Returns:
            List[shapes.Line]: A list of pyglet shapes representing the arrow.
        """
        lines = []
        if horizontal:
            lines.append(shapes.Line(begin.x, begin.y,
                                    end.x, end.y,
                                    width, color=color))
            if direction == Direction.RIGHT:
                lines.append(shapes.Line(end.x, end.y,
                                        end.x - tip, end.y - tip,
                                        width, color=color))
                lines.append(shapes.Line(end.x, end.y,
                                        end.x - tip, end.y + tip,
                                        width, color=color))
            if direction == Direction.LEFT:
                lines.append(shapes.Line(begin.x, begin.y,
                                        begin.x + tip, begin.y - tip,
                                        width, color=color))
                lines.append(shapes.Line(begin.x, begin.y,
                                        begin.x + tip, begin.y + tip,
                                        width, color=color))
        else:
            lines.append(shapes.Line(begin.x, begin.y,
                                    end.x, end.y,
                                    width, color=color))
            if direction == Direction.UP:
                lines.append(shapes.Line(end.x, end.y,
                                        end.x - tip, end.y - tip,
                                        width, color=color))
                lines.append(shapes.Line(end.x, end.y,
                                        end.x + tip, end.y - tip,
                                        width, color=color))
            if direction == Direction.DOWN:
                lines.append(shapes.Line(begin.x, begin.y,
                                        begin.x - tip, begin.y + tip,
                                        width, color=color))
                lines.append(shapes.Line(begin.x, begin.y,
                                        begin.x + tip, begin.y + tip,
                                        width, color=color))
        return lines
    
    @classmethod
    def draw_car_rect(cls, car: Car, color: Color) -> shapes.Rectangle:
        """
        Creates a rectangle shape for a car.

        Args:
            car (Car): The car object.

        Returns:
            shapes.Rectangle: A pyglet rectangle shape representing the car.
        """
        return shapes.Rectangle(
            x=car.pos.x, y=car.pos.y,
            width=car.w, height=car.h,
            color=color
        )
    
    @classmethod
    def draw_lines(cls, *line_coords: int, color: Tuple[int, int, int], width: int = 2) -> List[shapes.Line]:
        """
        Creates lines from given coordinates.

        Args:
            *line_coords (int): The coordinates of the lines.
            color (Tuple[int, int, int]): The color of the lines.
            width (int, optional): The width of the lines. Defaults to 2.

        Returns:
            List[shapes.Line]: A list of pyglet shapes representing the lines.
        """
        lines = []
        for i in range(0, len(line_coords) - 2, 2):
            lines.append(
                shapes.Line(line_coords[i], line_coords[i + 1], line_coords[i + 2], line_coords[i + 3], color=color,
                            thickness=width))
        return lines
    
    @classmethod
    def draw_brake_line(cls, car: Car, color: Color, reservation_management: ReservationManagement) -> List[shapes.Line]:
        """
        Creates a brake line for a car..

        Args:
            car (Car): The car object.

        Returns:
            List[shapes.Line]: A list of pyglet shapes representing the brake line.
        """
        lines:List[shapes.Line] = []
        reservations = reservation_management.get_car_reservations(car.id)
        for i, seg_info in enumerate(reservations):
            segment = seg_info.segment
            if not seg_info.turn:
                if true_direction[seg_info.direction] or isinstance(segment, LaneSegment):
                    x_begin = segment.h_begin + seg_info.begin if horiz_direction[seg_info.direction] else segment.h_begin + BLOCK_SIZE // 2
                    y_begin = segment.v_begin + BLOCK_SIZE // 2 if horiz_direction[seg_info.direction] else segment.v_begin + seg_info.begin
                    x_end = segment.h_begin + seg_info.end if horiz_direction[seg_info.direction] else segment.h_begin + BLOCK_SIZE // 2
                    y_end = segment.v_begin + BLOCK_SIZE // 2  if horiz_direction[seg_info.direction] else segment.v_begin + seg_info.end
                else:
                    x_begin = segment.h_begin + segment.length + seg_info.begin if horiz_direction[seg_info.direction] else segment.h_begin + BLOCK_SIZE // 2
                    y_begin = segment.v_begin + BLOCK_SIZE // 2 if horiz_direction[seg_info.direction] else segment.v_begin + segment.length + seg_info.begin
                    x_end = segment.h_begin + segment.length + seg_info.end if horiz_direction[seg_info.direction] else segment.h_begin + BLOCK_SIZE // 2
                    y_end = segment.v_begin + BLOCK_SIZE // 2  if horiz_direction[seg_info.direction] else segment.v_begin + segment.length + seg_info.end

                lines.append(shapes.Line(x= x_begin,\
                                        y= y_begin, \
                                        x2= x_end, \
                                        y2= y_end, \
                                        color=color,
                                        thickness=5))
            else:
                if horiz_direction[reservations[i - 1].direction]:
                    x_begin = segment.h_begin if true_direction[reservations[i - 1].direction] else segment.h_begin + segment.length
                    y_begin = segment.v_begin + segment.length // 2 
                    x_end = segment.h_begin + segment.length // 2 
                    y_end = segment.v_begin + segment.length if true_direction[seg_info.direction] else segment.v_begin
                else:
                    x_begin = segment.h_begin + segment.length // 2
                    y_begin = segment.v_begin if true_direction[reservations[i - 1].direction] else segment.v_begin + segment.length
                    x_end = segment.h_begin + segment.length if true_direction[seg_info.direction] else segment.h_begin
                    y_end = segment.v_begin + segment.length // 2

                lines.append(shapes.Line(x= x_begin,\
                                         y= y_begin, \
                                         x2= segment.h_begin + segment.length // 2, \
                                         y2= segment.v_begin + segment.length // 2, \
                                         color=color,
                                         thickness=5))
                lines.append(shapes.Line(x= segment.h_begin + segment.length // 2,\
                                         y= segment.v_begin + segment.length // 2, \
                                         x2= x_end, \
                                         y2= y_end, \
                                         color=color,
                                         thickness=5))

        return lines