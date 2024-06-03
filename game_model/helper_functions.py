import random
import string

import numpy as np

from game_model.constants import *
from game_model.car import Car
from game_model.road_network import Direction, Road, CrossingSegment, LaneSegment, true_direction, Goal, Segment
from gui.colors import colors


def dist(p1, p2):
    return np.linalg.norm([p1.x - p2.x, p1.y - p2.y])


def overlap(p1, w1, h1, p2, w2, h2):
    # If one rectangle is on left side of other
    if p1.x > p2.x + w2 or p2.x > p1.x + w1:
        return False

    # If one rectangle is above other
    if p1.y > p2.y + h2 or p2.y > p1.y + h1:
        return False

    return True


def reached_goal(car: Car, goal: Goal):
    if car.res[0]["seg"] == goal.lane_segment:
        if dist(car.get_center(), goal.pos) < car.size // 2 + BLOCK_SIZE // 2:
            return True
    return False


def create_random_car(segments: list[Segment], cars) -> Car:
    name = random.choice([color for color in colors.keys()
                          if not any([car.name == color for car in cars])])
    color = colors[name]

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


def create_segments(roads: list[Road]):
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


def collision_check(car: Car):
    for segment in car.get_size_segments():
        begin = abs(segment["begin"])
        end = abs(segment["end"])
        for other_car in segment["seg"].cars:
            if other_car != car:
                for other_seg in other_car.get_size_segments():
                    if other_seg["seg"] == segment["seg"]:
                        o_begin = abs(other_seg["begin"])
                        o_end = abs(other_seg["end"])
                        if begin < o_begin < end:
                            return True
                        elif begin < o_end < end:
                            return True

    return False