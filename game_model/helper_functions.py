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
    if car.res[0].segment == goal.lane_segment:
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
                color = colors[name]
        
    # name = random.choice([color for color in colors.keys()
    #                       if not any([car.name == color for car in cars])])
    # color = colors[name]

    lane_segment = random.choice([seg for seg in segments
                                  if isinstance(seg, LaneSegment) and
                                  not any([seg == car.res[0].segment for car in cars])])

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
        segment_car2 = next((seg for seg in car2_segments if segment_car1.segment == seg.segment), None)
        if segment_car2 is not None:
            begin1 = abs(segment_car1.begin)
            end1 = abs(segment_car1.end)
            begin2 = abs(segment_car2.begin)
            end2 = abs(segment_car2.end)

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
            o_begin = abs(other_seg[0].begin)
            o_end = o_begin + other_car.get_braking_distance()
            if o_begin <= car_loc <= o_end or o_begin <= car_loc + car.get_braking_distance() <= \
                    o_end or car_loc <= o_begin <= car_loc + car.get_braking_distance() or car_loc <= o_end <= car_loc + car.get_braking_distance():
                return True
    return False