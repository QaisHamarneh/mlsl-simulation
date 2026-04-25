import math

import heapq
from itertools import count

from mlsl_simulation.game_model.car_types import CarType
from mlsl_simulation.game_model.constants import *
from mlsl_simulation.game_model.road_network.road_network import Goal, Intersection, Segment, LaneSegment, CrossingSegment, SegmentInfo, Point, Problem, direction_sign, true_direction, right_direction, horiz_direction, Color
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from typing import Optional, List, Dict


class Car:
    def __init__(self,
                 name: str,
                 type: CarType,
                 loc: int,
                 segment: LaneSegment,
                 speed: int,
                 size: int,
                 color: Color,
                 max_speed: int,
                 first_goal: Goal,
                 second_goal: Goal,
                 reservation_management: ReservationManagement) -> None:
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
        # fixed variables
        self.id = name + "_" + str(id(self))
        self.name = name
        self.type = type
        self.size = size
        self.color = color
        self.max_speed = max_speed

        # dynamic variables
        self.goal = first_goal
        self.second_goal = second_goal
        self.__dead = False
        self.speed = speed
        self.direction = segment.lane.direction
        self.changing_lane = None
        self.loc = loc
        self.illegal_move = False

        self.time: int = 0
        self.score: int = 0

        # For gui only
        self.pos = Point(0, 0)
        self.w = 0
        self.h = 0

        initial_segment_info = SegmentInfo(segment=segment,
                                           begin=self.loc,
                                           end=(1 if true_direction[self.direction] else -1) * self.get_braking_distance(),
                                           direction=self.direction)
        reservation_management.add_car_reservation(car_id=self.id, segment_info=initial_segment_info)

        self.update_position(reservation_management)

    def move(self, rm: ReservationManagement) -> bool:
        if self.__dead:
            return False

        reservations = rm.get_car_reservations_view(self.id)

        self.loc += direction_sign[reservations[0].direction] * self.speed
        self.check_reservation(rm)
        self.time += 1

        self._extend_reservations(rm)
        # `reservations` is the live list — appended items are visible.

        last = reservations[-1]
        if last.segment.length - abs(last.end) <= BLOCK_SIZE:
            state = last.segment.end_crossing.intersection.intersection_state
            if not state.get_car_priority(self.id):
                state.add_car_priority(self.id, self.time)

        while abs(self.loc) > reservations[0].segment.length:
            passed = rm.pop_car_reservation(self.id, 0)
            self.loc = direction_sign[reservations[0].direction] * (abs(self.loc) - passed.segment.length)

        reservations[0].begin = self.loc
        reservations[0].turn = False
        self.direction = reservations[0].direction

        # Single pass: time-to-leave for crossings, then expand non-tail ends, then set tail.
        crossing_speed = max(1, min(self.speed, CROSSING_MAX_SPEED))
        cumulative = 0
        n = len(reservations)
        for i, seg_info in enumerate(reservations):
            cumulative += abs(seg_info.end - seg_info.begin)
            if isinstance(seg_info.segment, CrossingSegment):
                seg_info.segment.crossing_segment_state.add_time_to_leave(
                    self.id, self.time + math.ceil(cumulative / crossing_speed))

        consumed = 0
        for i in range(n - 1):
            s = reservations[i]
            s.end = direction_sign[s.direction] * s.segment.length
            consumed += abs(s.end - s.begin)

        tail = reservations[-1]
        end_off = max(self.size + BUFFER, self.get_braking_distance() - consumed)
        tail.end = direction_sign[tail.direction] * (end_off + abs(tail.begin))

        self.update_position(rm)
        return True

    def _extend_reservations(self, rm: ReservationManagement) -> None:
        reservations = rm.get_car_reservations_view(self.id)
        braking = self.get_braking_distance()
        total_seg_length = sum(r.segment.length for r in reservations)

        if abs(self.loc) + braking < total_seg_length:
            return

        next_segs = self.get_next_segment(rm)            # FIX: was missing
        if not next_segs or len(next_segs) < 2:
            return
        next_segs = next_segs[1:]                        # drop current tail

        next_segs[0].intersection.intersection_state.pop_car_priority(self.id)

        crossing_speed = max(1, min(self.speed, CROSSING_MAX_SPEED))
        last_dir = reservations[-1].direction
        cumulative = sum(abs(r.end - r.begin) for r in reservations)

        for i, segment in enumerate(next_segs):
            if isinstance(segment, LaneSegment):
                seg_dir = segment.lane.direction
                jump = abs(self.loc) + braking - total_seg_length
                end_off = max(jump, self.size + BUFFER)
            else:  # CrossingSegment
                seg_dir = next(d for d, s in segment.connected_segments.items()
                            if s is next_segs[i + 1])
                end_off = segment.length

            sign = direction_sign[seg_dir]
            seg_info = SegmentInfo(segment, 0, sign * end_off, seg_dir, seg_dir != last_dir)
            rm.add_car_reservation(self.id, seg_info)

            cumulative += end_off
            total_seg_length += segment.length

            if isinstance(segment, CrossingSegment):
                segment.crossing_segment_state.add_time_to_leave(
                    self.id, self.time + math.ceil(cumulative / crossing_speed))

            last_dir = seg_dir


    def old_move(self, reservation_management: ReservationManagement) -> bool:
        """
        Move the car within its lane and handle lane changes and reservations.

        Returns:
            bool: True if the car moved successfully, False otherwise.
        """
        if self.get_death_status():
            return False

        # Within the lane
        self.loc += (1 if true_direction[reservation_management.get_car_reservation(self.id, 0).direction] else -1) * self.speed
        self.check_reservation(reservation_management)

        self.time += 1

        braking_distance = self.get_braking_distance()
        self.old_extend_res(reservation_management, braking_distance)

        last_seg_info = reservation_management.get_car_reservation(self.id, -1)
        if last_seg_info.segment.length - abs(last_seg_info.end) <= BLOCK_SIZE:
            intersection: Intersection = last_seg_info.segment.end_crossing.intersection
            if not intersection.intersection_state.get_car_priority(self.id):
                intersection.intersection_state.add_car_priority(self.id, self.time)

        while abs(self.loc) > reservation_management.get_car_reservation(self.id, 0).segment.length:
            seg_info = reservation_management.pop_car_reservation(self.id, 0)
            self.loc = (1 if true_direction[reservation_management.get_car_reservation(self.id, 0).direction] else -1) * (abs(self.loc) - seg_info.segment.length)

        reservation_management.update_car_reservation_begin(car_id=self.id, index=0, begin=self.loc)
        self.direction = reservation_management.get_car_reservation(car_id=self.id, index=0).direction

        reservations = reservation_management.get_car_reservations(self.id)

        for i, seg_info in enumerate(reservations):
            if isinstance(seg_info.segment, CrossingSegment):
                seg_info.segment.crossing_segment_state.add_time_to_leave(
                    self.id,
                    math.ceil(sum([abs(seg.end - seg.begin) for seg in reservations[0:i+1]]) /
                                      max(1, min(self.speed, CROSSING_MAX_SPEED))) 
                )
        
        reservation_management.update_car_reservation_turn(car_id=self.id, index=0, turn=False)

        for i, seg_info in enumerate(reservations):
            if i < len(reservations) - 1:
                reservation_management.update_car_reservation_end(car_id=self.id, 
                                                                  index=i, 
                                                                  end=(1 if true_direction[seg_info.direction] else -1) * seg_info.segment.length)

        # Update the "end" of the last reserved segment (last reserved segment is always a lane segment)
        end = max (self.size + BUFFER, 
                   braking_distance - sum([abs(reservations[i].end - reservations[i].begin) for i in range(len(reservations) - 1)]))
        
        reservation_management.update_car_reservation_end(car_id=self.id,
                                                          index=-1,
                                                          end=(1 if true_direction[reservations[-1].direction] else -1) * (end + abs(reservations[-1].begin)))

        self.update_position(reservation_management)

        return True

    def old_extend_res(self, reservations_management: ReservationManagement, breaking_distance:int) -> None:
        """
        Extend the reservation of the car to the next segments.
        """
        reservations = reservations_management.get_car_reservations(self.id)
        reserved_length = sum([abs(seg_info.end - seg_info.begin) for seg_info in reservations])
        if abs(self.loc) + breaking_distance < sum([seg_info.segment.length for seg_info in reservations]):
            return 
        
        next_segments = self.get_next_segment(reservation_management=reservations_management)
        next_segments = next_segments[1:]
        next_segments[0].intersection.intersection_state.pop_car_priority(self.id)

        jump = abs(self.loc) + breaking_distance - sum([seg_info.segment.length for seg_info in reservations])
        for i, segment in enumerate(next_segments):
            jump = abs(self.loc) + breaking_distance - sum([seg_info.segment.length for seg_info in reservations])
            next_dir = None
            if isinstance(segment, LaneSegment):
                next_dir = segment.lane.direction
            elif isinstance(segment, CrossingSegment):
                next_dir = next(dir for dir, seg in segment.connected_segments.items() if seg == next_segments[i + 1])

            segment_info = SegmentInfo(segment, 
                                       0,
                                       (1 if true_direction[next_dir] else -1) * segment.length if isinstance(segment, CrossingSegment) else\
                                       (1 if true_direction[next_dir] else -1) * max(jump, self.size + BUFFER),
                                       # min((1 if true_direction[next_dir] else -1) * extra, next_seg.length) if 
                                       # isinstance(next_seg, LaneSegment) else BLOCK_SIZE,
                                       next_dir,
                                       next_dir != reservations[-1].direction)
            
            reservations_management.add_car_reservation(self.id, segment_info)
            if isinstance(segment, CrossingSegment):
                segment.crossing_segment_state.add_time_to_leave(self.id,
                                                                 math.ceil(sum([abs(seg_info.end - seg_info.begin) for seg_info in reservations]) / 
                                                                           max(1, min(self.speed, CROSSING_MAX_SPEED))))
            reservations = reservations_management.get_car_reservations(self.id)
        
        if len(reservations) > 1:
            res_len = sum([abs(res_seg.end - res_seg.begin) for res_seg in reservations])
            if res_len != breaking_distance and \
                abs(reservations[-1].end - reservations[-1].begin) != self.size + BUFFER:
                num_lane_seg = len([seg for seg in reservations if isinstance(seg.segment, LaneSegment)])
                print(f"Issue 7 {self.name} - "\
                      f"last segment={abs(reservations[-1].end - reservations[-1].begin)} - "\
                      f"size={self.size + BUFFER} - "\
                        f"braking dist={breaking_distance} - "\
                            f"res length={res_len} - "\
                                 f"num seg={len(reservations)} - num lane seg={num_lane_seg}")

    def change_speed(self, speed_diff: int) -> None:
        """
        Change the speed of the car.

        Args:
            speed_diff (int): The difference in speed to apply.

        Returns:
            None.
        """
        self.speed = max(min(self.speed + speed_diff, self.max_speed), 0)

    def get_adjacent_lane_segments(self, reservation_management: ReservationManagement, lane_segment: None | LaneSegment = None) -> None | List[LaneSegment]:
        """
        Get the adjacent lane segment.

        Args:
            lane_diff (int): The difference in lane number.
            lane_segment (LaneSegment, optional): The current lane segment. Defaults to using the first lane segment in the reservation.

        Returns:
            LaneSegment: The adjacent lane segment.
        """
        reservations = reservation_management.get_car_reservations(self.id)
        if lane_segment is None:
            if isinstance(reservations[0].segment, LaneSegment):
                lane_segment = reservations[0].segment
            else:
                return None

        lanes = lane_segment.lane.road.right_lanes if right_direction[lane_segment.lane.direction] \
            else lane_segment.lane.road.left_lanes
        current_seg_num = lane_segment.num
        return [lane.segments[current_seg_num] for lane in lanes]
    
    def get_adjacent_lane_segment(self, reservation_management: ReservationManagement, lane_diff: int, lane_segment: None | LaneSegment = None) -> None | LaneSegment:
        """
        Get the adjacent lane segment.

        Args:
            lane_diff (int): The difference in lane number.
            lane_segment (LaneSegment, optional): The current lane segment. Defaults to using the first lane segment in the reservation.

        Returns:
            LaneSegment: The adjacent lane segment.
        """
        reservations = reservation_management.get_car_reservations(self.id)
        if lane_segment is None:
            if isinstance(reservations[0].segment, LaneSegment):
                lane_segment = reservations[0].segment
            else:
                return None

        lanes = lane_segment.lane.road.right_lanes if right_direction[lane_segment.lane.direction] \
            else lane_segment.lane.road.left_lanes
        
        actual_lane_diff = (1 if right_direction[lane_segment.lane.direction] else -1) * lane_diff
        lane_num = lane_segment.lane.num + actual_lane_diff
        current_seg_num = lane_segment.num

        if 0 <= lane_num < len(lanes):
            return  lanes[lane_num].segments[current_seg_num]
        return None

    def change_lane(self, reservations_management: ReservationManagement, lane_diff: int) -> bool | Problem:
        """
        Change the lane of the car.

        Args:
            lane_diff (int): The difference in lane number.

        Returns:
            bool: True if the lane was changed successfully, False otherwise.
        """
        reservations = reservations_management.get_car_reservations(self.id)

        # case 1: car is not in a lane segment -> return problem
        if not (isinstance(reservations[0].segment, LaneSegment) and \
                len(reservations) == 1):
            return Problem.CHANGE_LANE_WHILE_CROSSING
        # # case 2: car will not be in lane segment in LANECHANGE time steps -> return problem
        # if abs(self.loc) + self.get_braking_distance() + LANECHANGE_TIME_STEPS * self.speed > reservations[0].segment.length:
        #     return False

        if lane_diff == 0:
            return False

        adjacent_lane_seg = self.get_adjacent_lane_segment(reservations_management, lane_diff)

        # case 3: there is no adjacent lane segment -> return problem
        if adjacent_lane_seg is None:
            return Problem.NO_ADJACENT_LANE

        self.changing_lane = True
        reservations_management.set_reserved_lane_change_segment(self.id, (self.time, adjacent_lane_seg))
        return True

    def check_reservation(self, reservations_management: ReservationManagement) -> bool:
        """
        Check the reservation for lane change.

        Returns:
            bool: True if the reservation is valid, False otherwise.
        """
        if not self.changing_lane:
            return False
        
        reserved_lane_change_segment = reservations_management.get_reserved_lane_change_segment(self.id)
        reservations = reservations_management.get_car_reservations(self.id)

        if reserved_lane_change_segment is not None and \
            self.time - reserved_lane_change_segment[0] == LANECHANGE_TIME_STEPS:
            self.changing_lane = False

            new_reserve = SegmentInfo(reserved_lane_change_segment[1],
                                                        reservations[0].begin,
                                                        reservations[0].end,
                                                        reservations[0].direction)
            for _ in reservations:
                reservations_management.pop_car_reservation(self.id, 0)

            reservations_management.add_car_reservation(self.id, new_reserve)
            reservations_management.remove_reserved_lane_change_segment(self.id)
            
            self.update_position(reservations_management)

            return True

    def get_braking_distance(self, speed: int = None) -> int:
        """
        Get the braking distance of the car.

        Args:
            speed (int, optional): The speed of the car. Defaults to None.

        Returns:
            int: The braking distance of the car.
        """
        if self.get_death_status():
            return self.speed

        if speed is None:
            speed = self.speed
        assert speed >= 0, f"Speed must be positive {self.type} - {speed}"
        # braking = math.ceil(speed**2  // (2 * MAX_DEC))

        braking = 0
        while speed > 0:
            braking += speed
            speed -= MAX_DEC
        # BLOCK_SIZE // 2 additional distance when speed = 0
        return self.size + braking + BUFFER
    
    def get_size_segments(self, reservations_management: ReservationManagement) -> List[SegmentInfo]:
        """
        Get the segments occupied by the car.

        Returns:
            list[dict]: The list of segments occupied by the car.
        """
        reservations = reservations_management.get_car_reservations(self.id)
        segments: list[SegmentInfo] = []
        accumulated_size = 0
        i = 0
        while accumulated_size < self.size:
            seg_info = reservations[i]
            begin = abs(seg_info.begin)
            end = abs(seg_info.end)
            diff = end - begin   
            remaining = min(diff, self.size - accumulated_size)
            segments.append(SegmentInfo(seg_info.segment, 
                                        seg_info.begin, 
                                        seg_info.begin + (1 if true_direction[seg_info.direction] else -1) * remaining, 
                                        seg_info.direction))
            accumulated_size += diff
            i += 1
        return segments


    def get_death_status(self) -> bool:
        return self.__dead
    
    def get_next_segment(self, reservation_management: ReservationManagement, last_seg: Segment | None = None) -> List[Segment]:
        """
        Get the next segment for the car to move to.

        Args:
            last_seg (Segment): The last segment the car was on.
        Returns:
             List[Segment]: The next segments for the car to move to, up to the next Lanesegment
        """
        reservations = reservation_management.get_car_reservations(self.id)

        if last_seg is None:
            last_seg = reservations[-1].segment

        if reservations[0].segment == self.goal.lane_segment:
            #case 1: cur seg == goal seg -> preplan path to second goal
            segs = self.astar_new(reservations_management=reservation_management, start_seg=last_seg, goal=self.second_goal)

        else:
            #case 2: cur seg != goal seg -> plan path to first goal(e.g. for alternative lanes (right, left)
            segs = self.astar_new(reservations_management=reservation_management, start_seg=last_seg)
        


        if len(segs) == 0:
            print("Astar Error: No segments found by the astar function!")
            return None

        if len(segs) == 1:
            print("Astar Error: One segment found by the astar function!")
            return None

        for i in range(1, len(segs)):
            if isinstance(segs[i], LaneSegment):
                return segs[0:i + 1]

        return []

    def astar(self, reservations_management: ReservationManagement, start_seg: Segment = None, goal: Goal = None) -> Optional[List[Segment]]:
        """
        Perform the A* search algorithm to find the shortest path from the car's current segment to the goal segment.

        Returns:
            Optional[List[Segment]]: The list of segments representing the shortest path from the current segment to the goal segment, or None if no path is found.
        """

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
                            return math.dist([current_seg.end, current_seg.lane.top],
                                        [goal_seg.begin, goal_seg.lane.top])
                        else:
                            return math.dist([current_seg.lane.top, current_seg.end],
                                        [goal_seg.begin, goal_seg.lane.top])
                    else:
                        if current_seg.lane.road.horizontal:
                            return math.dist([current_seg.end, current_seg.lane.top],
                                        [goal_seg.lane.top, goal_seg.begin])
                        else:
                            return math.dist([current_seg.lane.top, current_seg.end],
                                        [goal_seg.lane.top, goal_seg.begin])
                case CrossingSegment():
                    if goal_seg.lane.road.horizontal:
                        return math.dist([current_seg.horiz_lane.top + (BLOCK_SIZE // 2), current_seg.vert_lane.top + (BLOCK_SIZE // 2)],
                                    [goal_seg.begin, goal_seg.lane.top])
                    else:
                        return math.dist([current_seg.horiz_lane.top + (BLOCK_SIZE // 2), current_seg.vert_lane.top + (BLOCK_SIZE // 2)],
                                    [goal_seg.lane.top, goal_seg.begin])

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

        start_seg = reservations_management.get_car_reservation(self.id, -1).segment if start_seg is None else start_seg
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

    def update_position(self, reservation_management: ReservationManagement) -> None:
        """
        Update the position of the car, based on the current lane segment, location, direction and speed.

        Returns:
            tuple[int, int, int, int]: The updated position (x, y, w, h) of the car.
        """
        """ Returns the bottom left corner of the car """
        segment_info = reservation_management.get_car_reservation(self.id, 0)
        segment = segment_info.segment
        is_lane_seg = isinstance(segment, LaneSegment)

        if is_lane_seg:
            seg_begin = segment.begin
        if horiz_direction[self.direction]:
            if not is_lane_seg:
                seg_begin = segment.vert_lane.top if true_direction[segment_info.direction] else segment.vert_lane.top + BLOCK_SIZE
            self.pos.y = segment.lane.top \
                if is_lane_seg else segment.horiz_lane.top
            self.pos.x = seg_begin + self.loc - (0 if true_direction[segment_info.direction] else self.size)
            self.w = self.size
            self.h = BLOCK_SIZE
        else:
            if not is_lane_seg:
                seg_begin = segment.horiz_lane.top if true_direction[segment_info.direction] else segment.horiz_lane.top + BLOCK_SIZE
            self.pos.x = segment.lane.top \
                if is_lane_seg else segment.vert_lane.top
            self.pos.y = seg_begin + self.loc - (0 if true_direction[segment_info.direction] else self.size)
            self.w = BLOCK_SIZE
            self.h = self.size

    def get_position(self) -> tuple[int, int, int, int]:
        """
        returns the position of the car.

        Returns:
            tuple[int, int, int, int]: The updated position (bottom left corner) (x, y, w, h) of the car.
        """

        return self.pos.x, self.pos.y, self.w, self.h
    
    def get_center(self, reservation_management: ReservationManagement) -> List:
        """
        Get the center point of the car.

        Returns:
            Point: The center point of the car.
        """
        reservation = reservation_management.get_car_reservation(self.id, 0)
        if horiz_direction[reservation.direction]:
            return [self.pos.x + self.size // 2, self.pos.y + BLOCK_SIZE // 2]
        else:
            return [self.pos.x + BLOCK_SIZE // 2, self.pos.y + self.size // 2]


    def astar_new(self, reservations_management: ReservationManagement,
            start_seg: Segment = None, goal: Goal = None) -> List[Segment]:

        start_seg = (reservations_management.get_car_reservation(self.id, -1).segment
                    if start_seg is None else start_seg)
        goal_seg  = self.goal.lane_segment if goal is None else goal.lane_segment

        if start_seg is goal_seg:
            return [start_seg]

        def heuristic(seg: Segment) -> float:
            # Center of seg in (x, y)
            match seg:
                case LaneSegment():
                    cx = seg.end if seg.lane.road.horizontal else seg.lane.top
                    cy = seg.lane.top if seg.lane.road.horizontal else seg.end
                case CrossingSegment():
                    cx = seg.vert_lane.top  + BLOCK_SIZE // 2   # x
                    cy = seg.horiz_lane.top + BLOCK_SIZE // 2   # y
                case _:
                    return 0.0
            gx = goal_seg.begin if goal_seg.lane.road.horizontal else goal_seg.lane.top
            gy = goal_seg.lane.top if goal_seg.lane.road.horizontal else goal_seg.begin
            return math.dist((cx, cy), (gx, gy))

        tiebreak   = count()
        open_heap  = [(heuristic(start_seg), next(tiebreak), start_seg)]
        came_from: dict[Segment, Segment] = {}
        g_score    = {start_seg: 0}
        closed: set[Segment] = set()

        while open_heap:
            _, _, current = heapq.heappop(open_heap)

            if current in closed:
                continue
            closed.add(current)

            if current is goal_seg:
                path: list[Segment] = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_seg)
                path.reverse()
                return path

            match current:
                case LaneSegment():
                    neighbors = [current.end_crossing] if current.end_crossing else []
                case CrossingSegment():
                    neighbors = [s for s in current.connected_segments.values() if s is not None]
                case _:
                    neighbors = []

            for nb in neighbors:
                if nb in closed:
                    continue
                tg = g_score[current] + current.length
                if tg < g_score.get(nb, float('inf')):
                    came_from[nb] = current
                    g_score[nb]   = tg
                    heapq.heappush(open_heap, (tg + heuristic(nb), next(tiebreak), nb))

        return []   # no path found — caller must handle empty list

    def handle_car_death(self, reservation_management: ReservationManagement) -> None:
        index = len(self.get_size_segments(reservation_management))
        reservations = reservation_management.get_car_reservations(self.id)
        for seg_info in reservations:
            if isinstance(seg_info.segment, CrossingSegment):
                seg_info.segment.intersection.intersection_state.pop_car_priority(self.id)
        while index < len(reservations):
            reservation_management.pop_car_reservation(self.id, index)
        self.speed = 0
        self.__dead = True