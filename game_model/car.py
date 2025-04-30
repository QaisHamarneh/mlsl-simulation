import numpy as np

from game_model.constants import *
from game_model.road_network import Color, LaneSegment, true_direction, Problem, CrossingSegment, Point, \
    horiz_direction, right_direction, Segment
from typing import Optional, List, Dict


class Car:
    def __init__(self,
                 name: str,
                 loc: int,
                 segment: LaneSegment,
                 speed: int,
                 size: int,
                 color: Color,
                 max_speed: int) -> None:
        """
        Initialize a Car object.

        Args:
            name (str): The name of the car.
            loc (int): The initial location of the car.
            segment (LaneSegment): The initial lane segment the car is on.
            speed (int): The initial speed of the car.
            size (int): The size of the car.
            color (Color): The color of the car.
            max_speed (int): The maximum speed of the car.
        """
        self.reserved_segment = None
        self.changing_lane = None
        self.name = name
        self.speed = speed
        self.size = size
        self.color = color
        self.dead = False
        self.goal = None
        self.second_goal = None
        self.direction = segment.lane.direction
        self.loc = loc
        self.max_speed = max_speed
        self.claimed_lane: dict = {}
        self.parallel_res: list = []
        self.lane_change_counter: int = 0
        self.crossing_counter: int = 0
        self.time: int = 0
        self.stagnation: int = 0
        self.last_loc: Point = loc

        self.res: list = [{"seg": segment,
                           "dir": self.direction,
                           "turn": False,
                           "begin": self.loc,
                           "end": (1 if true_direction[self.direction] else -1) * self.get_braking_distance()}]
        segment.cars.append(self)
        self.extend_res()

        # For gui only
        self.pos = Point(0, 0)
        self.w = 0
        self.h = 0

        self._update_position()

    @property
    def dead(self):
        return self._dead
    
    @dead.setter
    def dead(self, _dead: bool):
        if _dead:
            index = len(self.get_size_segments())
            while index < len(self.res):
                self.res[index]["seg"].cars.remove(self)
                self.res.remove(self.res[index])
                index += 1

            self.speed = 0

        self._dead = _dead

    def move(self) -> bool:
        """
        Move the car within its lane and handle lane changes and reservations.

        Returns:
            bool: True if the car moved successfully, False otherwise.
        """
        if self.dead:
            return False

        # Within the lane
        self.loc += (1 if true_direction[self.res[0]["dir"]] else -1) * self.speed
        self.check_reservation()

        self.time += 1

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

    def get_next_segment(self, last_seg: dict = None) -> List[Segment]:
        """
        Get the next segment for the car to move to.

        Args:
            last_seg (dict, optional): The last segment the car was on. Defaults to None.
            direction (int, optional): The direction the car is moving. Defaults to None.

        Returns:
             List[Segment]: The next segments for the car to move to, up to the next Lanesegment
        """
        if last_seg is None:
            last_seg = self.res[-1]
        # if direction is None:
        #     direction = self.res[-1]["dir"]

        if self.res[0]["seg"] == self.goal.lane_segment:
            #case 1: cur seg == goal seg -> preplan path to second goal
            # segs = self.astar()
            segs = self.astar(goal=self.second_goal)

        else:
            #case 2: cur seg != goal seg -> plan path to first goal(e.g. for alternative lanes (right, left)
            segs = self.astar(last_seg["seg"])
        


        if len(segs) == 0:
            print("Astar Error: No segments found by the astar function.")

        if len(segs) == 1:
            return segs

        i = 1

        for i in range(1, len(segs)):
            if isinstance(segs[i], LaneSegment):
                return segs[0:i + 1]

        return []



    def extend_res(self) -> None:
        """
        Extend the reservation of the car to the next segments.
        """
        next_segs = None
        while self.goal is not None and (
                abs(self.loc) + self.get_braking_distance() >= sum([seg["seg"].length for seg in self.res]) or
                isinstance(self.res[-1]["seg"], CrossingSegment)):
            if next_segs is None:
                next_segs = self.astar()
            if len(next_segs) < 2:
                next_segs = self.astar(goal=self.second_goal)
            if len(next_segs) < 2:
                print(Problem.NO_NEXT_SEGMENT)
                print(f"Problem car {self.name} loc {self.loc} speed {self.speed}")
                for seg in self.res:
                    print(f"{seg['seg']} {seg['begin']} {seg['end']}")
                break

            next_seg = next_segs.pop(1)

            parallel_next_seg = None

            # if self.parallel_res:
            #    parallel_next_seg = self.get_next_segment(self.parallel_res[-1])

            if next_seg is None and parallel_next_seg is None:
                #check if car is on the goal segment
                if self.goal.lane_segment != self.res[-1]["seg"]:
                    print(Problem.NO_NEXT_SEGMENT)
                    print(f"Problem car {self.name} loc {self.loc} speed {self.speed}")
                    for seg in self.res:
                        print(f"{seg['seg']} {seg['begin']} {seg['end']}")
                    break
            else:
                extra = (1 if true_direction[self.direction] else -1) * (
                        abs(self.loc) + self.get_braking_distance() - sum([seg["seg"].length for seg in self.res]))
                next_dir = None
                if isinstance(next_seg, LaneSegment):
                    next_dir = next_seg.lane.direction
                elif isinstance(next_seg, CrossingSegment):
                    next_next_seg = next_segs[1] if next_segs else None
                    if next_next_seg is None:
                        print(Problem.NO_NEXT_SEGMENT)
                    if isinstance(next_next_seg, LaneSegment):
                        next_dir = next_next_seg.lane.direction
                    else:
                        for k, v in next_seg.connected_segments.items():
                            if v == next_next_seg:
                                next_dir = k
                                break
                next_seg_info = {"seg": next_seg,
                                 "dir": next_dir,
                                 "turn": next_dir != self.res[-1]["dir"],
                                 "begin": 0,
                                 "end": extra if isinstance(next_seg, LaneSegment) else 1 * BLOCK_SIZE}
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

    def turn(self, new_direction: int) -> bool:
        """
        Turn the car to a new direction.

        Args:
            new_direction (int): The new direction to turn the car.

        Returns:
            bool: True if the car turned successfully, False otherwise.
        """

        if isinstance(self.res[-1]["seg"], CrossingSegment):
            self.direction = new_direction
            self.res[-1]["dir"] = self.direction
            self.res[-1]["turn"] = True
            if self.parallel_res:
                self.parallel_res[-1]["turn"] = True
            return True

    def change_speed(self, speed_diff: int) -> bool:
        """
        Change the speed of the car.

        Args:
            speed_diff (int): The difference in speed to apply.

        Returns:
            bool: True if the speed was changed successfully, False otherwise.
        """
        self.speed = max(min(self.speed + speed_diff, self.max_speed), 0)
        # accumulated_res = 0
        # i = 0
        # for seg in self.res:
        #     accumulated_res += abs(seg["end"]) - abs(seg["begin"])
        #     i += 1
        #     if accumulated_res > self.get_braking_distance():
        #         break
        # while len(self.res) > i:
        #     seg = self.res.pop(i)
        #     seg["seg"].cars.remove(self)
        #     if self.parallel_res:
        #         seg = self.parallel_res.pop(i)
        #         seg["seg"].cars.remove(self)
        return True

    def get_adjacent_lane_segment(self, lane_diff: int, lane_segment: LaneSegment = None) -> LaneSegment:
        """
        Get the adjacent lane segment.

        Args:
            lane_diff (int): The difference in lane number.
            lane_segment (LaneSegment, optional): The current lane segment. Defaults to using the first lane segment in the reservation.

        Returns:
            LaneSegment: The adjacent lane segment.
        """
        if lane_segment is None:
            lane_segment = self.res[0]["seg"]
        actual_lane_diff = (-1 if right_direction[self.direction] else 1) * lane_diff
        num = lane_segment.lane.num
        lanes = lane_segment.lane.road.right_lanes if right_direction[self.direction] \
            else lane_segment.lane.road.left_lanes
        if 0 <= num + actual_lane_diff < len(lanes):
            current_seg_num = self.res[0]["seg"].num
            if self.res[0]["dir"] != lanes[num + actual_lane_diff].direction:
                return None
            return lanes[num + actual_lane_diff].segments[current_seg_num]
        return None

    def change_lane(self, lane_diff: int) -> bool:
        """
        Change the lane of the car.

        Args:
            lane_diff (int): The difference in lane number.

        Returns:
            bool: True if the lane was changed successfully, False otherwise.
        """
        # case 1: car is not in a lane segment -> return problem
        if not (isinstance(self.res[0]["seg"], LaneSegment) and \
                len(self.res) == 1):
            return Problem.CHANGE_LANE_WHILE_CROSSING
        # case 2: car is not in lane segment in LANECHANGE time steps -> return problem
        if abs(self.loc) + self.get_braking_distance() + LANECHANGE_TIME_STEPS * self.speed > self.res[0]["seg"].length:
            return False

        if lane_diff == 0:
            return False

        next_lane_seg = self.get_adjacent_lane_segment(lane_diff)

        # case 3: there is no adjacent lane segment -> return problem
        if next_lane_seg is None:
            return Problem.NO_ADJACENT_LANE

        self.changing_lane = True
        self.last_segment = (self.pos.x, self.pos.y)
        self.reserved_segment = (self.time, next_lane_seg)
        return True

    def check_reservation(self) -> bool:
        """
        Check the reservation for lane change.

        Returns:
            bool: True if the reservation is valid, False otherwise.
        """
        if not self.changing_lane:
            return

        if self.time - self.reserved_segment[0] == LANECHANGE_TIME_STEPS:
            self.changing_lane = False
            for seg in self.res:
                seg["seg"].cars.remove(self)
            self.res = [{"seg": self.reserved_segment[1],
                         "dir": self.res[0]["dir"],
                         "turn": False,
                         "begin": self.res[0]["begin"],
                         "end": self.res[0]["end"]}]
            self.res[0]["seg"].cars.append(self)
            self.extend_res()
            self._update_position()
            return True

        if self.time - self.reserved_segment[0] > LANECHANGE_TIME_STEPS:
            self.changing_lane = False
            self.reserved_segment = None
            return False

    def claim_lane(self, lane_diff: int) -> None:
        """
        Claim the adjacent lane segment.

        Args:
            lane_diff (int): The difference in lane number.
        """
        # check that only in one (lane) segment
        if len(self.res) == 1 and isinstance(self.res[0]["seg"], LaneSegment):
            # check that car is still only in one lane segment in CLAIMTIME time steps
            if self.loc + (1 if true_direction[self.direction] else -1) * self.speed * CLAIMTIME > self.res[0][
                "seg"].length:
                return

            next_lane_seg = self.get_adjacent_lane_segment(lane_diff)
            if next_lane_seg is not None:
                return
                # todo

    def _update_position(self) -> None:
        """
        Update the position of the car, based on the current lane segment, location, direction and speed.
        """
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

    def return_updated_position(self, seg: Segment) -> tuple[int, int, int, int]:
        """
        Return the updated position of the car.

        Args:
            seg (Segment): The segment the car is on.

        Returns:
            tuple[int, int, int, int]: The updated position (x, y, w, h) of the car.
        """
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

    def get_center(self) -> Point:
        """
        Get the center point of the car.

        Returns:
            Point: The center point of the car.
        """
        if horiz_direction[self.res[0]["dir"]]:
            return Point(self.pos.x + self.size // 2, self.pos.y + BLOCK_SIZE // 2)
        else:
            return Point(self.pos.x + BLOCK_SIZE // 2, self.pos.y + self.size // 2)

    def get_braking_distance(self, speed: int = None) -> int:
        """
        Get the braking distance of the car.

        Args:
            speed (int, optional): The speed of the car. Defaults to None.

        Returns:
            int: The braking distance of the car.
        """
        if self.dead:
            return self.speed

        if speed is None:
            speed = self.speed
        braking = speed**2  // (2 * MAX_DEC)
        # BLOCK_SIZE // 2 additional distance when speed = 0
        return self.size + braking + BUFFER

    def get_segment_info(self, segment: Segment) -> dict:
        """
        Get the information of a segment.

        Args:
            segment (Segment): The segment to get information for.

        Returns:
            dict: standard information of the segment.
        """
        for seg in self.res:
            if seg["seg"] == segment:
                return seg

    def get_size_segments(self) -> list[dict]:
        """
        Get the segments occupied by the car.

        Returns:
            list[dict]: The list of segments occupied by the car.
        """
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

    def astar(self, start_seg = None, goal = None) -> Optional[List[Segment]]:
        """
        Perform the A* search algorithm to find the shortest path from the car's current segment to the goal segment.

        Returns:
            Optional[List[Segment]]: The list of segments representing the shortest path from the current segment to the goal segment, or None if no path is found.
        """

        def dist(p1: Point, p2: Point) -> float:
            """
            Calculate the Euclidean distance between two points.

            Args:
                p1 (Point): The first point.
                p2 (Point): The second point.

            Returns:
                float: The Euclidean distance between the two points.
            """
            return np.linalg.norm([p1.x - p2.x, p1.y - p2.y])

        def astar_heuristic(current_seg: Segment, goal_seg: LaneSegment) -> float:
            """
            Calculate the heuristic distance between the current segment and the goal segment for the A* algorithm.

            Args:
                current_seg (Segment): The current segment the car is on.
                goal_seg (LaneSegment): The goal segment the car is trying to reach.

            Returns:
                float: The heuristic distance between the current segment and the goal segment.
            """
            match current_seg:
                case LaneSegment():
                    if goal_seg.lane.road.horizontal:
                        if current_seg.lane.road.horizontal:
                            return dist(Point(current_seg.end, current_seg.lane.top),
                                        Point(goal_seg.begin, goal_seg.lane.top))
                        else:
                            return dist(Point(current_seg.lane.top, current_seg.end),
                                        Point(goal_seg.begin, goal_seg.lane.top))
                    else:
                        if current_seg.lane.road.horizontal:
                            return dist(Point(current_seg.end, current_seg.lane.top),
                                        Point(goal_seg.lane.top, goal_seg.begin))
                        else:
                            return dist(Point(current_seg.lane.top, current_seg.end),
                                        Point(goal_seg.lane.top, goal_seg.begin))
                case CrossingSegment():
                    if goal_seg.lane.road.horizontal:
                        return dist(Point(current_seg.horiz_lane.top + MID_LANE, current_seg.vert_lane.top + MID_LANE),
                                    Point(goal_seg.begin, goal_seg.lane.top))
                    else:
                        return dist(Point(current_seg.horiz_lane.top + MID_LANE, current_seg.vert_lane.top + MID_LANE),
                                    Point(goal_seg.lane.top, goal_seg.begin))

        def reconstruct_path(came_from_list: Dict[Segment, Segment], current: LaneSegment) -> List[Segment]:
            """
            Reconstruct the path from the start segment to the goal segment using the came_from map.

            Args:
                came_from_list (Dict[Segment, Segment]): A dictionary mapping each segment to the segment it came from.
                current (LaneSegment): The current segment (goal segment).

            Returns:
                List[Segment]: The reconstructed path from the start segment to the goal segment.
            """
            path: list[Segment] = [current]
            while current in came_from_list:
                current = came_from_list[current]
                path.insert(0, current)
            return path

        start_seg = self.res[-1]["seg"] if start_seg is None else start_seg
        goal_seg = self.goal.lane_segment if goal is None else goal.lane_segment
        # Initialize the open list with the start node and a cost of 0
        open_list = [(0, start_seg)]
        # Initialize the came_from dictionary to track the path
        came_from: dict[Segment, Segment] = {}
        # Initialize the g_score dictionary to store the cost from start to each node
        g_score = {start_seg: 0}
        # Initialize the f_score dictionary to store the total estimated cost from start to goal
        f_score = {start_seg: astar_heuristic(start_seg, goal_seg)}  # Replace with your heuristic function
        while open_list:
            _, current_seg = open_list.pop(0)

            if current_seg == goal_seg:
                return reconstruct_path(came_from, current_seg)

            neighbors = []
            match current_seg:
                case LaneSegment():
                    neighbors = [current_seg.end_crossing] if current_seg.end_crossing is not None else []
                case CrossingSegment():
                    neighbors = [seg for seg in
                                 current_seg.connected_segments.values()
                                 if seg is not None]

            for neighbor in neighbors:
                if neighbor not in g_score:
                    g_score[neighbor] = float('inf')
                    f_score[neighbor] = float('inf')
                tentative_g_score = g_score[current_seg] + current_seg.length

                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current_seg
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + astar_heuristic(neighbor, goal_seg)
                    open_list.append((f_score[neighbor], neighbor))

        return None  # No path found

