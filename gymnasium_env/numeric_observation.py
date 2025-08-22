from typing import Dict, Tuple
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
                lane_number = lane.num
                direction = lane.direction

                if direction is Direction.RIGHT:
                    begin_x = 0
                    end_x = sum([semgment.length for semgment in lane.segments])
                    begin_y = end_y = lane.top
                elif direction is Direction.DOWN:
                    begin_x = end_x = lane.top
                    begin_y = sum([semgment.length for semgment in lane.segments])
                    end_y = 0
                elif direction is Direction.LEFT:
                    begin_x = sum([semgment.length for semgment in lane.segments])
                    end_x = 0
                    begin_y = end_y = lane.top
                else:
                    begin_x = end_x = lane.top
                    begin_y = 0
                    end_y = sum([semgment.length for semgment in lane.segments])

                lanes.append([
                    lane_number, 
                    direction.value, 
                    begin_x, 
                    begin_y, 
                    end_x, 
                    end_y
                ])

        while len(lanes) < MAX_LANES:
            lanes.append([-1] * LANES_INFO)

        lanes = np.array(lanes, dtype=np.float32)

        print(lanes)

        test = False
        cars = []
        for car in self.game_model.cars:
            speed = np.array([[car.speed] + [0] * (CAR_RES_INFO - 1)], dtype=np.float32)

            reservations = []
            for seg_info in car.res:

                if isinstance(seg_info.segment, LaneSegment):
                    test = True

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

        # if test:
        #     print(cars)

        return {
            'block_size': block_size,
            'lanes': lanes,
            'cars': cars
        }

    def _get_lane_reservation(self, seg_info: SegmentInfo, seg: LaneSegment) -> Tuple[float, float, float, float]:
        # horizontal lane
        if seg_info.direction in (Direction.RIGHT, Direction.LEFT):
            res_begin_x = seg.begin + seg_info.begin 
            res_end_x = seg.begin + seg_info.end
            res_begin_y = res_end_y = seg.lane.top

            if seg_info.direction is Direction.RIGHT:
                assert res_begin_x <= res_end_x
            else:
                assert res_begin_x >= res_end_x
        # vertical lane
        else:
            res_begin_x = res_end_x = seg.lane.top
            res_begin_y = seg.begin + seg_info.begin
            res_end_y = seg.begin + seg_info.end

            if seg_info.direction is Direction.UP:
                assert res_begin_y <= res_end_y
            else:
                assert res_begin_y >= res_end_y

        return [
            res_begin_x, 
            res_begin_y, 
            res_end_x, 
            res_end_y
        ]
    
    def _get_crossing_reservation(self, seg_info: SegmentInfo, seg: CrossingSegment) -> Tuple[float, float, float, float]:
        res_begin_x = res_begin_y = res_end_x = res_end_y = None
        blocks = 0
        
        if seg_info.direction in (Direction.RIGHT, Direction.UP):
            lane = seg.horiz_lane if seg_info.direction is Direction.RIGHT else seg.vert_lane

            for i in range(len(lane.segments)):
                blocks += lane.segments[i].length

                if (lane.segments[i] is seg):
                    if lane.direction is Direction.UP:
                        res_begin_y = blocks - BLOCK_SIZE
                        res_end_y = blocks
                        res_begin_x = res_end_x = lane.top
                    else:
                        res_begin_x = blocks - BLOCK_SIZE
                        res_end_x = blocks
                        res_begin_y = res_end_y = lane.top
        else:
            lane = seg.horiz_lane if seg_info.direction is Direction.LEFT else seg.vert_lane

            for i in range(len(lane.segments) - 1, 0, -1):
                blocks += lane.segments[i].length

                if (lane.segments[i] is seg):
                    if lane.direction is Direction.DOWN:
                        res_begin_y = WINDOW_HEIGHT - blocks + BLOCK_SIZE
                        res_end_y = WINDOW_HEIGHT - blocks
                        res_begin_x = res_end_x = lane.top
                    else:
                        res_begin_x = WINDOW_WIDTH - blocks + BLOCK_SIZE
                        res_end_x = WINDOW_WIDTH - blocks
                        res_begin_y = res_end_y = lane.top

        return [
            res_begin_x,
            res_begin_y,
            res_end_x,
            res_end_y
        ]