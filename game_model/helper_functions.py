import random
from typing import Optional, List

import numpy as np

from game_model.car import Car
from game_model.constants import *
from game_model.road_network import Direction, Road, true_direction, Goal, Point
from game_model.road_network import LaneSegment, CrossingSegment, Segment
from gui.selected_colors import selected_colors
from gui.colors import colors


def dist(p1: Point, p2: Point) -> float:
    """
    Calculate the Euclidean distance between two points.

    Args:
        p1 (Point): The first point.
        p2 (Point): The second point.

    Returns:
        float: The distance between the two points.
    """
    return np.linalg.norm([p1.x - p2.x, p1.y - p2.y])


def overlap(p1: Point, w1: int, h1: int, p2: Point, w2: int, h2: int) -> bool:
    """
    Check if two rectangles overlap.

    Args:
        p1 (Point): The top-left point of the first rectangle.
        w1 (int): The width of the first rectangle.
        h1 (int): The height of the first rectangle.
        p2 (Point): The top-left point of the second rectangle.
        w2 (int): The width of the second rectangle.
        h2 (int): The height of the second rectangle.

    Returns:
        bool: True if the rectangles overlap, False otherwise.
    """
    # If one rectangle is on left side of other
    if p1.x > p2.x + w2 or p2.x > p1.x + w1:
        return False

    # If one rectangle is above other
    if p1.y > p2.y + h2 or p2.y > p1.y + h1:
        return False

    return True


def reached_goal(car: Car, goal: Goal) -> bool:
    """
    Check if a car has reached its goal.

    Args:
        car (Car): The car to check.
        goal (Goal): The goal to check against.

    Returns:
        bool: True if the car has reached the goal, False otherwise.
    """
    if car.res[0]["seg"] == goal.lane_segment:
        if dist(car.get_center(), goal.pos) < car.size // 2 + BLOCK_SIZE // 2:
            return True
    return False


