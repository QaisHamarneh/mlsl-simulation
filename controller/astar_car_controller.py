from typing import Tuple

from game_model.game_model import TrafficEnv
from game_model.road_network import LaneSegment, CrossingSegment
from game_model.constants import max_acc_a, max_decc_b, LEFT_LANE_CHANGE, RIGHT_LANE_CHANGE, NO_LANE_CHANGE, \
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
        lane_change = NO_LANE_CHANGE
        acceleration = self.get_accelerate(self.car.res + self.car.parallel_res)
        if isinstance(self.car.res[0]["seg"], LaneSegment) \
                and acceleration < 1 and len(self.car.res) == 1 \
                and self.car.res[0]["seg"] != self.game.goals[self.player].lane_segment \
                and not self.car.changing_lane:
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
                if right_lane_acceleration >= acceleration:
                    lane_change = RIGHT_LANE_CHANGE
                else:
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
                        if left_lane_acceleration > acceleration:
                            lane_change = LEFT_LANE_CHANGE
        if lane_change == NO_LANE_CHANGE:
            lane_change = self.check_right_lane()
        return acceleration, lane_change

    def get_accelerate(self, segments: list[dict]) -> int:
        """
        Calculate the optimal acceleration for the car based on the given segments, the car's speed and other cars on the
        road. The value is limited by the car's maximum speed and the maximum acceleration and deceleration values.

        Args:
            segments (list[dict]): A list of segment dictionaries containing information about the segments.

        Returns:
            int: The optimal acceleration value
        """
        max_acc, max_deceleration = max_acc_a, - max_decc_b
        # limit max_acc to the max speed of the car
        max_acc = min(max_acc, self.car.max_speed - self.car.speed)
        # limit max_deceleration to 0
        max_deceleration = max(max_deceleration, -self.car.speed)

        extended_segments = segments
        max_jump = segments[-1]["end"] + JUMP_TIME_STEPS * (self.car.speed + max_acc)
        if max_jump > extended_segments[-1]["seg"].length:
            max_jump -= extended_segments[-1]["seg"].length
            next_segments = self.car.get_next_segment(extended_segments[-1])
            if not next_segments:
                print("NO next segments in get_accelerate - Bug?")
                print("min acceleration")
                print(self.car.name)
                return max_deceleration
            for next_seg in next_segments[:-1]:
                max_jump -= next_seg.length
                extended_segments = extended_segments + [{
                    "seg": next_seg,
                    "dir": self.car.direction,
                    "turn": False,
                    "begin": 0,
                    "end": next_seg.length
                }]
            extended_segments = extended_segments + [{
                "seg": next_segments[-1],
                "dir": self.car.direction,
                "turn": False,
                "begin": 0,
                "end": max(self.car.size, max_jump)
            }]

        # iterate over all acceleration values between max_acc and max_deceleration
        for acceleration in range(max_acc, max_deceleration - 1, -1):
            # check if car extends max speed of the current segment
            if self.car.speed + acceleration > self.car.res[0]["seg"].max_speed:
                continue

            # check if car is changing
            if self.car.changing_lane:
                remaining_time = LANECHANGE_TIME_STEPS - (self.car.time - self.car.reserved_segment[0])
                required_space_in_segment = (self.car.speed + acceleration) * remaining_time
                remaining_space_in_segment = segments[-1]["seg"].length - segments[-1]["end"]
                if remaining_space_in_segment < required_space_in_segment:
                    continue

            # for each segment in the extended segments
            collision = False
            for seg in extended_segments:
                priority = seg["seg"].cars.index(self.car) if self.car in seg["seg"].cars else len(seg["seg"].cars)
                match seg["seg"]:
                    case LaneSegment():
                        if priority > 0 and len(seg["seg"].cars) > 0:
                            for i in range(priority):
                                other_car = seg["seg"].cars[i]
                                other_car_seg_info = other_car.get_segment_info(seg["seg"])
                                end = abs(seg["end"])
                                o_begin = abs(other_car_seg_info["begin"])
                                o_end = abs(other_car_seg_info["end"])
                                if o_begin <= end <= o_end or o_end <= end <= o_begin:
                                    collision = True
                                    break
                                elif end + JUMP_TIME_STEPS * (self.car.speed + 1) < o_begin:
                                    collision = False
                                    break
                    case CrossingSegment():
                        if priority > 0 and len(seg["seg"].cars) > 0:
                            collision = True
                            break

            if collision:
                continue
        # if no collision is detected return the acceleration
            else:
                return acceleration
        return acceleration


    def check_right_lane(self) -> int:
        """
        Check if the car should change to the right lane.

        Returns:
            int: 1 if the car should change to the right lane, 0 otherwise.
        """
        if self.car.changing_lane:
            return 0
        if isinstance(self.car.res[0]["seg"], LaneSegment) and len(self.car.res) == 1:
            if self.goal.lane_segment == self.car.res[0]["seg"]:
                return 0

            right_lane = self.car.get_adjacent_lane_segment(1)
            if right_lane is not None:
                return 1
            else:
                return 0
        else:
            return 0
