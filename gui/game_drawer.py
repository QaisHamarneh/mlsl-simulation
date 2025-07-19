from pyglet import shapes
from pyglet import text
from typing import List, Tuple, Union
from game_model.road_network import Road, Point, Direction, LaneSegment, CrossingSegment
from game_model.car import Car
from game_model.constants import *
from gui.map_colors import *
from gui.helpful_functions import get_xy_crossingseg, return_updated_position, find_greatest_gap

class GameDrawer():

    @classmethod
    def draw_cars(cls, cars: List[Car], flash_count: int, debug: bool = False) -> List[shapes.Rectangle]:
        car_shapes = []

        for car in cars:
            car_rect = GameDrawer.draw_car_rect(car, flash_count)

            car_res_box = None
            if car.res[0].direction == Direction.RIGHT:

                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = GameDrawer.draw_lines(x, y, x + car.get_braking_distance(), y,
                                            x + car.get_braking_distance(), y + h,
                                            x, y + h, x, y,
                                            color=car.color, width=2)

            elif car.res[0].direction == Direction.LEFT:

                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = GameDrawer.draw_lines(x + w, y, x + w - car.get_braking_distance(), y,
                                            x + w - car.get_braking_distance(), y + h,
                                            x + w, y + h, x + w, y,
                                            color=car.color, width=2)

            elif car.res[0].direction == Direction.UP:
                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = GameDrawer.draw_lines(x, y, x, y + car.get_braking_distance(),
                                            x + w, y + car.get_braking_distance(),
                                            x + w, y, x, y,
                                            color=car.color, width=2)

            elif car.res[0].direction == Direction.DOWN:
                if car.changing_lane:
                    x, y, w, h = return_updated_position(car)
                    car_res_box = GameDrawer.draw_lines(x, y + h, x, y - car.get_braking_distance() + h,
                                            x + w, y - car.get_braking_distance() + h,
                                            x + w, y + h, x, y + h,
                                            color=car.color, width=2)

            car_shapes.append(car_rect)

            brake_box_points = GameDrawer.draw_brake_box(car, debug)
            car_shapes += brake_box_points
            if car_res_box is not None:
                car_shapes += car_res_box

        return car_shapes
    
    @classmethod
    def draw_goals(cls, cars: List[Car]) -> List[shapes.Circle]:
        goal_shapes = []

        game_goals = [car.goal for car in cars]
        for goal in game_goals:
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
                    lane_shapes.append(shapes.Line(0, lane.top + BLOCK_SIZE,
                                                        WINDOW_WIDTH, lane.top + BLOCK_SIZE,
                                                        LANE_DISPLACEMENT, color=WHITE))
                elif i < len(road.right_lanes + road.left_lanes) - 1:
                    dashed_lines = GameDrawer.draw_dash_line(Point(0, lane.top + BLOCK_SIZE),
                                                  Point(WINDOW_WIDTH, lane.top + BLOCK_SIZE))
                    for line in dashed_lines:
                        lane_shapes.append(line)
                arrow = GameDrawer.draw_arrow(Point(1.5 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2),
                                   Point(3 * BLOCK_SIZE, lane.top + BLOCK_SIZE // 2), True, lane.direction)
                for line in arrow:
                    lane_shapes.append(line)
            else:
                if i == len(road.right_lanes) - 1 and len(road.left_lanes) > 0:
                    lane_shapes.append(shapes.Line(lane.top + BLOCK_SIZE, 0,
                                                        lane.top + BLOCK_SIZE, WINDOW_HEIGHT,
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
    def draw_car_rect(cls, car: Car, flash_count: int) -> shapes.Rectangle:
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
            color=car.color if not car.dead or flash_count <= FLASH_CYCLE / 2 else DEAD_GREY
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
    def draw_brake_box(cls, car: 'Car', debug: bool) -> List[Union[shapes.Line, shapes.Rectangle]]:
        """
        Creates a brake box for a car. This is done collecting all points of the brake box on the left and right side separately.

        Args:
            car (Car): The car object.
            debug (bool): Whether to include debug shapes.

        Returns:
            List[Union[shapes.Line, shapes.Rectangle]]: A list of pyglet shapes representing the brake box.
        """
        left_points = []
        right_points = []
        interesting_points = []
        (car_x, car_y) = car.pos.x, car.pos.y

        w = car.w if car.res[0].direction == Direction.UP or car.res[0].direction == Direction.DOWN else car.h

        # left back corner of car based on direction, append points as starting points for the brake box
        if car.res[0].direction == Direction.RIGHT:
            car_y = car_y + car.h
            car_x2, car_y2 = (car_x, car_y - car.h)
        if car.res[0].direction == Direction.DOWN:
            car_x = car_x + car.w
            car_y = car_y + car.h
            car_x2, car_y2 = (car_x - car.w, car_y)
        if car.res[0].direction == Direction.LEFT:
            car_x = car_x + car.w
            car_x2, car_y2 = (car_x, car_y + car.h)
        if car.res[0].direction == Direction.UP:
            car_x2, car_y2 = (car_x + car.w, car_y)

        left_points.append((car_x, car_y))
        right_points.append((car_x2, car_y2))

        remaining_distance = car.get_braking_distance()
        last_dir = car.res[0].direction

        # iterate over all segments of the car's path
        for i in range(0, len(car.res)):
            segment = car.res[i]
            seg = segment.segment

            # case 1: LaneSegment
            if isinstance(seg, LaneSegment):

                if seg.lane.road.horizontal:

                    dis = abs(seg.end - car_x)
                    if dis > remaining_distance:
                        if remaining_distance < car.size:
                            remaining_distance = car.size
                        if last_dir == Direction.RIGHT:
                            car_x += remaining_distance
                            car_x2 += remaining_distance
                        elif last_dir == Direction.LEFT:
                            car_x -= remaining_distance
                            car_x2 -= remaining_distance
                    else:
                        car_x = seg.end
                        car_x2 = seg.end
                        remaining_distance -= dis
                    left_points.append((car_x, car_y))
                    right_points.append((car_x2, car_y2))

                else:
                    dis = abs(seg.end - car_y)
                    if dis > remaining_distance:
                        if remaining_distance < car.size:
                            remaining_distance = car.size
                        if last_dir == Direction.DOWN:
                            car_y -= remaining_distance
                            car_y2 -= remaining_distance
                        elif last_dir == Direction.UP:
                            car_y += remaining_distance
                            car_y2 += remaining_distance
                    else:
                        car_y = seg.end
                        car_y2 = seg.end
                        remaining_distance -= dis
                    left_points.append((car_x, car_y))
                    right_points.append((car_x2, car_y2))
                last_dir = segment.direction



            # case 2: CrossingSegment
            elif isinstance(seg, CrossingSegment):
                # first segment is a crossing segment
                if i == 0:
                    x_anchor, y_anchor = get_xy_crossingseg(seg)
                    interesting_points.append((x_anchor, y_anchor))

                    if segment.direction == Direction.RIGHT:
                        dist = abs(car_x - (x_anchor + BLOCK_SIZE))
                        if dist > remaining_distance:
                            car_x = car_x + remaining_distance
                            car_x2 = car_x2 + remaining_distance
                        else:
                            car_x = x_anchor + BLOCK_SIZE
                            car_x2 = x_anchor + BLOCK_SIZE
                            remaining_distance -= dist

                    elif segment.direction == Direction.LEFT:
                        dist = abs(car_x - (x_anchor - BLOCK_SIZE))
                        if dist > remaining_distance:
                            car_x = car_x - remaining_distance
                            car_x2 = car_x2 - remaining_distance
                        else:
                            car_x = x_anchor - BLOCK_SIZE
                            car_x2 = x_anchor - BLOCK_SIZE
                            remaining_distance -= dist

                    elif segment.direction == Direction.UP:
                        dist = abs(car_y - (y_anchor + BLOCK_SIZE))
                        if dist > remaining_distance:
                            car_y = car_y + remaining_distance
                            car_y2 = car_y2 + remaining_distance
                        else:
                            car_y = y_anchor + BLOCK_SIZE
                            car_y2 = y_anchor + BLOCK_SIZE
                            remaining_distance -= dist

                    elif segment.direction == Direction.DOWN:
                        dist = abs(car_y - (y_anchor - BLOCK_SIZE))
                        if dist > remaining_distance:
                            car_y = car_y - remaining_distance
                            car_y2 = car_y2 - remaining_distance
                        else:
                            car_y = y_anchor - BLOCK_SIZE
                            car_y2 = y_anchor - BLOCK_SIZE
                            remaining_distance -= dist

                    left_points.append((car_x, car_y))
                    right_points.append((car_x2, car_y2))
                    last_dir = segment.direction

                else:

                    # going straight through a crossing segment
                    if last_dir.value == segment.direction.value:

                        if remaining_distance > BLOCK_SIZE:
                            if segment.direction == Direction.RIGHT:
                                car_x += BLOCK_SIZE + LANE_DISPLACEMENT
                                car_x2 += BLOCK_SIZE + LANE_DISPLACEMENT
                            elif segment.direction == Direction.LEFT:
                                car_x -= BLOCK_SIZE + LANE_DISPLACEMENT
                                car_x2 -= BLOCK_SIZE + LANE_DISPLACEMENT
                            elif segment.direction == Direction.UP:
                                car_y += BLOCK_SIZE + LANE_DISPLACEMENT
                                car_y2 += BLOCK_SIZE + LANE_DISPLACEMENT
                            elif segment.direction == Direction.DOWN:
                                car_y -= BLOCK_SIZE + LANE_DISPLACEMENT
                                car_y2 -= BLOCK_SIZE + LANE_DISPLACEMENT

                            remaining_distance -= BLOCK_SIZE
                            remaining_distance -= LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            right_points.append((car_x2, car_y2))
                            last_dir = segment.direction

                        else:

                            if car.res[i - 1].direction == Direction.RIGHT:
                                car_x += BLOCK_SIZE
                                car_x2 += BLOCK_SIZE

                            elif car.res[i - 1].direction == Direction.LEFT:
                                car_x -= BLOCK_SIZE
                                car_x2 -= BLOCK_SIZE

                            elif car.res[i - 1].direction == Direction.UP:
                                car_y += BLOCK_SIZE
                                car_y2 += BLOCK_SIZE

                            elif car.res[i - 1].direction == Direction.DOWN:
                                car_y -= BLOCK_SIZE
                                car_y2 -= BLOCK_SIZE

                            remaining_distance = car.size
                            left_points.append((car_x, car_y))
                            right_points.append((car_x2, car_y2))
                            last_dir = segment.direction

                    elif car.res[i - 1].direction.value - segment.direction.value == 1 or car.res[i - 1].direction.value - \
                            segment.direction.value == -3:  # left turn

                        if car.res[i - 1].direction == Direction.RIGHT:
                            car_x2 = car_x2 + BLOCK_SIZE + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_y2 = car_y2 + BLOCK_SIZE + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            #adjust left side with LANE_DISPLACEMENT
                            car_x = car_x + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_y = car_y + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))


                        if car.res[i - 1].direction == Direction.DOWN:
                            car_y2 = car_y2 - BLOCK_SIZE - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_x2 = car_x2 + BLOCK_SIZE + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            #adjust left side with LANE_DISPLACEMENT
                            car_y = car_y - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_x = car_x + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))


                        if car.res[i - 1].direction == Direction.LEFT:
                            car_x2 = car_x2 - BLOCK_SIZE - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_y2 = car_y2 - BLOCK_SIZE - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))

                            #adjust left side with LANE_DISPLACEMENT
                            car_x = car_x - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_y = car_y - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))


                        if car.res[i - 1].direction == Direction.UP:
                            car_y2 = car_y2 + BLOCK_SIZE + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_x2 = car_x2 - BLOCK_SIZE - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))

                            #adjust left side with LANE_DISPLACEMENT
                            car_y = car_y + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_x = car_x - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))


                        remaining_distance -= BLOCK_SIZE
                        remaining_distance -= LANE_DISPLACEMENT
                        last_dir = segment.direction

                    elif car.res[i - 1].direction.value - segment.direction.value == -1 or car.res[i - 1].direction.value - \
                            segment.direction.value == +3:  # right turn
                        if car.res[i - 1].direction == Direction.RIGHT:
                            car_x = car_x + BLOCK_SIZE + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_y = car_y - BLOCK_SIZE - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            #adjust right side with LANE_DISPLACEMENT
                            car_x2 = car_x2 - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_y2 = car_y2 - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))

                        if car.res[i - 1].direction == Direction.DOWN:
                            car_y = car_y - BLOCK_SIZE - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_x = car_x - BLOCK_SIZE - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            #adjust right side with LANE_DISPLACEMENT
                            car_y2 = car_y2 + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_x2 = car_x2 - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))


                        if car.res[i - 1].direction == Direction.LEFT:
                            car_x = car_x - BLOCK_SIZE - LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_y = car_y + BLOCK_SIZE + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            #adjust right side with LANE_DISPLACEMENT
                            car_x2 = car_x2 + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_y2 = car_y2 + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))

                        if car.res[i - 1].direction == Direction.UP:
                            car_y = car_y + BLOCK_SIZE + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            car_x = car_x + BLOCK_SIZE + LANE_DISPLACEMENT
                            left_points.append((car_x, car_y))
                            #adjust right side with LANE_DISPLACEMENT
                            car_y2 = car_y2 - LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))
                            car_x2 = car_x2 + LANE_DISPLACEMENT
                            right_points.append((car_x2, car_y2))

                        remaining_distance -= BLOCK_SIZE
                        remaining_distance -= LANE_DISPLACEMENT
                        last_dir = segment.direction

                    else:
                        print("error, not a valid turn", car.res[i - 1].direction, segment.direction)

        left_points.append((car_x, car_y))

        shapes_at_end = []
        # dots for the brake box
        shapes_at_end += [shapes.Rectangle(p[0], p[1], 6, 6, color=RED) for p in left_points]
        shapes_at_end += [shapes.Rectangle(p[0], p[1], 6, 6, color=BLACK) for p in right_points]

        # anchor point for crossing segments
        shapes_at_end += [shapes.Rectangle(p[0], p[1], 10, 10, color=RED) for p in interesting_points]

        # reserse right points
        right_points.reverse()
        # combine left and right points
        points = left_points + right_points
        # create lines from points
        line = GameDrawer.draw_lines(*[p for point in points for p in point], color=car.color, width=2)

        if debug:
            return line + shapes_at_end
        else:
            return line
        
    @classmethod
    def draw_test_results(cls, 
                          roads: List[Road],
                          test_params: None | Tuple[int, int, int, int] = None, 
                          test_results: None | List[Tuple[bool, str]] = None) -> text.Label:
        if test_params is None:
            test_params = find_greatest_gap(roads)

        if test_results is not None:
            return GameDrawer.draw_test_result_shape(test_results, *test_params)
        else:
            return text.Label("")

    @classmethod
    def draw_test_result_shape(cls, res, x, y, width, height) -> text.Label:
        """
        Creates a text result shape.

        Args:
            res (List[Tuple[bool, str]]): The test result.
            x (int): The x coordinate of the shape.
            y (int): The y coordinate of the shape.
            width (int): The width of the shape.
            height (int): The height of the shape.

        Returns:
            pyglet.text.Label: A pyglet text label representing the test result.
        """
        lines = [res[1] for res in res]

        font_size = 12

        while True:
            layout = text.Label(
                text='\n'.join(lines),
                font_name='Arial',
                font_size=font_size,
                x=x,
                y=y + height,
                width=width,
                height=height,
                multiline=True,
                anchor_x='left',
                anchor_y='top',
                color = BLACK_RGBA
            )
            if layout.content_height < height:
                break
            font_size -= 1

        return layout