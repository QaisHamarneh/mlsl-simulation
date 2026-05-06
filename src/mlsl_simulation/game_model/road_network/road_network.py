from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Tuple

from mlsl_simulation.constants import *
from mlsl_simulation.game_model.reservations.intersection_state import IntersectionState
from mlsl_simulation.game_model.reservations.crossing_segment_state import CrossingSegmentState


@dataclass
class Point:
    x: int
    y: int


class Direction(Enum):
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    UP = 4


class Problem(Enum):
    NO_NEXT_SEGMENT = 1
    CHANGE_LANE_WHILE_CROSSING = 2
    SLOWER_WHILE_0 = 3
    FASTER_WHILE_MAX = 4
    NO_ADJACENT_LANE = 5
    LANE_TOO_SHORT = 6


direction_axis = {Direction.RIGHT: (1, 0),
                  Direction.LEFT: (-1, 0),
                  Direction.UP: (0, 1),
                  Direction.DOWN: (0, -1)
                  }

true_direction = {Direction.RIGHT: True,
                  Direction.LEFT: False,
                  Direction.UP: True,
                  Direction.DOWN: False
                  }

horiz_direction = {Direction.RIGHT: True,
                   Direction.LEFT: True,
                   Direction.UP: False,
                   Direction.DOWN: False
                   }

right_direction = {Direction.RIGHT: True,
                   Direction.LEFT: False,
                   Direction.UP: False,
                   Direction.DOWN: True
                   }

direction_sign = {Direction.RIGHT: 1, Direction.LEFT: -1,
                  Direction.UP: 1, Direction.DOWN: -1}

clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]


Color = Tuple[int, int, int]


class Road:
    def __init__(self, name: str, horizontal: bool, top: int, right: int, left: int) -> None:
        """
        Initialize a Road object.

        Args:
            name (str): The name of the road.
            horizontal (bool): Whether the road is horizontal.
            top (int): The top position of the road.
            right (int): The number of right lanes.
            left (int): The number of left lanes.
        """
        self.name = name
        self.horizontal = horizontal
        self.top = top
        
        self.right_lanes = [Lane(self, i, Direction.RIGHT if self.horizontal else Direction.DOWN,
                                 self.top + i * BLOCK_SIZE)
                            for i in range(right)]

        self.left_lanes = [Lane(self, i, Direction.LEFT if self.horizontal else Direction.UP,
                                self.top + i * BLOCK_SIZE + i + right * BLOCK_SIZE)
                           for i in range(left)]

        # Below the last right lane
        self.bottom = self.top + (right + left) * BLOCK_SIZE

    def get_outer_lane_segment(self, segment: 'Segment', right_lanes: bool) -> Optional['LaneSegment']:
        """
        Get the outer lane segment.

        Args:
            segment (Segment): The segment to get the outer lane segment for.
            right_lanes (bool): Whether to get the right lanes.

        Returns:
            Optional[LaneSegment]: The outer lane segment if it exists, otherwise None.
        """
        if right_lanes:
            return self.right_lanes[0].segments[segment.num] if len(self.right_lanes) > 0 else None
        else:
            return self.left_lanes[-1].segments[segment.num] if len(self.left_lanes) > 0 else None

class Intersection:
    def __init__(self, horizontal_road: Road, vertical_road: Road):
        self.horizontal_road: Road = horizontal_road
        self.vertical_road: Road = vertical_road
        self.segments: List[CrossingSegment] = []
        self.intersection_state = IntersectionState()
    
    def __str__(self):
        return f"Horizontal: {self.horizontal_road.name} - Vertical: {self.vertical_road.name} - Crossing Segments {len(self.segments)}"

class Lane:
    def __init__(self, road: Road, num: int, direction: Direction, top: int) -> None:
        """
        Initialize a Lane object.

        Args:
            road (Road): The road the lane belongs to.
            num (int): The lane number.
            direction (Direction): The direction of the lane.
            top (int): The top position of the lane.
        """
        self.road: Road = road
        self.num: int = num
        self.top: int = top
        self.direction: Direction = direction
        self.segments: List[Segment] = []


class Segment(ABC):
    def __init__(self) -> None:
        """
        Initialize a Segment object.
        """
        self.length: int
        self.max_speed: int
        self.h_begin: int
        self.v_begin: int



