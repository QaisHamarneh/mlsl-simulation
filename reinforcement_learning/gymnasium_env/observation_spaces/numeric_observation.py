import numpy as np

from typing import List, Dict, Tuple
from reinforcement_learning.gymnasium_env.observation_spaces.abstract_observation import Observation
from reinforcement_learning.gymnasium_env.observation_spaces.observation_model_types import ObservationModelType
from reinforcement_learning.gymnasium_env.observation_spaces.observation_registry import register_observation_model
from gymnasium import spaces
from game_model.constants import BLOCK_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from game_model.road_network import Direction, LaneSegment, CrossingSegment, Lane, SegmentInfo
from scenarios.scenarios import SCENARIOS

MAX_CARS = max([scenario["players"] for _, scenario in SCENARIOS.items()])
MAX_LANES = max([sum([len(road.right_lanes) + len(road.left_lanes) for road in scenario["roads"]]) for _, scenario in SCENARIOS.items()])
MAX_RES = 16

LANES_INFO = 6
CAR_RES_INFO = 6

@register_observation_model(ObservationModelType.NUMERIC_OBSERVATION)
class NumbericObservation(Observation):
    """Numeric observation model for RL environment.
    
    Converts the game state into a flattened numeric observation suitable for
    reinforcement learning algorithms. The observation includes information about
    lanes (their position and direction) and car reservations (speed and segment
    reservations along their path).
    
    The observation space is a Box with shape (obs_dim,) where:
    - First MAX_LANES * LANES_INFO values represent lane information
    - Remaining MAX_CARS * (1 + MAX_RES) * CAR_RES_INFO values represent car data
    """
    
    def space(self) -> spaces.Space:
        """Define the observation space for the RL environment.
        
        Returns a gymnasium Box space with normalized values in [0, 1] containing
        information about all lanes and car reservations.
        
        Returns:
            spaces.Box: A box space with shape (obs_dim,) and dtype float32.
                The total dimension includes:
                - lanes_shape: MAX_LANES * LANES_INFO (6 features per lane)
                - cars_shape: MAX_CARS * (1 + MAX_RES) * CAR_RES_INFO
                             (6 features per reservation + speed)
        """
        lanes_shape = MAX_LANES * LANES_INFO
        cars_shape = MAX_CARS * (1 + MAX_RES) * CAR_RES_INFO

        obs_dim = lanes_shape + cars_shape

        return spaces.Box(
            low=0,
            high=1,
            shape=(obs_dim,),
            dtype=np.float32
        )

    def observe(self) -> Dict:
        """Generate the current numeric observation from the game state.
        
        Constructs a flattened numpy array containing:
        1. Lane information: For each lane, the normalized lane number, direction,
           and bounding box coordinates (begin_x, begin_y, end_x, end_y).
        2. Car information: For each car, the normalized speed and up to MAX_RES
           reservation segments, each containing lane number, direction, and
           normalized position coordinates within the segment.
        
        Padding is applied with zeros when the actual number of lanes or cars
        is less than the maximum constants.
        
        Returns:
            numpy.ndarray: Flattened observation array of shape (obs_dim,) with
                dtype float32. All values are normalized to [0, 1].
        """
        # block size
        # block_size = np.array([BLOCK_SIZE / WINDOW_WIDTH, BLOCK_SIZE / WINDOW_HEIGHT])

        # lanes
        lanes = []
        for road in self.game_model.roads:
            for lane in road.left_lanes + road.right_lanes:
                lanes.append(self._get_lane_bounds(lane))

        while len(lanes) < MAX_LANES:
            lanes.append([0] * LANES_INFO)

        lanes = np.array(lanes, dtype=np.float32).flatten()

        # car reservations
        cars = []
        for car in self.game_model.cars:
            speed = np.array([[car.speed / car.max_speed] + [0] * (CAR_RES_INFO - 1)], dtype=np.float32)

            reservations = []
            for seg_info in self.reservation_management.iterate_car_reservations(car.id):

                if isinstance(seg_info.segment, LaneSegment):

                    # todo: move doubled code from lanesegment and crossing segment
                    reservations.append([
                        seg_info.segment.lane.num / MAX_LANES,
                        seg_info.direction.value / Direction.DIRECTIONS.value,
                        *self._get_lane_reservation(seg_info, seg_info.segment)
                    ])

                elif isinstance(seg_info.segment, CrossingSegment):
                    lane_num = seg_info.segment.horiz_lane.num if seg_info.direction in (Direction.RIGHT, Direction.LEFT) else seg_info.segment.vert_lane.num

                    reservations.append([
                        lane_num / MAX_LANES,
                        seg_info.direction.value / Direction.DIRECTIONS.value,
                        *self._get_crossing_reservation(seg_info, seg_info.segment)
                    ])

            while len(reservations) < MAX_RES:
                reservations.append([0] * CAR_RES_INFO)

            reservations = np.array(reservations, dtype=np.float32)
            all_info = np.vstack((speed, reservations))
            cars.append(all_info)

        while len(cars) < MAX_CARS:
            cars.append(np.zeros((1 + MAX_RES, CAR_RES_INFO), dtype=np.float32))

        cars = np.array(cars, dtype=np.float32).flatten()

        return np.concatenate([lanes, cars])
    
    def _get_lane_bounds(self, lane: Lane) -> List[float]:
        """Get normalized bounding box coordinates for a lane.
        
        Computes the lane's position and extent in normalized window coordinates.
        The returned coordinates represent the lane's start and end points on the
        road network, normalized relative to the window dimensions.
        
        Args:
            lane (Lane): The lane object to extract bounds from.
        
        Returns:
            List[float]: A list of 6 normalized values:
                [lane_num_normalized, direction_normalized, begin_x, begin_y, end_x, end_y]
                where:
                - lane_num_normalized: lane.num / MAX_LANES
                - direction_normalized: lane.direction.value / Direction.DIRECTIONS.value
                - begin_x, begin_y: normalized starting coordinates
                - end_x, end_y: normalized ending coordinates
                Normalization is relative to WINDOW_WIDTH and WINDOW_HEIGHT.
        """
        total_length = sum(seg.length for seg in lane.segments)

        normalized_lane_num = lane.num / MAX_LANES
        normalized_lane_direction = lane.direction.value / Direction.DIRECTIONS.value

        if lane.direction is Direction.RIGHT:
            return [normalized_lane_num, 
                    normalized_lane_direction, 
                    0, 
                    lane.top / WINDOW_HEIGHT, 
                    total_length / WINDOW_WIDTH, 
                    lane.top / WINDOW_HEIGHT]
        elif lane.direction is Direction.DOWN:
            return [normalized_lane_num, 
                    normalized_lane_direction, 
                    lane.top / WINDOW_WIDTH, 
                    total_length / WINDOW_HEIGHT, 
                    lane.top / WINDOW_WIDTH, 
                    0]
        elif lane.direction is Direction.LEFT:
            return [normalized_lane_num, 
                    normalized_lane_direction, 
                    total_length / WINDOW_WIDTH, 
                    lane.top / WINDOW_HEIGHT, 
                    0, 
                    lane.top / WINDOW_HEIGHT]
        else:  # UP
            return [normalized_lane_num, 
                    normalized_lane_direction, 
                    lane.top / WINDOW_WIDTH, 
                    0, 
                    lane.top / WINDOW_WIDTH, 
                    total_length / WINDOW_HEIGHT]

    def _get_lane_reservation(self, seg_info: SegmentInfo, seg: LaneSegment) -> Tuple[float, float, float, float]:
        """Get normalized coordinates for a lane segment reservation.
        
        Calculates the start and end positions of a reservation within a lane segment,
        accounting for the lane's direction (horizontal or vertical).
        
        Args:
            seg_info (SegmentInfo): Information about the segment reservation including
                begin and end positions within the segment.
            seg (LaneSegment): The lane segment object.
        
        Returns:
            Tuple[float, float, float, float]: A tuple of 4 normalized values:
                (res_begin_x, res_begin_y, res_end_x, res_end_y)
                All coordinates are normalized relative to WINDOW_WIDTH and WINDOW_HEIGHT.
        """
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
            res_begin_x / WINDOW_WIDTH, 
            res_begin_y / WINDOW_HEIGHT, 
            res_end_x / WINDOW_WIDTH, 
            res_end_y / WINDOW_HEIGHT
        ]

    def _get_crossing_reservation(self, seg_info: SegmentInfo, seg: CrossingSegment) -> Tuple[float, float, float, float]:
        """Get normalized coordinates for a crossing segment reservation.
        
        Calculates the start and end positions of a reservation within a crossing segment.
        Handles both horizontal and vertical crossings by selecting the appropriate lane.
        
        Args:
            seg_info (SegmentInfo): Information about the segment reservation.
            seg (CrossingSegment): The crossing segment object.
        
        Returns:
            Tuple[float, float, float, float]: A tuple of 4 normalized values:
                (begin_x, begin_y, end_x, end_y) representing the reservation bounds
                within the crossing, normalized relative to WINDOW_WIDTH and WINDOW_HEIGHT.
        """
        # Pick the correct lane (horizontal vs vertical)
        lane = seg.horiz_lane if seg_info.direction in (Direction.LEFT, Direction.RIGHT) else seg.vert_lane
        forward = seg_info.direction in (Direction.RIGHT, Direction.UP)

        return self._accumulate_crossing_coords(lane, seg, forward)

    def _accumulate_crossing_coords(self, lane, target_seg, forward: bool) -> Tuple[float, float, float, float]:
        """Accumulate coordinates for a target crossing segment along a lane.
        
        Traverses the lane's segments in forward or reverse order to find the target
        crossing segment and returns its normalized position coordinates.
        
        Args:
            lane: The lane containing the crossing segment.
            target_seg: The crossing segment to locate.
            forward (bool): If True, traverse segments in forward order. If False, traverse
                in reverse order.
        
        Returns:
            Tuple[float, float, float, float]: A tuple of 4 normalized values:
                (begin_x, begin_y, end_x, end_y) representing the target segment's
                position in normalized window coordinates.
        
        Raises:
            ValueError: If the target segment is not found in the lane.
        """
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