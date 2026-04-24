import math
from typing import Tuple

from mlsl_simulation.game_model.car import Car 
from mlsl_simulation.game_model.road_network.road_network import Intersection, Segment, LaneSegment, CrossingSegment, SegmentInfo, Goal, \
    true_direction
from mlsl_simulation.game_model.constants import BUFFER, MAX_ACC, MAX_DEC, LANE_MAX_SPEED, CROSSING_MAX_SPEED, LEFT_LANE_CHANGE, \
      RIGHT_LANE_CHANGE, NO_LANE_CHANGE, JUMP_TIME_STEPS, LANECHANGE_TIME_STEPS
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement


class AstarCarController:
    def __init__(self, car: Car, cars:list[Car], reservation_management: ReservationManagement) -> None:
        """
        Initialize the AstarCarController.

        Args:
            game (TrafficEnv): The game environment.
            player (int): The player index.
        """
        self.car = car
        self.cars = cars
        self.first_go = True
        self.reservation_management: ReservationManagement = reservation_management

    def get_action(self) -> Tuple[int, int]:
        """
        Determine the next action for the car.

        Args:
            cars (list[car]): A list of all other cars in the game model.
        Returns:
            Tuple[int, int]: A tuple containing the acceleration and lane change values.
        """
        if self.first_go:
            self.first_go = False
            return 0, 0
        
        lane_change = NO_LANE_CHANGE
        reservations = self.reservation_management.get_car_reservations(self.car.id)

        # This should be changed to check res and parallel_res separately.
        max_possible_acc = self.get_accelerate(reservations)
        if self.car.changing_lane:
            lane_change_segment = self.reservation_management.get_reserved_lane_change_segment(self.car.id)
            if lane_change_segment is None:
                print(f"Issue 4: {self.car.name}")
            else:
                lane_change_segment_info = SegmentInfo(
                        lane_change_segment[1],
                        reservations[0].begin,
                        reservations[0].end,
                        self.car.direction
                    )
                max_possible_acc = min(self.get_accelerate(reservations), 
                                       self.get_accelerate([lane_change_segment_info]))

        elif max_possible_acc < MAX_ACC and len(reservations) == 1  \
                and isinstance(reservations[0].segment, LaneSegment) \
                and reservations[0].segment != self.car.goal.lane_segment:
            # try right lane
            right_lane_acceleration = MAX_DEC
            right_lane = self.car.get_adjacent_lane_segment(self.reservation_management, RIGHT_LANE_CHANGE)
            if right_lane is not None:
                right_segment = SegmentInfo(
                        right_lane,
                        reservations[0].begin,
                        reservations[0].end,
                        self.car.direction
                    )
                if not self._check_collision(right_segment):
                    right_lane_acceleration = self.get_accelerate([right_segment])
                    if right_lane_acceleration >= max_possible_acc:
                        lane_change = RIGHT_LANE_CHANGE
                
            if right_lane_acceleration < MAX_ACC:
                # try left lane
                left_lane = self.car.get_adjacent_lane_segment(self.reservation_management, LEFT_LANE_CHANGE)
                if left_lane is not None:
                    left_segment = SegmentInfo(
                            left_lane,
                            reservations[0].begin,
                            reservations[0].end,
                            self.car.direction
                        )
                    if not self._check_collision(left_segment):
                        left_lane_acceleration = self.get_accelerate([left_segment])
                        if left_lane_acceleration > max_possible_acc:
                            lane_change = LEFT_LANE_CHANGE
                        
        return max_possible_acc, lane_change

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
        max_acc  = min(MAX_ACC, self.car.max_speed - self.car.speed, min([seg_info.segment.max_speed for seg_info in segments]))
        max_dec = - min(MAX_DEC, self.car.speed)

        # iterate over all acceleration values between max_acc and max_dec
        for acceleration in range(max_acc, max_dec - 1, -1):

            new_speed = self.car.speed + acceleration

            # check if car is changing lane
            if self.car.changing_lane:
                lane_change_info = self.reservation_management.get_reserved_lane_change_segment(self.car.id)
                remaining_time = LANECHANGE_TIME_STEPS - (self.car.time - lane_change_info[0])
                required_space_in_segment = (self.car.speed + acceleration) * remaining_time
                remaining_space_in_segment = segments[-1].segment.length - segments[-1].end
                if remaining_space_in_segment < required_space_in_segment:
                    continue

            added_segments = [segments[-1]]
            new_brk_dist = self.car.get_braking_distance(new_speed) + new_speed

            if new_brk_dist > reserved_length:
                potential_jump = new_brk_dist - reserved_length
                if potential_jump + abs(segments[-1].end) >= segments[-1].segment.length:
                    next_segments = self.car.get_next_segment(self.reservation_management, segments[-1].segment)
                    if not next_segments:
                        print("NO next segments in get_accelerate - Bug?")
                        print(self.car.name)
                        print(segments[-1].segment)
                        return max_dec
                    
                    
                    for next_segment in next_segments[:-1]:
                        potential_jump -= next_segment.length
                        if isinstance(next_segment, CrossingSegment):
                            added_segments.append(
                                SegmentInfo(
                                    next_segment,
                                    0,
                                    next_segment.length,
                                    self.car.direction
                                ))
                    if isinstance(next_segments[-1], LaneSegment):
                        added_segments.append(
                            SegmentInfo(
                                next_segments[-1],
                                0,
                                (1 if true_direction[next_segments[-1].lane.direction] else -1) * 
                                    max(self.car.size + BUFFER, potential_jump),
                                    # max(self.car.size, potential_jump + self.car.size),
                                next_segments[-1].lane.direction
                            ))
            else:
                added_segments = [SegmentInfo(
                    segments[-1].segment,
                    segments[-1].begin,
                    (1 if true_direction[segments[-1].direction] else -1) * \
                        max(self.car.size + BUFFER, (new_brk_dist - upto_last_seg_reserved_length) + abs(segments[-1].begin)),
                    segments[-1].direction,
                    )]


            collision = False

            # Case 0: Already in a crossing
            for i, seg_info in enumerate(segments):
                seg: Segment = seg_info.segment
                if isinstance(seg, CrossingSegment):
                    cars_on_crossing_segment = self.reservation_management.get_cars_on_segment(seg)[0:self.reservation_management.get_cars_on_segment(seg).index(self.car.id)]
                    if len(cars_on_crossing_segment) > 0:
                        time_to_enter = math.ceil((sum([abs(proir_seg.end - proir_seg.begin) 
                                            for proir_seg in segments[0:i]]) / max(new_speed, CROSSING_MAX_SPEED)))
                        earlist_car = min(seg.crossing_segment_state.get_time_to_leave(other_car_id) for other_car_id in cars_on_crossing_segment[0:self.reservation_management.get_cars_on_segment(seg).index(self.car.id)])
                        if time_to_enter <= earlist_car:
                            collision = True
                            break
                        # for other_car_id in cars_on_crossing_segment[0:self.reservation_management.get_cars_on_segment(seg).index(self.car.id)]: 
                        #     other_car = [car for car in self.cars if car.id == other_car_id][0]
                        #     # if new_speed > other_car.speed:
                        #     #     collision = True
                        #     #     break
                        #     if time_to_enter <= seg.crossing_segment_state.get_time_to_leave(other_car_id):
                        #         collision = True
                        #         break
                if collision:
                    break
            if collision:
                break

            # Case 1: Enter a crossing
            if len(added_segments) > 1:
                for i, added_seg in enumerate(added_segments):
                    seg = added_seg.segment
                    if isinstance(seg, CrossingSegment):
                        cars_on_crossing_segment = self.reservation_management.get_cars_on_segment(seg)
                        if len(cars_on_crossing_segment) > 0:
                            # collision = True
                            # break
                            time_to_enter = \
                                math.ceil((sum([abs(proir_seg.end - proir_seg.begin) 
                                                for proir_seg in added_segments[0:i]]) / max(new_speed, CROSSING_MAX_SPEED)))
                            
                            earlist_car = min(seg.crossing_segment_state.get_time_to_leave(other_car_id) for other_car_id in cars_on_crossing_segment)
                            if time_to_enter <= earlist_car:
                                collision = True
                                break
                            # for other_car_id in cars_on_crossing_segment:
                            #     other_car = [car for car in self.cars if car.id == other_car_id][0]
                            #     # if new_speed > other_car.speed:
                            #     #     collision = True
                            #     #     break
                            #     if time_to_enter <= seg.crossing_segment_state.get_time_to_leave(other_car_id):
                            #         collision = True
                            #         break
                if collision:
                    break
                elif isinstance(added_segments[1].segment, CrossingSegment):
                    intersection: Intersection = added_segments[1].segment.intersection
                    for other_car_id, other_car_time in intersection.intersection_state.get_priority_items():
                        car_priority = intersection.intersection_state.get_car_priority(self.car.id)
                        if other_car_id != self.car.id and car_priority is not None and other_car_time < car_priority:
                            collision = True
                            break

            if collision:
                break
            # Case 2: Extension within a lane segment
            last_seg = added_segments[-1]
            for other_car_id in self.reservation_management.get_cars_on_segment(last_seg.segment):
                if other_car_id != self.car.id:
                    other_car_seg_info = next(seg_info for seg_info in self.reservation_management.get_car_reservations(other_car_id)
                                                if seg_info.segment == last_seg.segment)
                    begin = abs(last_seg.begin)
                    end = abs(last_seg.end)
                    other_car = [car for car in self.cars if car.id == other_car_id][0]
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
    
    def _check_collision(self, seg_info: SegmentInfo):
        for other_car_id in self.reservation_management.get_cars_on_segment(seg_info.segment):
            if other_car_id != self.car.id:
                other_car_seg_info = next(o_seg_info for o_seg_info in self.reservation_management.get_car_reservations(other_car_id) if o_seg_info.segment == seg_info.segment)
                begin = abs(seg_info.begin)
                end = abs(seg_info.end)
                o_begin = abs(other_car_seg_info.begin)
                o_end = abs(other_car_seg_info.end)
                if self.getOverlap(min(begin, end), max(begin, end), 
                               min(o_begin, end), max(o_begin, o_end)) > 0: 
                    return True
        return False
    
    def getOverlap(self, begin_1, end_1, begin_2, end_2):
        return max(0, min(end_1, end_2) - max(begin_1, begin_2))