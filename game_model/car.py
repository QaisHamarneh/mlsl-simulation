from game_model.constants import *
from game_model.road_network import Color, LaneSegment, true_direction, Problem, CrossingSegment, Point, \
    horiz_direction, right_direction, Segment


class Car:
    def __init__(self,
                 name: str,
                 loc: int,
                 segment: LaneSegment,
                 speed: int,
                 size: int,
                 color: Color,
                 max_speed: int) -> None:

        self.reserved_segment = None
        self.changing_lane = None
        self.name = name
        self.speed = speed
        self.size = size
        self.color = color
        self.dead = False
        self.direction = segment.lane.direction
        self.loc = loc
        self.max_speed = max_speed
        self.claimed_lane: dict = {}
        self.parallel_res: list = []
        self.lane_change_counter: int = 0
        self.crossing_counter: int = 0
        self.time: int = 0

        self.claim: list = []
        self.res: list = [{"seg": segment,
                           "dir": self.direction,
                           "turn": False,
                           "begin": self.loc,
                           "end": (1 if true_direction[self.direction] else -1) * self.get_braking_distance()}]
        segment.cars.append(self)
        self.extend_res()
        self.last_segment = None
        self.changed_lane = False

        # For gui only
        self.pos = Point(0, 0)
        self.w = 0
        self.h = 0

        self._update_position()

    def move(self):
        # Within the lane
        self.loc += (1 if true_direction[self.res[0]["dir"]] else -1) * self.speed
        self.check_reservation()

        self.time += 1

        # Cancel claimed lanes if the car enters a crossing
        if len(self.res) > 1 and len(self.claimed_lane) > 0:
            self.claimed_lane = {}

        self.extend_res()

        while abs(self.loc) > self.res[0]["seg"].length:
            self.loc = (1 if true_direction[self.res[1]["dir"]] else -1) * (abs(self.loc) - self.res[0]["seg"].length)
            seg_info = self.res.pop(0)
            seg_info["seg"].cars.remove(self)
            if self.parallel_res:
                parallel_seg_info = self.parallel_res.pop(0)
                parallel_seg_info["seg"].cars.remove(self)
        if self.res[0]["turn"]:
            # self.loc = 0
            self.res[0]["turn"] = False
            if self.parallel_res:
                self.parallel_res[0]["turn"] = False

        self.res[0]["begin"] = self.loc
        if self.parallel_res:
            self.parallel_res[0]["begin"] = self.loc

        for i, seg in enumerate(self.res):
            if i < len(self.res) - 1:
                seg["end"] = (1 if true_direction[seg["dir"]] else -1) * seg["seg"].length
        for i, seg in enumerate(self.parallel_res):
            if i < len(self.parallel_res) - 1:
                seg["end"] = (1 if true_direction[seg["dir"]] else -1) * seg["seg"].length

        # Update the "end" of the last reserved segment
        end = self.get_braking_distance() - sum([abs(self.res[i]["end"] - self.res[i]["begin"]) for i in
                                                 range(len(self.res) - 1)])
        self.res[-1]["end"] = (1 if true_direction[self.res[-1]["dir"]] else -1) * end + self.res[-1]["begin"]
        if self.parallel_res:
            self.parallel_res[-1]["end"] = end + self.parallel_res[-1]["begin"]

        self._update_position()
        return True

    def get_next_segment(self, last_seg=None, direction=None) -> Segment:
        if last_seg is None:
            last_seg = self.res[-1]
        if direction is None:
            direction = self.res[-1]["dir"]

        if isinstance(last_seg["seg"], LaneSegment):
            return last_seg["seg"].end_crossing
        else:
            return last_seg["seg"].connected_segments[direction]

    def extend_res(self):
        while abs(self.loc) + self.get_braking_distance() >= sum([seg["seg"].length for seg in self.res]):
            next_seg = self.get_next_segment()
            parallel_next_seg = None
            if self.parallel_res:
                parallel_next_seg = self.get_next_segment(self.parallel_res[-1])
            if next_seg is None and parallel_next_seg is None:
                print("Problem.NO_NEXT_SEGMENT")
                print(f"Problem car {self.name} loc {self.loc} speed {self.speed}")
                for seg in self.res:
                    print(f"{seg['seg']} {seg['begin']} {seg['end']}")
                break
                # return Problem.NO_NEXT_SEGMENT
            else:
                extra = (1 if true_direction[self.direction] else -1) * (
                        abs(self.loc) + self.get_braking_distance() - sum([seg["seg"].length for seg in self.res]))
                next_seg_info = {"seg": next_seg,
                                 "dir": self.direction,
                                 "turn": False,
                                 "begin": 0,
                                 "end": extra}
                self.res.append(next_seg_info)
                next_seg.cars.append(self)
            if parallel_next_seg is not None:
                next_parallel_seg_info = {"seg": parallel_next_seg,
                                          "dir": self.direction,
                                          "turn": False,
                                          "begin": 0,
                                          "end": extra}
                self.parallel_res.append(next_parallel_seg_info)
                parallel_next_seg.cars.append(self)
        while isinstance(self.res[-1]["seg"], CrossingSegment):
            next_seg = self.get_next_segment()
            if next_seg is None:
                print("Problem.NO_NEXT_SEGMENT")
                break
            if isinstance(next_seg, CrossingSegment):
                next_seg_info = {"seg": next_seg,
                                    "dir": self.direction,
                                    "turn": False,
                                    "begin": 0,
                                    "end": 1 if true_direction[self.direction] else -1 * next_seg.length}
                self.res.append(next_seg_info)
                next_seg.cars.append(self)
            elif isinstance(next_seg, LaneSegment):
                next_seg_info = {"seg": next_seg,
                                 "dir": self.direction,
                                 "turn": False,
                                 "begin": 0,
                                 "end": (1 if true_direction[self.direction] else -1) * self.size}
                self.res.append(next_seg_info)
                next_seg.cars.append(self)

    def turn(self, new_direction):

        if isinstance(self.res[-1]["seg"], CrossingSegment):
            self.direction = new_direction
            self.res[-1]["dir"] = self.direction
            self.res[-1]["turn"] = True
            if self.parallel_res:
                self.parallel_res[-1]["turn"] = True
            return True
        if isinstance(self.res[-2]["seg"], CrossingSegment):
            self.direction = new_direction
            #remove the last segment
            seg = self.res.pop()
            seg["seg"].cars.remove(self)
            self.res[-1]["dir"] = self.direction
            self.res[-1]["turn"] = True
            if self.parallel_res:
                self.parallel_res[-1]["turn"] = True
            return True

    def change_speed(self, speed_diff):
        self.speed = max(min(self.speed + speed_diff, self.max_speed), 0)
        accumulated_res = 0
        i = 0
        for seg in self.res:
            accumulated_res += abs(seg["end"]) - abs(seg["begin"])
            i += 1
            if accumulated_res > self.get_braking_distance():
                break
        while len(self.res) > i:
            seg = self.res.pop(i)
            seg["seg"].cars.remove(self)
            if self.parallel_res:
                seg = self.parallel_res.pop(i)
                seg["seg"].cars.remove(self)
        return True

    def get_adjacent_lane_segment(self, lane_diff, lane_segment: LaneSegment = None) -> LaneSegment:
        if lane_segment is None:
            lane_segment = self.res[0]["seg"]
        actual_lane_diff = (-1 if right_direction[self.direction] else 1) * lane_diff
        num = lane_segment.lane.num
        lanes = lane_segment.lane.road.right_lanes if right_direction[self.direction] \
            else lane_segment.lane.road.left_lanes
        if 0 <= num + actual_lane_diff < len(lanes):
            current_seg_num = self.res[0]["seg"].num
            return lanes[num + actual_lane_diff].segments[current_seg_num]
        return None

    def change_lane(self, lane_diff):
        #case 1: car is not in a lane segment -> return problem
        if not (isinstance(self.res[0]["seg"], LaneSegment) and \
                len(self.res) == 1):
            return Problem.CHANGE_LANE_WHILE_CROSSING
        #case 2: car is not in lane segment in LANECHANGE time steps -> return problem
        if abs(self.loc) + self.get_braking_distance() + LANECHANGE_TIME_STEPS * self.speed > self.res[0]["seg"].length:
            return Problem.LANE_TOO_SHORT

        next_lane_seg = self.get_adjacent_lane_segment(lane_diff)

        #case 3: there is no adjacent lane segment -> return problem
        if next_lane_seg is None:
            return Problem.NO_ADJACENT_LANE

        self.changing_lane = True
        self.last_segment = (self.pos.x, self.pos.y)
        self.reserved_segment = (self.time, next_lane_seg)
        return True

    def check_reservation(self):
        if not self.changing_lane:
            return
        from game_model.helper_functions import reservation_check
        #check for collision in the new lane
        for car in self.reserved_segment[1].cars:

            if car != self and reservation_check(self):
                self.changing_lane = False
                self.reserved_segment = None
                return False

        if self.time - self.reserved_segment[0] == LANECHANGE_TIME_STEPS:
            self.changing_lane = False
            self.res[0]["seg"].cars.remove(self)
            self.res = [{"seg": self.reserved_segment[1],
                         "dir": self.res[0]["dir"],
                         "turn": False,
                         "begin": self.res[0]["begin"],
                         "end": self.res[0]["end"]}]
            self.res[0]["seg"].cars.append(self)
            self.extend_res()
            self._update_position()
            return True

    """
    def change_lane(self, lane_diff):
        if isinstance(self.res[0]["seg"], LaneSegment) and \
                len(self.res) == 1:
            next_lane_seg = self.get_adjacent_lane_segment(lane_diff)
            if next_lane_seg is not None:
                self.changed_lane = True
                self.last_segment = (self.pos.x, self.pos.y)
                self.res[0]["seg"].cars.remove(self)
                self.res[0] = {"seg": next_lane_seg,
                               "dir": self.res[0]["dir"],
                               "turn": False,
                               "begin": self.res[0]["begin"],
                               "end": self.res[0]["end"]}
                self.res[0]["seg"].cars.append(self)
                self._update_position()
                return True
            else:
                return Problem.NO_ADJACENT_LANE

        return Problem.CHANGE_LANE_WHILE_CROSSING
        # if isinstance(self.res[0]["seg"], LaneSegment) and self.loc + self.size <= self.res[0]["seg"].length:
        #     # Not yet claimed
        #     if len(self.claimed_lane) == 0 and self.lane_change_counter == 0:
        #         next_lane_seg = self.get_adjacent_lane_segment(lane_diff)
        #         if next_lane_seg is not None:
        #             self.claimed_lane = {"seg": next_lane_seg,
        #                                  "dir": next_lane_seg.lane.direction,
        #                                  "turn": False,
        #                                  "begin": self.res[0]["begin"],
        #                                  "end": self.res[0]["end"]}
        #         else:
        #             print("Problem.NO_ADJACENT_LANE")
        #             return Problem.NO_ADJACENT_LANE
        #
        #     # claimed, but not started to change lane
        #     elif len(self.claimed_lane) > 0:
        #         assert self.lane_change_counter == 0, f"Lane Change Counter = {self.lane_change_counter}"
        #         assert len(self.parallel_res) == 0, f"Claiming while para-res is not empty"
        #
        #         # Changing to a different lane
        #         if self.get_adjacent_lane_segment(lane_diff) != self.claimed_lane["seg"]:
        #             self.claimed_lane = {}
        #             return self.change_lane(lane_diff)
        #
        #         self.lane_change_counter += lane_diff
        #         self.parallel_res = [{}]
        #         for k, v in self.claimed_lane.items():
        #             self.parallel_res[0][k] = v
        #         self.claimed_lane = {}
        #
        #     # claimed, but not started to change lane
        #     elif self.parallel_res:
        #         assert len(self.claimed_lane) == 0, f"Changing lane started while still in claim"
        #         self.lane_change_counter += lane_diff
        #
        #         # Cancelled the lane change
        #         if self.lane_change_counter == 0:
        #             self.parallel_res = []
        #
        #         # Completed the lane change
        #         elif abs(self.lane_change_counter) == LANE_CHANGE_STEPS:
        #             self.res = []
        #             for seg in self.parallel_res:
        #                 self.res.append(seg)
        #             self.parallel_res = []
        #
        #     print(f"lane_diff = {lane_diff}")
        #     if self.claimed_lane:
        #         print(self.claimed_lane["seg"])
        #     print([seg["seg"] for seg in self.parallel_res])
        #     return True

        # return Problem.CHANGE_LANE_WHILE_CROSSING
    """

    def claim_lane(self, lane_diff):
        # check that only in one (lane) segment
        if len(self.res) == 1 and isinstance(self.res[0]["seg"], LaneSegment):
            # check that car is still only in one lane segment in CLAIMTIME time steps
            if self.loc + (1 if true_direction[self.direction] else -1) * self.speed * CLAIMTIME > self.res[0][
                "seg"].length:
                return

            next_lane_seg = self.get_adjacent_lane_segment(lane_diff)
            if next_lane_seg is not None:
                return
                #todo

    def _update_position(self):
        """ Returns the bottom left corner of the car """
        seg, direction = self.res[0]["seg"], self.res[0]["dir"]
        lane_seg = isinstance(seg, LaneSegment)
        road = seg.lane.road if lane_seg \
            else (seg.horiz_lane.road if horiz_direction[direction] else seg.vert_lane.road)

        if lane_seg:
            seg_begin = seg.begin
        if road.horizontal:
            if not lane_seg:
                seg_begin = seg.vert_lane.top if true_direction[direction] else seg.vert_lane.top + BLOCK_SIZE
            self.pos.y = seg.lane.top + self.lane_change_counter * (BLOCK_SIZE // LANE_CHANGE_STEPS) \
                if lane_seg else seg.horiz_lane.top
            self.pos.x = seg_begin + self.loc - (0 if true_direction[direction] else self.size)
            # BLOCK_SIZE // 6 for the triangle
            self.w = self.size - BLOCK_SIZE // 6
            self.h = BLOCK_SIZE
        else:
            if not lane_seg:
                seg_begin = seg.horiz_lane.top if true_direction[direction] else seg.horiz_lane.top + BLOCK_SIZE
            self.pos.x = seg.lane.top + self.lane_change_counter * (BLOCK_SIZE // LANE_CHANGE_STEPS) \
                if lane_seg else seg.vert_lane.top
            self.pos.y = seg_begin + self.loc - (0 if true_direction[direction] else self.size)
            # BLOCK_SIZE // 6 for the triangle
            self.w = BLOCK_SIZE
            self.h = self.size - BLOCK_SIZE // 6

    def return_updated_position(self, seg):
        """ Returns the bottom left corner of the car """
        seg, direction = seg, self.res[0]["dir"]
        road = seg.lane.road
        seg_begin = seg.begin
        if road.horizontal:
            y = seg.lane.top + self.lane_change_counter * (BLOCK_SIZE // LANE_CHANGE_STEPS)
            x = seg_begin + self.loc - (0 if true_direction[direction] else self.size)
            # BLOCK_SIZE // 6 for the triangle
            w = self.size - BLOCK_SIZE // 6
            h = BLOCK_SIZE
        else:
            x = seg.lane.top + self.lane_change_counter * (BLOCK_SIZE // LANE_CHANGE_STEPS)
            y = seg_begin + self.loc - (0 if true_direction[direction] else self.size)
            # BLOCK_SIZE // 6 for the triangle
            w = BLOCK_SIZE
            h = self.size - BLOCK_SIZE // 6
        return x, y, w, h

    def get_center(self):
        if horiz_direction[self.res[0]["dir"]]:
            return Point(self.pos.x + self.size // 2, self.pos.y + BLOCK_SIZE // 2)
        else:
            return Point(self.pos.x + BLOCK_SIZE // 2, self.pos.y + self.size // 2)

    def get_braking_distance(self, speed=None):
        if speed is None:
            speed = self.speed
        braking = (speed * (speed + 1)) // 2
        # BLOCK_SIZE // 2 additional distance when speed = 0
        return self.size + braking + BLOCK_SIZE // 2

    def get_segment_info(self, segment):
        for seg in self.res:
            if seg["seg"] == segment:
                return seg

    def get_size_segments(self):
        segments = []
        accumulated_size = 0
        i = 0
        while accumulated_size < self.size:
            seg_info = self.res[i]
            begin = abs(seg_info["begin"])
            end = abs(seg_info["end"])
            diff = end - begin
            remaining = min(diff, self.size - accumulated_size)
            segments.append({
                "seg": seg_info["seg"],
                "begin": seg_info["begin"],
                "end": seg_info["begin"] + (1 if true_direction[seg_info["dir"]] else -1) * remaining,
                "dir": seg_info["dir"]
            })
            accumulated_size += diff
            i += 1
        return segments