class LaneSegment(Segment):
    def __init__(self, lane: Lane, begin: int, end: int, num) -> None:
        """
        Initialize a LaneSegment object.

        Args:
            lane (Lane): The lane the segment belongs to.
            begin (int): The beginning position of the segment.
            end (int): The ending position of the segment.
        """
        super().__init__()
        self.road: Road = lane.road
        self.lane: Lane = lane
        self.begin: int = begin
        self.end: int = end
        self.num: int = num
        self.end_crossing: Optional[CrossingSegment] = None
        self.begin_crossing: Optional[CrossingSegment] = None
        self.length: int = abs(self.end - self.begin)
        self.max_speed: int = LANE_MAX_SPEED
        self.h_begin = self.begin if horiz_direction[self.lane.direction] else self.lane.top
        self.v_begin = self.lane.top if horiz_direction[self.lane.direction] else self.begin

    def __str__(self) -> str:
        """
        Return a string representation of the LaneSegment.

        Returns:
            str: The string representation of the LaneSegment.
        """
        return f"{self.lane.road.name}:{self.lane.direction.name}:{self.lane.num}:{self.num}"


class CrossingSegment(Segment):
    def __init__(self, horiz_lane: Lane, vert_lane: Lane, intersection: Intersection) -> None:
        """
        Initialize a CrossingSegment object.

        Args:
            horiz_lane (Lane): The horizontal lane.
            vert_lane (Lane): The vertical lane.
        """
        super().__init__()
        self.horiz_lane: Lane = horiz_lane
        self.vert_lane: Lane = vert_lane
        self.intersection: Intersection = intersection
        self.connected_segments: Dict[Direction, Optional[Segment]] = {
            Direction.RIGHT: None,
            Direction.LEFT: None,
            Direction.UP: None,
            Direction.DOWN: None
        }
        self.length: int = BLOCK_SIZE
        self.horiz_num: Optional[int] = None
        self.vert_num: Optional[int] = None
        self.max_speed: int = CROSSING_MAX_SPEED
        self.crossing_segment_state: CrossingSegmentState = CrossingSegmentState()
        self.h_begin = self.vert_lane.top
        self.v_begin = self.horiz_lane.top

    def get_road(self, direction: Direction, opposite: bool = False) -> Road:
        """
        Get the road in the given direction.

        Args:
            direction (Direction): The direction to get the road for.
            opposite (bool): Whether to get the opposite road.

        Returns:
            Road: The road in the given direction.
        """
        if (horiz_direction[direction] and not opposite) or (not horiz_direction[direction] and opposite):
            return self.horiz_lane.road
        else:
            return self.vert_lane.road

    def __str__(self):
        return f"({self.horiz_lane.road.name}:{self.horiz_lane.direction.name}:{self.horiz_lane.num}, " \
               f"{self.vert_lane.road.name}:{self.vert_lane.direction.name}:{self.vert_lane.num})"


class SegmentInfo:
    def __init__(self, segment: Segment, begin: int, end:int, direction: Direction, turn:bool=False) -> None:
        self.segment = segment
        self.begin = begin
        self.end = end
        self.direction = direction
        self.turn = turn
        
    def __str__(self):
        return f"{self.segment} -- begin = {self.begin}, end = {self.end}"


class Goal:
    def __init__(self, lane_segment: LaneSegment, color: Color) -> None:
        """
        Initialize a Goal object.

        Args:
            lane_segment (LaneSegment): The lane segment the goal is on.
            color (Color): The color of the goal.are
        """
        self.pos = Point(0, 0)
        self.color = color
        self.update_lane_segment(lane_segment)

    def update_lane_segment(self, lane_segment: LaneSegment) -> None:
        self.lane_segment = lane_segment
        self._update_position()

    def _update_position(self) -> None:
        """
        Update the position of the goal.
        """
        mid_seg = (self.lane_segment.begin + self.lane_segment.end) // 2
        self.pos = Point(mid_seg, self.lane_segment.lane.top + BLOCK_SIZE // 2) \
            if self.lane_segment.lane.road.horizontal \
            else Point(self.lane_segment.lane.top + BLOCK_SIZE // 2, mid_seg)
