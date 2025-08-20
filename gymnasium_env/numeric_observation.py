from typing import Dict, Tuple
from gymnasium_env.abstract_observation import Observation
from gymnasium import spaces
from game_model.game_model import TrafficEnv
from game_model.constants import BLOCK_SIZE, LANE_DISPLACEMENT
from game_model.road_network import Direction, LaneSegment, CrossingSegment, Lane, SegmentInfo
import numpy as np

MAX_CARS = 22
MAX_LANES = 20
MAX_RES = 16

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
                shape=(MAX_LANES, 4), # direction, begin, number in road, block size or end
                dtype=np.float32
                ),
            'cars': spaces.Box(
                low=np.inf, 
                high=np.inf,
                shape=(MAX_CARS, 1 + MAX_RES, 6), 
                # (speed + 10 res) * 6 fields (res_begin, res_end, seg_begin, seg_end, direction, lane or crossing
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
                direction = lane.direction.value
                num_in_road = lane.num
                begin, end = self._lane_span(lane)
                lanes.append([direction, num_in_road, begin, end])

        while len(lanes) < MAX_LANES:
            lanes.append([-1] * 4)

        lanes = np.array(lanes, dtype=np.float32)

        # cars
        cars = []
        for car in self.game_model.cars:
            speed = np.array([[car.speed] + [0] * 5], dtype=np.float32)

            reservations = []
            for seg_info in car.res:
                direction = seg_info.direction.value
                res_begin = seg_info.begin
                res_end = seg_info.end
                seg_begin, seg_end, seg_type = self._segment_span(seg_info)

                reservations.append([
                    seg_type,
                    direction,
                    res_begin,
                    res_end,
                    seg_begin,
                    seg_end
                ])

            while len(reservations) < MAX_RES:
                reservations.append([0] * 6)

            reservations = np.array(reservations, dtype=np.float32)
            all_info = np.vstack((speed, reservations))
            cars.append(all_info)

        while len(cars) < MAX_CARS:
            cars.append(np.zeros((1 + MAX_RES, 6), dtype=np.float32))

        cars = np.array(cars, dtype=np.float32)

        return {
            'block_size': block_size,
            'lanes': lanes,
            'cars': cars
        }
    
    def _lane_span(self, lane: Lane) -> Tuple[int, int]:
        lane_segments = [segment for segment in lane.segments if isinstance(segment, LaneSegment)]
        if not lane_segments:
            return lane.top, lane.top
        begin = lane_segments[0].begin
        end = lane_segments[-1].end
        return begin, end
    
    def _segment_span(self, seg_info: SegmentInfo) -> Tuple[int, int, int]:
        seg = seg_info.segment
        if isinstance(seg, LaneSegment):
            return seg.begin, seg.end, 1  # type 1 = lane
        else:
            if seg_info.direction in (Direction.LEFT, Direction.RIGHT):
                return seg.horiz_lane.top, seg.horiz_lane.top + seg.length, 2
            else:
                return seg.vert_lane.top, seg.vert_lane.top + seg.length, 2