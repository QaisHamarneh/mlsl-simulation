from controller.helper_functions import astar_heuristic, reconstruct_path
from game_model.game_model import TrafficEnv
from game_model.road_network import LaneSegment, CrossingSegment, Segment, true_direction


class AstarCarController:
    def __init__(self, game: TrafficEnv, player: int):
        self.game = game
        self.player = player

        self.car = self.game.cars[player]
        self.goal = self.game.goals[player]
        self.next_segments = []

    def get_action(self) -> int:
        dir_diff = 0
        lane_change = 0
        acceleration = self.get_accelerate(self.car.res + self.car.parallel_res)
        if isinstance(self.car.res[0]["seg"], LaneSegment) \
                and acceleration < 1 and len(self.car.res) == 1 \
                and self.car.res[0]["seg"] != self.game.goals[self.player].lane_segment:
            right_lane = self.car.get_adjacent_lane_segment(-1)
            if right_lane is not None:
                right_lane_acceleration = self.get_accelerate([{
                    "seg": right_lane,
                    "dir": self.car.direction,
                    "turn": False,
                    "begin": self.car.res[0]["begin"],
                    "end": self.car.res[0]["end"]
                }])
                if right_lane_acceleration > acceleration:
                    lane_change = -1
                else:
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
                            lane_change = 1
        action = acceleration
        if dir_diff > 0:
            action = dir_diff * 10 + action
        if lane_change > 0:
            action = lane_change * 100 + action
        return action

    def get_accelerate(self, segments):
        acceleration = 1
        extended_segments = segments
        max_jump = segments[-1]["end"] + 2 * (self.car.speed + 1)
        while max_jump > extended_segments[-1]["seg"].length:
            # if segments[-1]["end"] + 2 * (self.car.speed + 1) > segments[-1]["seg"].length:
            max_jump -= extended_segments[-1]["seg"].length
            next_seg = self.car.get_next_segment(extended_segments[-1])
            if next_seg is None:
                return -1
            extended_segments = extended_segments + [{
                    "seg": next_seg,
                    "dir": self.car.direction,
                    "turn": False,
                    "begin": 0,
                    "end": min(max_jump, next_seg.length)
            }]

        # seg = extended_segments[-1]
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
                            if o_begin <= end <= o_end:
                                return -1
                            elif end + 2 * (self.car.speed + 1) < o_begin:
                                acceleration = min(acceleration, 1)
                            elif end + 2 * self.car.speed < o_begin:
                                acceleration = 0
                case CrossingSegment():
                    if priority > 0 and len(seg["seg"].cars) > 0:
                        return -1
        return acceleration

    def check_right_lane(self):
        if self.car.changing_lane:
            return False
        if isinstance(self.car.res[0]["seg"], LaneSegment) and len(self.car.res) == 1:
            # check if goal is on this segment
            if self.goal.lane_segment == self.car.res[0]["seg"]:
                return False

            right_lane = self.car.get_adjacent_lane_segment(1)
            if right_lane is not None:
                self.car.change_lane(1)
                return True
        else:
            return False
