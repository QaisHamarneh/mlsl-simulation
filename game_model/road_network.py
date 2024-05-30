from dataclasses import dataclass
from enum import Enum
from game_model.constants import *
from abc import ABC


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

clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]


Color = (int, int, int)


class Road:
    def __init__(self,
                 name: str,
                 horizontal: bool,
                 top: int,
                 right: int,
                 left: int) -> None:
        self.name = name
        self.horizontal = horizontal
        self.top = top

        self.right_lanes = [Lane(self, i, Direction.RIGHT if self.horizontal else Direction.DOWN,
                                 self.top + i * BLOCK_SIZE + i * LANE_DISPLACEMENT)
                            for i in range(right)]

        # Below the last left lane
        self.half = self.top + right * BLOCK_SIZE + (right - 1) * LANE_DISPLACEMENT

        self.left_lanes = [Lane(self, i, Direction.LEFT if self.horizontal else Direction.UP,
                                self.top + i * BLOCK_SIZE + i * LANE_DISPLACEMENT +
                                right * BLOCK_SIZE + right * LANE_DISPLACEMENT)
                           for i in range(left)]

        # Below the last right lane
        self.bottom = self.top + (right + left) * BLOCK_SIZE + (
                right + left - 1) * LANE_DISPLACEMENT


class Lane:
    def __init__(self,
                 road: Road,
                 num: int,
                 direction: Direction,
                 top: int) -> None:
        self.road = road
        self.num = num
        self.top = top
        self.direction = direction
        self.segments = []


class Segment(ABC):
    def __init__(self) -> None:
        self.length = 0
        self.cars = []
        self.max_speed = 0


class LaneSegment(Segment):
    def __init__(self, lane: Lane, begin: int, end: int) -> None:
        super().__init__()
        self.lane = lane
        self.begin = begin
        self.end = end
        self.end_crossing = None
        self.length = abs(self.end - self.begin)
        self.num = None
        self.max_speed = BLOCK_SIZE // 3

    def __str__(self):
        return f"{self.lane.road.name}:{self.lane.direction.name}:{self.lane.num}"


class CrossingSegment(Segment):
    def __init__(self, horiz_lane: Lane, vert_lane: Lane) -> None:
        super().__init__()
        self.horiz_lane = horiz_lane
        self.vert_lane = vert_lane
        self.connected_segments: dict[Direction, Segment] = {Direction.RIGHT: None,
                                                             Direction.LEFT: None,
                                                             Direction.UP: None,
                                                             Direction.DOWN: None}
        self.length = BLOCK_SIZE
        self.horiz_num = None
        self.vert_num = None
        self.max_speed = BLOCK_SIZE // 10

    def get_road(self, direction: Direction, opposite: bool = False):
        if horiz_direction[direction] and not opposite:
            return self.horiz_lane.road
        else:
            return self.vert_lane.road

    def __str__(self):
        return f"({self.horiz_lane.road.name}:{self.horiz_lane.direction.name}:{self.horiz_lane.num}, " \
               f"{self.vert_lane.road.name}:{self.vert_lane.direction.name}:{self.vert_lane.num})"


class Goal:
    def __init__(self, lane_segment: LaneSegment, color: Color) -> None:
        self.lane_segment = lane_segment
        self.color = color
        self.update_position()

    def update_position(self):
        mid_seg = (self.lane_segment.begin + self.lane_segment.end) // 2
        self.pos = Point(mid_seg, self.lane_segment.lane.top + BLOCK_SIZE // 2) \
            if self.lane_segment.lane.road.horizontal \
            else Point(self.lane_segment.lane.top + BLOCK_SIZE // 2, mid_seg)
