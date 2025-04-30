from typing import Tuple

from game_model.game_model import TrafficEnv
from game_model.helper_functions import reservation_check
from game_model.road_network import LaneSegment, CrossingSegment, true_direction
from game_model.constants import MAX_ACC, MAX_DEC, LEFT_LANE_CHANGE, RIGHT_LANE_CHANGE, NO_LANE_CHANGE, \
    JUMP_TIME_STEPS, LANECHANGE_TIME_STEPS


class AstarCarController:
    def __init__(self, game: TrafficEnv, player: int) -> None:
        """
        Initialize the AstarCarController.

        Args:
            game (TrafficEnv): The game environment.
            player (int): The player index.
        """
        self.game = game
        self.player = player
        self.car = self.game.cars[player]
        self.goal = self.game.goals[player]
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
        max_possible_acc = min(self.get_accelerate(self.car.res), self.get_accelerate(self.car.parallel_res))
        if isinstance(self.car.res[0]["seg"], LaneSegment) \
                and max_possible_acc < MAX_ACC and len(self.car.res) == 1 \
                and self.car.res[0]["seg"] != self.game.goals[self.player].lane_segment \
                and not self.car.changing_lane:
            # try left lane
            left_lane = self.car.get_adjacent_lane_segment(1)
            if left_lane is not None:
                left_lane_acceleration = self.get_accelerate([{
                    "seg": left_lane,
                    "dir": self.car.direction,
                    "turn": False,
                    "begin": self.car.res[0]["begin"],
                    "end": self.car.res[0]["end"]
                }])
                if left_lane_acceleration > max_possible_acc:
                    lane_change = LEFT_LANE_CHANGE
                    max_possible_acc = left_lane_acceleration   
                
            # try right lane
            right_lane = self.car.get_adjacent_lane_segment(-1)
            if right_lane is not None:
                right_lane_acceleration = self.get_accelerate([{
                    "seg": right_lane,
                    "dir": self.car.direction,
                    "turn": False,
                    "begin": self.car.res[0]["begin"],
                    "end": self.car.res[0]["end"]
                }])
                if right_lane_acceleration >= max_possible_acc:
                    lane_change = RIGHT_LANE_CHANGE
                    max_possible_acc = right_lane_acceleration
        return max_possible_acc, lane_change

    def get_accelerate(self, segments: list[dict]) -> int:
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

        reserved_length = sum([abs(seg["end"] - seg["begin"]) for seg in segments])
        # limit max_acc to the max speed of the car
        max_acc,  = min(MAX_ACC, self.car.max_speed - self.car.speed), 
        max_dec = - max(abs(MAX_DEC), self.car.speed)

        # iterate over all acceleration values between max_acc and max_dec
        for acceleration in range(max_acc, max_dec - 1, -1):

            new_speed = self.car.speed + acceleration

            # check if car exceeds max speed of the current segment
            if self.car.speed + acceleration > min([seg["seg"].max_speed for seg in segments]):
                continue

            # check if car is changing lane
            if self.car.changing_lane:
                remaining_time = LANECHANGE_TIME_STEPS - (self.car.time - self.car.reserved_segment[0])
                required_space_in_segment = (self.car.speed + acceleration) * remaining_time
                remaining_space_in_segment = segments[-1]["seg"].length - segments[-1]["end"]
                if remaining_space_in_segment < required_space_in_segment:
                    continue

            added_segments = [segments[-1]]
            new_brk_dist = self.car.get_braking_distance(new_speed) + new_speed


            if new_brk_dist > reserved_length:
                potential_jump = new_brk_dist - reserved_length
                if potential_jump + abs(segments[-1]["end"]) >= segments[-1]["seg"].length:
                # potential_jump -= extended_segments[-1]["seg"].length
                    next_segments = self.car.get_next_segment(segments[-1])
                    if not next_segments:
                        print("NO next segments in get_accelerate - Bug?")
                        print(self.car.name)
                        return max_dec
                    
                    
                    for next_seg in next_segments[:-1]:
                        potential_jump -= next_seg.length
                        added_segments = added_segments + [{
                            "seg": next_seg,
                            "dir": self.car.direction,
                            "turn": False,
                            "begin": 0,
                            "end": next_seg.length
                        }]
                        # reserved_length += next_seg.length
                    added_segments = added_segments + [{
                        "seg": next_segments[-1],
                        "dir": self.car.direction,
                        "turn": False,
                        "begin": 0,
                        "end": (1 if true_direction[next_segments[-1].lane.direction] else -1) * 
                                max(self.car.size, potential_jump + self.car.size)
                    }]
                    # reserved_length += max(self.car.size, potential_jump)

            collision = False
            # Case 1: Enter a crossing
            if len(added_segments) > 1:
                
                for added_seg in added_segments:
                    seg = added_seg["seg"]
                    if isinstance(seg, CrossingSegment):
                        if len(seg.cars) > 0:
                            collision = True
                            break

            # Case 2: Extension within a lane segment
            last_seg = added_segments[-1]
            for other_car in last_seg["seg"].cars:
                if other_car != self.car:
                    other_car_seg_info = other_car.get_segment_info(last_seg["seg"])
                    end = abs(last_seg["end"])
                    o_begin = abs(other_car_seg_info["begin"])
                    o_end = abs(other_car_seg_info["end"])
                    if o_begin <= end <= o_end or o_end <= end <= o_begin:
                        collision = True
                        break

            # if no collision is detected return the acceleration
            if not collision:
                return acceleration
        
        return max_dec