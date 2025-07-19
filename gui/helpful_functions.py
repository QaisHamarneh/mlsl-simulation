import pyglet
from pyglet import shapes

from game_model.constants import *
from game_model.road_network import Direction, Road, LaneSegment, CrossingSegment, true_direction
from game_model.car import Car
from typing import List, Tuple, Union

from gui.map_colors import *


def get_xy_crossingseg(seg: CrossingSegment) -> Tuple[int, int]:
    """
    Gets the x and y coordinates of a crossing segment, using the connected segments to a lane segment.

    Args:
        seg (CrossingSegment): The crossing segment.

    Returns:
        Tuple[int, int]: The x and y coordinates of the crossing segment.
    """
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


def find_greatest_gap(roads: List[Road]) -> Tuple[int, int, int, int]:
    """
    Finds the greatest gap between two roads. Iterate over all roads and find the greatest gap between two roads,
    returning the x,y coordinates of the top left corner and the width and height of the gap.

    Args:
        roads (List[Road]): A list of roads, with top and bottom parameters.

    Returns:
        Tuple[int, int, int, int]: The x,y coordinates of the top left corner and the width and height of the gap.
    """
    # Find the greatest gap between two roads, differentiating between horizontal and vertical roads
    if len(roads) == 0:
        return 0, 0, 0, 0

    # seperate horizontal and vertical roads

    horizontal_roads = [road for road in roads if road.horizontal]
    vertical_roads = [road for road in roads if not road.horizontal]

    # sort roads by their top value

    horizontal_roads.sort(key=lambda road: road.top)
    vertical_roads.sort(key=lambda road: road.top)

    # calculate the gap between each road (compare last.bottom with next.top)

    horizontal_gaps = [horizontal_roads[i + 1].top - horizontal_roads[i].bottom for i in
                       range(len(horizontal_roads) - 1)]
    vertical_gaps = [vertical_roads[i + 1].top - vertical_roads[i].bottom for i in range(len(vertical_roads) - 1)]

    # find the largest gap

    max_horizontal_gap = max(horizontal_gaps) if len(horizontal_gaps) > 0 else 0
    max_vertical_gap = max(vertical_gaps) if len(vertical_gaps) > 0 else 0

    # find the top left corner of the gap

    vertical_index = vertical_gaps.index(max_vertical_gap) if len(vertical_gaps) > 0 else 0
    horizontal_index = horizontal_gaps.index(max_horizontal_gap) if len(horizontal_gaps) > 0 else 0

    x = vertical_roads[vertical_index].bottom
    y = horizontal_roads[horizontal_index].bottom

    return x, y, max_vertical_gap, max_horizontal_gap


def return_updated_position(car: Car) -> tuple[int, int, int, int]:
    """
    Return the updated position of the car.

    Args:
        seg (Segment): The segment the car is on.

    Returns:
        tuple[int, int, int, int]: The updated position (x, y, w, h) of the car.
    """
    """ Returns the bottom left corner of the car """
    direction = car.res[0].direction
    seg = car.reserved_segment[1]
    road = seg.lane.road
    seg_begin = seg.begin
    if road.horizontal:
        y = seg.lane.top + car.lane_change_counter * (BLOCK_SIZE // LANE_CHANGE_STEPS)
        x = seg_begin + car.loc - (0 if true_direction[direction] else car.size)
        # BLOCK_SIZE // 6 for the triangle
        w = car.size - BLOCK_SIZE // 6
        h = BLOCK_SIZE
    else:
        x = seg.lane.top + car.lane_change_counter * (BLOCK_SIZE // LANE_CHANGE_STEPS)
        y = seg_begin + car.loc - (0 if true_direction[direction] else car.size)
        # BLOCK_SIZE // 6 for the triangle
        w = BLOCK_SIZE
        h = car.size - BLOCK_SIZE // 6
    return x, y, w, h