def create_random_car(segments: List[Segment], cars: List[Car]) -> Car:
    """
    Create a random car that does not overlap with existing cars.
    Randomly selects a color, lane segment, speed, size. The location is set to 0.

    Args:
        segments (List[Segment]): The list of segments to place the car in.
        cars (List[Car]): The list of existing cars.

    Returns:
        Car: The randomly created car.
    """
    name = ""
    color = (0, 0, 0)
    for c in selected_colors:
        if not any([car.name == c for car in cars]):
            name = c
            color = selected_colors[name]
    if name == "":
        for c in colors:
            if not any([car.name == c for car in cars]):
                name = c
                color = selected_colors[name]
        
    # name = random.choice([color for color in colors.keys()
    #                       if not any([car.name == color for car in cars])])
    # color = colors[name]

    lane_segment = random.choice([seg for seg in segments
                                  if isinstance(seg, LaneSegment) and
                                  not any([seg == car.res[0]["seg"] for car in cars])])

    max_speed = random.randint(BLOCK_SIZE // 4, BLOCK_SIZE // 3)
    speed = random.randint(BLOCK_SIZE // 10, max_speed)

    size = random.randint(BLOCK_SIZE // 2, 3 * BLOCK_SIZE // 2)
    loc = 0

    return Car(name=name,
               loc=loc,
               segment=lane_segment,
               speed=speed,
               size=size,
               color=color,
               max_speed=max_speed)


def create_segments(roads: List[Road]) -> Optional[List[Segment]]:
    """
    Create segments for the given roads.

    Args:
        roads (List[Road]): The list of roads to create segments for.

    Returns:
        Optional[List[Segment]]: The list of created segments, or None if there was an overlap.
    """
    roads.sort(key=lambda r: r.top)
    segments = []
    last_horiz = 0
    for horiz_road in roads:
        if horiz_road.horizontal:
            if last_horiz > horiz_road.top:
                print(f"\nRoad {horiz_road.name} overlaps with the previous road")
                return None
            last_vert = 0
            for vert_road in roads:
                if not vert_road.horizontal:
                    if last_vert > vert_road.top:
                        print(f"\nRoad {vert_road.name} {vert_road.top} overlaps with previous road {last_vert}")
                        return None

                    # Starting with lanes:
                    for horiz_lane in horiz_road.right_lanes + horiz_road.left_lanes:
                        # There horizontal exist a lane segment:
                        for vert_lane in vert_road.right_lanes + vert_road.left_lanes:
                            horiz_lane_segment = None
                            vert_lane_segment = None
                            if vert_road.top > last_vert and \
                                    (vert_lane.num == 0 and
                                     (vert_lane.direction == Direction.DOWN or len(vert_road.right_lanes) == 0)):
                                horiz_lane_segment = LaneSegment(horiz_lane, last_vert, vert_road.top) \
                                    if true_direction[horiz_lane.direction] \
                                    else LaneSegment(horiz_lane, vert_road.top, last_vert)
                            if horiz_road.top > last_horiz and \
                                    (horiz_lane.num == 0 and
                                     (horiz_lane.direction == Direction.RIGHT or len(horiz_road.right_lanes) == 0)):
                                vert_lane_segment = LaneSegment(vert_lane, last_horiz, horiz_road.top) \
                                    if true_direction[vert_lane.direction] \
                                    else LaneSegment(vert_lane, horiz_road.top, last_horiz)

                            if horiz_lane_segment is not None:
                                horiz_lane.segments.append(horiz_lane_segment)
                                horiz_lane_segment.num = len(horiz_lane.segments) - 1
                                segments.append(horiz_lane_segment)
                            if vert_lane_segment is not None:
                                vert_lane.segments.append(vert_lane_segment)
                                vert_lane_segment.num = len(vert_lane.segments) - 1
                                segments.append(vert_lane_segment)

                            crossing_segment = CrossingSegment(horiz_lane, vert_lane)
                            horiz_lane.segments.append(crossing_segment)
                            vert_lane.segments.append(crossing_segment)
                            crossing_segment.horiz_num = len(horiz_lane.segments) - 1
                            crossing_segment.vert_num = len(vert_lane.segments) - 1
                            segments.append(crossing_segment)

                    last_vert = vert_road.bottom

            last_horiz = horiz_road.bottom

    for road in roads:
        for lane in road.right_lanes + road.left_lanes:
            if true_direction[lane.direction]:
                for i in range(len(lane.segments) - 1):
                    match lane.segments[i]:
                        case LaneSegment():
                            lane.segments[i].end_crossing = lane.segments[i + 1]
                        case CrossingSegment():
                            if lane.direction == Direction.RIGHT:
                                lane.segments[i].connected_segments[Direction.RIGHT] = lane.segments[i + 1]
                                # if isinstance(lane.segments[i + 1], CrossingSegment):
                                #     lane.segments[i + 1].left = lane.segments[i]
                            elif lane.direction == Direction.UP:
                                lane.segments[i].connected_segments[Direction.UP] = lane.segments[i + 1]
                                # if isinstance(lane.segments[i + 1], CrossingSegment):
                                #     lane.segments[i + 1].down = lane.segments[i]
            else:
                for j in range(1, len(lane.segments)):
                    match lane.segments[j]:
                        case LaneSegment():
                            lane.segments[j].end_crossing = lane.segments[j - 1]
                        case CrossingSegment():
                            if lane.direction == Direction.LEFT:
                                lane.segments[j].connected_segments[Direction.LEFT] = lane.segments[j - 1]
                                # if isinstance(lane.segments[j - 1], CrossingSegment):
                                #     lane.segments[j - 1].right = lane.segments[j]
                            elif lane.direction == Direction.DOWN:
                                lane.segments[j].connected_segments[Direction.DOWN] = lane.segments[j - 1]
                                # if isinstance(lane.segments[j - 1], CrossingSegment):
                                #     lane.segments[j - 1].up = lane.segments[j]

    return segments


def collision_check(car1: Car, car2:Car) -> bool:
    """
    Check if a car is in collision with any other car.

    Args:
        car (Car): The car to check.

    Returns:
        bool: True if there is a collision, False otherwise.
    """
    car1_segments = car1.get_size_segments()
    car2_segments = car2.get_size_segments()
    for segment_car1 in car1_segments:
        if segment_car1["seg"] in [seg["seg"] for seg in car2_segments]:
            begin1 = abs(segment_car1["begin"])
            end1 = abs(segment_car1["end"])
            segment_car2 = next(seg for seg in car2_segments if segment_car1["seg"] == seg["seg"])
            begin2 = abs(segment_car2["begin"])
            end2 = abs(segment_car2["end"])

            if begin2 < begin1 < end2:
                return True
            elif begin2 < end1 < end2:
                return True
            
            elif begin1 < begin2 < end1:
                return True
            elif begin1 < end2 < end1:
                return True

    return False


def reservation_check(car: Car) -> bool:
    """
    Check if a car's reservation overlaps with any other car's reservation.

    Args:
        car (Car): The car to check.

    Returns:
        bool: True if there is an overlap, False otherwise.
    """
    seg = car.reserved_segment[1]
    car_loc = abs(car.loc)
    for other_car in seg.cars:
        if other_car != car:
            other_seg = other_car.get_size_segments()
            o_begin = abs(other_seg[0]["begin"])
            o_end = o_begin + other_car.get_braking_distance()
            if o_begin <= car_loc <= o_end or o_begin <= car_loc + car.get_braking_distance() <= \
                    o_end or car_loc <= o_begin <= car_loc + car.get_braking_distance() or car_loc <= o_end <= car_loc + car.get_braking_distance():
                return True
    return False



