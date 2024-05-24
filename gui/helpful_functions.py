from pyglet import shapes

from game_model.constants import *
from game_model.road_network import Direction, LaneSegment, CrossingSegment


def draw_dash_line(start, end, width=LANE_DISPLACEMENT, color=WHITE, dash=20):
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


def draw_arrow(begin, end, horizontal, direction, tip=BLOCK_SIZE // 4, width=LANE_DISPLACEMENT, color=WHITE):
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


def create_car_rect(car):
    return shapes.Rectangle(
        x=car.pos.x, y=car.pos.y,
        width=car.w, height=car.h,
        color=car.color if not car.dead else DEAD_GREY
    )


def create_lines(*line_coords, color, width=2):
    lines = []
    for i in range(0, len(line_coords) - 2, 2):
        lines.append(
            shapes.Line(line_coords[i], line_coords[i + 1], line_coords[i + 2], line_coords[i + 3], color=color,
                        width=width))
    return lines


def get_xy_crossingseg(seg):
    x = 0
    y = 0
    right = False
    down = False
    count_right = 0
    count_down = 0
    x_seg = seg
    y_seg = seg

    if seg.connected_segments[Direction.LEFT] is not None:
        right = True
        while not isinstance(x_seg, LaneSegment):
            count_right += 1
            x_seg = x_seg.connected_segments[Direction.LEFT]
        x = x_seg.begin
    elif seg.connected_segments[Direction.RIGHT] is not None:
        while not isinstance(x_seg, LaneSegment):
            count_right += 1
            x_seg = x_seg.connected_segments[Direction.RIGHT]
        x = x_seg.begin

    if seg.connected_segments[Direction.DOWN] is not None:
        down = True
        while not isinstance(y_seg, LaneSegment):
            count_down += 1
            y_seg = y_seg.connected_segments[Direction.DOWN]
        y = y_seg.begin
    elif seg.connected_segments[Direction.UP] is not None:
        while not isinstance(y_seg, LaneSegment):
            count_down += 1
            y_seg = y_seg.connected_segments[Direction.UP]
        y = y_seg.begin

    x = x + count_right * BLOCK_SIZE + (
            count_right - 1) * LANE_DISPLACEMENT if right else x - count_right * BLOCK_SIZE - (
            count_right - 1) * LANE_DISPLACEMENT
    y = y + count_down * BLOCK_SIZE + (
            count_down - 1) * LANE_DISPLACEMENT if down else y - count_down * BLOCK_SIZE - (
            count_down - 1) * LANE_DISPLACEMENT

    return x, y


def brake_box(car, debug):
    left_points = []
    right_points = []
    interesting_points = []
    (car_x, car_y) = car.pos.x, car.pos.y

    w = car.w if car.res[0]["dir"] == Direction.UP or car.res[0]["dir"] == Direction.DOWN else car.h

    # left back corner of car based on direction, append points as starting points for the brake box
    if car.res[0]["dir"] == Direction.RIGHT:
        car_y = car_y + car.h
        car_x2, car_y2 = (car_x, car_y - car.h)
    if car.res[0]["dir"] == Direction.DOWN:
        car_x = car_x + car.w
        car_y = car_y + car.h
        car_x2, car_y2 = (car_x - car.w, car_y)
    if car.res[0]["dir"] == Direction.LEFT:
        car_x = car_x + car.w
        car_x2, car_y2 = (car_x, car_y + car.h)
    if car.res[0]["dir"] == Direction.UP:
        car_x2, car_y2 = (car_x + car.w, car_y)

    left_points.append((car_x, car_y))
    right_points.append((car_x2, car_y2))

    remaining_distance = car.get_braking_distance()
    last_dir = car.res[0]["dir"]
    tip_dir = car.res[0]["dir"]

    for i in range(0, len(car.res)):
        segment = car.res[i]
        seg = segment["seg"]
        if isinstance(seg, LaneSegment):
            if seg.lane.road.horizontal:
                dis = abs(seg.end - car_x)
                if dis > remaining_distance:
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
            last_dir = segment["dir"]
            tip_dir = segment["dir"]


        elif isinstance(seg, CrossingSegment):
            if i == 0:
                x_anchor, y_anchor = get_xy_crossingseg(seg)
                interesting_points.append((x_anchor, y_anchor))

                if segment["dir"] == Direction.RIGHT:
                    dist = abs(car_x - (x_anchor + BLOCK_SIZE))
                    if dist > remaining_distance:
                        car_x = car_x + remaining_distance
                        car_x2 = car_x2 + remaining_distance
                    else:
                        car_x = x_anchor + BLOCK_SIZE
                        car_x2 = x_anchor + BLOCK_SIZE
                        remaining_distance -= dist

                elif segment["dir"] == Direction.LEFT:
                    dist = abs(car_x - (x_anchor - BLOCK_SIZE))
                    if dist > remaining_distance:
                        car_x = car_x - remaining_distance
                        car_x2 = car_x2 - remaining_distance
                    else:
                        car_x = x_anchor - BLOCK_SIZE
                        car_x2 = x_anchor - BLOCK_SIZE
                        remaining_distance -= dist

                elif segment["dir"] == Direction.UP:
                    dist = abs(car_y - (y_anchor + BLOCK_SIZE))
                    if dist > remaining_distance:
                        car_y = car_y + remaining_distance
                        car_y2 = car_y2 + remaining_distance
                    else:
                        car_y = y_anchor + BLOCK_SIZE
                        car_y2 = y_anchor + BLOCK_SIZE
                        remaining_distance -= dist

                elif segment["dir"] == Direction.DOWN:
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
                last_dir = segment["dir"]
            else:
                if last_dir.value == segment["dir"].value or remaining_distance < BLOCK_SIZE + LANE_DISPLACEMENT:

                    if remaining_distance > BLOCK_SIZE:
                        if segment["dir"] == Direction.RIGHT:
                            car_x += BLOCK_SIZE + LANE_DISPLACEMENT
                            car_x2 += BLOCK_SIZE + LANE_DISPLACEMENT
                        elif segment["dir"] == Direction.LEFT:
                            car_x -= BLOCK_SIZE + LANE_DISPLACEMENT
                            car_x2 -= BLOCK_SIZE + LANE_DISPLACEMENT
                        elif segment["dir"] == Direction.UP:
                            car_y += BLOCK_SIZE + LANE_DISPLACEMENT
                            car_y2 += BLOCK_SIZE + LANE_DISPLACEMENT
                        elif segment["dir"] == Direction.DOWN:
                            car_y -= BLOCK_SIZE + LANE_DISPLACEMENT
                            car_y2 -= BLOCK_SIZE + LANE_DISPLACEMENT

                        remaining_distance -= BLOCK_SIZE
                        remaining_distance -= LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                        right_points.append((car_x2, car_y2))
                        last_dir = segment["dir"]

                    else:

                        if car.res[i - 1]["dir"] == Direction.RIGHT:
                            car_x += remaining_distance
                            car_x2 += remaining_distance
                            tip_dir = Direction.RIGHT

                        elif car.res[i - 1]["dir"] == Direction.LEFT:
                            car_x -= remaining_distance
                            car_x2 -= remaining_distance
                            tip_dir = Direction.LEFT

                        elif car.res[i - 1]["dir"] == Direction.UP:
                            car_y += remaining_distance
                            car_y2 += remaining_distance
                            tip_dir = Direction.UP

                        elif car.res[i - 1]["dir"] == Direction.DOWN:
                            car_y -= remaining_distance
                            car_y2 -= remaining_distance
                            tip_dir = Direction.DOWN

                        remaining_distance = 0
                        left_points.append((car_x, car_y))
                        right_points.append((car_x2, car_y2))
                        last_dir = segment["dir"]

                elif car.res[i - 1]["dir"].value - segment["dir"].value == 1 or car.res[i - 1]["dir"].value - \
                        segment["dir"].value == -3:  # left turn

                    if car.res[i - 1]["dir"] == Direction.RIGHT:
                        car_x2 = car_x2 + BLOCK_SIZE + LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))
                        car_y2 = car_y2 + BLOCK_SIZE + LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))

                    if car.res[i - 1]["dir"] == Direction.DOWN:
                        car_y2 = car_y2 - BLOCK_SIZE - LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))
                        car_x2 = car_x2 + BLOCK_SIZE + LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))

                    if car.res[i - 1]["dir"] == Direction.LEFT:
                        car_x2 = car_x2 - BLOCK_SIZE - LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))
                        car_y2 = car_y2 - BLOCK_SIZE - LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))

                    if car.res[i - 1]["dir"] == Direction.UP:
                        car_y2 = car_y2 + BLOCK_SIZE + LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))
                        car_x2 = car_x2 - BLOCK_SIZE - LANE_DISPLACEMENT
                        right_points.append((car_x2, car_y2))

                    remaining_distance -= BLOCK_SIZE
                    remaining_distance -= LANE_DISPLACEMENT
                    last_dir = segment["dir"]

                elif car.res[i - 1]["dir"].value - segment["dir"].value == -1 or car.res[i - 1]["dir"].value - \
                        segment["dir"].value == +3:  # right turn
                    if car.res[i - 1]["dir"] == Direction.RIGHT:
                        car_x = car_x + BLOCK_SIZE + LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                        car_y = car_y - BLOCK_SIZE - LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                    if car.res[i - 1]["dir"] == Direction.DOWN:
                        car_y = car_y - BLOCK_SIZE - LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                        car_x = car_x - BLOCK_SIZE - LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                    if car.res[i - 1]["dir"] == Direction.LEFT:
                        car_x = car_x - BLOCK_SIZE - LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                        car_y = car_y + BLOCK_SIZE + LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                    if car.res[i - 1]["dir"] == Direction.UP:
                        car_y = car_y + BLOCK_SIZE + LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                        car_x = car_x + BLOCK_SIZE + LANE_DISPLACEMENT
                        left_points.append((car_x, car_y))
                    remaining_distance -= BLOCK_SIZE
                    remaining_distance -= LANE_DISPLACEMENT
                    last_dir = segment["dir"]

                else:
                    print("error, not a valid turn", car.res[i - 1]["dir"], segment["dir"])

    # add points for the brake box, the tip of the triangle
    last_dir = tip_dir

    if last_dir == Direction.RIGHT:
        car_x = car_x + w // 4
        car_y = car_y - w // 2

    if last_dir == Direction.LEFT:
        car_x = car_x - w // 4
        car_y = car_y + w // 2

    if last_dir == Direction.UP:
        car_x = car_x + w // 2
        car_y = car_y + w // 4

    if last_dir == Direction.DOWN:
        car_x = car_x - w // 2
        car_y = car_y - w // 4

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
    line = create_lines(*[p for point in points for p in point], color=car.color, width=2)

    if debug:
        return line + shapes_at_end
    else:
        return line
