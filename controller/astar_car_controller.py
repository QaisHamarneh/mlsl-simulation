import math
from typing import Tuple

from game_model.car import Car 
from game_model.helper_functions import reservation_check
from game_model.road_network import LaneSegment, CrossingSegment, SegmentInfo, Goal, true_direction
from game_model.constants import MAX_ACC, MAX_DEC, LANE_MAX_SPEED, CROSSING_MAX_SPEED, LEFT_LANE_CHANGE, \
      RIGHT_LANE_CHANGE, NO_LANE_CHANGE, JUMP_TIME_STEPS, LANECHANGE_TIME_STEPS


class AstarCarController:
    def __init__(self, car: Car, goal: Goal) -> None:
        """
        Initialize the AstarCarController.

        Args:
            game (TrafficEnv): The game environment.
            player (int): The player index.
        """
        self.car = car
        self.goal = goal
        self.first_go = True

    def get_action(self) -> Tuple[int, int]:
        """
        Determine the next action for the car.

        Returns:
            Tuple[int, int]: A tuple containing the acceleration and lane change values.
        """
        if self.first_go:
            self.first_go = False
            return 0, 0
        
        # safety check for changing lanes:
        if self.car.changing_lane:
            for car in self.car.reserved_segment[1].cars:

                if car != self and reservation_check(self.car):
                    self.car.changing_lane = False
                    self.car.reserved_segment = None
                    break
        
        lane_change = NO_LANE_CHANGE
        # This should be changed to check res and parallel_res separately.
        current_lane_acc = min(self.get_accelerate(self.car.res), self.get_accelerate(self.car.parallel_res))
        max_possible_acc = current_lane_acc
        if isinstance(self.car.res[0].segment, LaneSegment) \
                and max_possible_acc < MAX_ACC and len(self.car.res) == 1 \
                and self.car.res[0].segment != self.goal.lane_segment \
                and not self.car.changing_lane:
            # try left lane
            left_lane = self.car.get_adjacent_lane_segment(1)
            if left_lane is not None:
                left_segment = SegmentInfo(
                        left_lane,
                        self.car.res[0].begin,
                        self.car.res[0].end,
                        self.car.direction
                    )
                if not self.check_collision(left_segment):
                    left_lane_acceleration = self.get_accelerate([left_segment])
                    if left_lane_acceleration > max_possible_acc:
                        lane_change = LEFT_LANE_CHANGE
                        max_possible_acc = left_lane_acceleration
                
            # try right lane
            right_lane = self.car.get_adjacent_lane_segment(-1)
            if right_lane is not None:
                right_segment = SegmentInfo(
                        right_lane,
                        self.car.res[0].begin,
                        self.car.res[0].end,
                        self.car.direction
                    )
                if not self.check_collision(right_segment):
                    right_lane_acceleration = self.get_accelerate([right_segment])
                    if right_lane_acceleration >= max_possible_acc:
                        lane_change = RIGHT_LANE_CHANGE
                        max_possible_acc = right_lane_acceleration
        return min(max_possible_acc, max_possible_acc), lane_change

    def get_accelerate(self, segments: list[SegmentInfo]) -> int:
        """
        Calculate the optimal acceleration for the car based on the given segments, the car's speed and other cars on the
        road. The value is limited by the car's maximum speed and the maximum acceleration and deceleration values.

        Args:
            segments (list[dict]): A list of segment dictionaries containing information about the segments.

        Returns:
            int: The optimal acceleration value
        """
        if len(segments) == 0:
            return MAX_ACC

        reserved_length = sum([abs(seg_info.end - seg_info.begin) for seg_info in segments])
        upto_last_seg_reserved_length = reserved_length- abs(segments[-1].end - segments[-1].begin)
        # limit max_acc to the max speed of the car
        max_acc  = min(MAX_ACC, self.car.max_speed - self.car.speed)
        max_dec = - min(MAX_DEC, self.car.speed)

        # iterate over all acceleration values between max_acc and max_dec
        for acceleration in range(max_acc, max_dec - 1, -1):

            new_speed = self.car.speed + acceleration

            # check if car exceeds max speed of the current segment
            if self.car.speed + acceleration > min([seg_info.segment.max_speed for seg_info in segments]):
                continue

            # check if car is changing lane
            if self.car.changing_lane:
                remaining_time = LANECHANGE_TIME_STEPS - (self.car.time - self.car.reserved_segment[0])
                required_space_in_segment = (self.car.speed + acceleration) * remaining_time
                remaining_space_in_segment = segments[-1].segment.length - segments[-1].end
                if remaining_space_in_segment < required_space_in_segment:
                    continue

            added_segments = [segments[-1]]
            new_brk_dist = self.car.get_braking_distance(new_speed) + new_speed

            if new_brk_dist > reserved_length:
                potential_jump = new_brk_dist - reserved_length
                if potential_jump + abs(segments[-1].end) >= segments[-1].segment.length:
                # potential_jump -= extended_segments[-1].segment.length
                    next_segments = self.car.get_next_segment(segments[-1].segment)
                    if not next_segments:
                        print("NO next segments in get_accelerate - Bug?")
                        print(self.car.name)
                        print(segments[-1].segment)
                        return max_dec
                    
                    
                    for next_seg in next_segments[:-1]:
                        potential_jump -= next_seg.length
                        added_segments.append(
                            SegmentInfo(
                                next_seg,
                                0,
                                next_seg.length,
                                self.car.direction
                            ))
                        # reserved_length += next_seg.length
                    added_segments.append(
                        SegmentInfo(
                            next_segments[-1],
                            0,
                            (1 if true_direction[next_segments[-1].lane.direction] else -1) * 
                                max(self.car.size, potential_jump),
                                # max(self.car.size, potential_jump + self.car.size),
                            next_segments[-1].lane.direction
                        ))
                    # reserved_length += max(self.car.size, potential_jump)
            else:
                added_segments = [SegmentInfo(
                    segments[-1].segment,
                    segments[-1].begin,
                    # (1 if true_direction[segments[-1].direction] else -1) * new_brk_dist,
                    (1 if true_direction[segments[-1].direction] else -1) * \
                        max(self.car.size, (new_brk_dist - upto_last_seg_reserved_length + abs(segments[-1].begin))),
                    segments[-1].direction,
                    )]


            collision = False

            # Case 0: Already in a crossing
            for i, seg_info in enumerate(segments):
                seg = seg_info.segment
                if isinstance(seg, CrossingSegment):
                    if len(seg.cars) > 1:
                        # collision = True
                        # break
                        time_to_enter = \
                            math.ceil((sum([abs(seg_info.end - seg_info.begin) 
                                            for seg_info in segments[0:i]]) / max(new_speed, CROSSING_MAX_SPEED)))
                        for other_car in seg.cars[0:seg.cars.index(self.car)]:
                            if new_speed > other_car.speed:
                                collision = True
                                break
                            if  time_to_enter <= seg.time_to_leave[other_car]:
                                collision = True
                                break

            # Case 1: Enter a crossing
            if len(added_segments) > 1:
                distance_to_intersection = added_segments[0].segment.length - abs(added_segments[0].begin) + self.car.size
                for i, added_seg in enumerate(added_segments):
                    seg = added_seg.segment
                    if isinstance(seg, CrossingSegment):
                        if len(seg.cars) > 0:
                            # collision = True
                            # break
                            time_to_enter = \
                                math.ceil((sum([seg_info.segment.length
                                                for seg_info in added_segments[1:i]]) + distance_to_intersection) / max(new_speed, CROSSING_MAX_SPEED))
                            for other_car in seg.cars:
                                other_car_seg_info = next(seg_info for seg_info in other_car.res 
                                                        if seg_info.segment == seg)
                                if new_speed > other_car.speed or time_to_enter <= seg.time_to_leave[other_car] or other_car_seg_info.direction != added_seg.direction:
                                    collision = True
                                    break
                if not collision:
                    if isinstance(added_segments[1].segment, CrossingSegment):
                        intersection = added_segments[1].segment.intersection
                        for other_car, time in intersection.priority.items():
                            if other_car != self.car and time < intersection.priority[self.car]:
                                collision = True

            # Case 2: Extension within a lane segment
            if not collision:
                last_seg = added_segments[-1]
                for other_car in last_seg.segment.cars:
                    if other_car != self.car:
                        other_car_seg_info = next(seg_info for seg_info in other_car.res 
                                                  if seg_info.segment == last_seg.segment)
                        begin = abs(last_seg.begin)
                        end = abs(last_seg.end)
                        o_max_dec = - min(MAX_DEC, other_car.speed)
                        o_begin = abs(other_car_seg_info.begin) + other_car.speed - o_max_dec
                        o_end = abs(other_car_seg_info.end) + other_car.speed - o_max_dec
                        if o_begin <= begin <= o_end or o_end <= begin <= o_begin:
                            continue
                        if o_begin <= end <= o_end or o_end <= end <= o_begin:
                            collision = True
                            break

            # if no collision is detected return the acceleration
            if not collision:
                return acceleration
                            
        return max_dec
    
    def check_collision(self, seg_info: SegmentInfo):
        for other_car in seg_info.segment.cars:
            if other_car != self.car:
                other_car_seg_info = next(o_seg_info for o_seg_info in other_car.res if o_seg_info.segment == seg_info.segment)
                begin = abs(seg_info.begin)
                end = abs(seg_info.end)
                o_begin = abs(other_car_seg_info.begin)
                o_end = abs(other_car_seg_info.end)
                if self.getOverlap(min(begin, end), max(begin, end), 
                               min(o_begin, end), max(o_begin, o_end)) > 0: 
                    return True, other_car
        return None, None
    
    def getOverlap(self, begin_1, end_1, begin_2, end_2):
        return max(0, min(end_1, end_2) - max(begin_1, begin_2))