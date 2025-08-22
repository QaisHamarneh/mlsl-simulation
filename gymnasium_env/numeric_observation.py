from typing import List, Dict, Tuple
from gymnasium_env.abstract_observation import Observation
from gymnasium import spaces
from game_model.game_model import TrafficEnv
from game_model.constants import BLOCK_SIZE, LANE_DISPLACEMENT, WINDOW_WIDTH, WINDOW_HEIGHT
from game_model.road_network import Direction, LaneSegment, CrossingSegment, Lane, SegmentInfo
import numpy as np

MAX_CARS = 22
MAX_LANES = 20
MAX_RES = 16

LANES_INFO = 6
CAR_RES_INFO = 6

LANE_SEGMENT = 1
CROSSING_SEGMENT = 2

class NumbericObservation(Observation):
    def __init__(self, game_model: TrafficEnv) -> None:
        super().__init__(game_model)

    def space(self) -> spaces.Space:
        return spaces.Dict({
            'block_size': spaces.Box(
                low=0, 
                high=np.inf, 
                shape=(1,), 
                dtype=np.float32
                ),
            'lanes': spaces.Box(
                low=np.inf, 
                high=np.inf,
                shape=(MAX_LANES, LANES_INFO),
                dtype=np.float32
                ),
            'cars': spaces.Box(
                low=np.inf, 
                high=np.inf,
                shape=(MAX_CARS, 1 + MAX_RES, CAR_RES_INFO), 
                # (speed + 16 res) * 6 fields (res_begin, res_end, seg_begin, seg_end, direction, lane or crossing
                dtype=np.float32
                )
            })

    def observe(self) -> Dict:
        # block size
        block_size = np.array([BLOCK_SIZE])

        # lanes
        lanes = []
        for road in self.game_model.roads:
            for lane in road.left_lanes + road.right_lanes:
                lanes.append(self._get_lane_bounds(lane))

        while len(lanes) < MAX_LANES:
            lanes.append([-1] * LANES_INFO)

        lanes = np.array(lanes, dtype=np.float32)

        # car reservations
        cars = []
        for car in self.game_model.cars:
            speed = np.array([[car.speed] + [0] * (CAR_RES_INFO - 1)], dtype=np.float32)

            reservations = []
            for seg_info in car.res:

                if isinstance(seg_info.segment, LaneSegment):

                    reservations.append([
                        seg_info.segment.lane.num,
                        seg_info.direction.value,
                        *self._get_lane_reservation(seg_info, seg_info.segment)
                    ])

                elif isinstance(seg_info.segment, CrossingSegment):
                    lane_num = seg_info.segment.horiz_lane.num if seg_info.direction in (Direction.RIGHT, Direction.LEFT) else seg_info.segment.vert_lane.num

                    reservations.append([
                        lane_num,
                        seg_info.direction.value,
                        *self._get_crossing_reservation(seg_info, seg_info.segment)
                    ])

            while len(reservations) < MAX_RES:
                reservations.append([0] * CAR_RES_INFO)

            reservations = np.array(reservations, dtype=np.float32)
            all_info = np.vstack((speed, reservations))
            cars.append(all_info)

        while len(cars) < MAX_CARS:
            cars.append(np.zeros((1 + MAX_RES, CAR_RES_INFO), dtype=np.float32))

        cars = np.array(cars, dtype=np.float32)

        return {
            'block_size': block_size,
            'lanes': lanes,
            'cars': cars
        }
    
    def _get_lane_bounds(self, lane) -> List[float]:
        """Return lane_number, direction, begin_x, begin_y, end_x, end_y"""
        total_length = sum(seg.length for seg in lane.segments)

        if lane.direction is Direction.RIGHT:
            return [lane.num, lane.direction.value, 0, lane.top, total_length, lane.top]
        elif lane.direction is Direction.DOWN:
            return [lane.num, lane.direction.value, lane.top, total_length, lane.top, 0]
        elif lane.direction is Direction.LEFT:
            return [lane.num, lane.direction.value, total_length, lane.top, 0, lane.top]
        else:  # UP
            return [lane.num, lane.direction.value, lane.top, 0, lane.top, total_length]

    def _get_lane_reservation(self, seg_info: SegmentInfo, seg: LaneSegment) -> Tuple[float, float, float, float]:
        # horizontal lane
        if seg_info.direction in (Direction.RIGHT, Direction.LEFT):
            res_begin_x = seg.begin + seg_info.begin 
            res_end_x = seg.begin + seg_info.end
            res_begin_y = res_end_y = seg.lane.top
        # vertical lane
        else:
            res_begin_x = res_end_x = seg.lane.top
            res_begin_y = seg.begin + seg_info.begin
            res_end_y = seg.begin + seg_info.end

        return [
            res_begin_x, 
            res_begin_y, 
            res_end_x, 
            res_end_y
        ]

    def _get_crossing_reservation(self, seg_info: SegmentInfo, seg: CrossingSegment) -> Tuple[float, float, float, float]:
        # Pick the correct lane (horizontal vs vertical)
        lane = seg.horiz_lane if seg_info.direction in (Direction.LEFT, Direction.RIGHT) else seg.vert_lane
        forward = seg_info.direction in (Direction.RIGHT, Direction.UP)

        return self._accumulate_crossing_coords(lane, seg, forward)

    def _accumulate_crossing_coords(self, lane, target_seg, forward: bool) -> Tuple[float, float, float, float]:
        blocks = 0
        segments = lane.segments if forward else reversed(lane.segments)

        for seg in segments:
            blocks += seg.length
            if seg is target_seg:
                if lane.direction is Direction.UP:
                    return [lane.top, blocks - BLOCK_SIZE, lane.top, blocks]
                elif lane.direction is Direction.DOWN:
                    return [lane.top, WINDOW_HEIGHT - blocks + BLOCK_SIZE, lane.top, WINDOW_HEIGHT - blocks]
                elif lane.direction is Direction.RIGHT:
                    return [blocks - BLOCK_SIZE, lane.top, blocks, lane.top]
                elif lane.direction is Direction.LEFT:
                    return [WINDOW_WIDTH - blocks + BLOCK_SIZE, lane.top, WINDOW_WIDTH - blocks, lane.top]

        raise ValueError("Target segment not found in lane")