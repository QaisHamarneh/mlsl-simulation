from typing import Dict, List, Tuple
from mlsl_simulation.game_model.road_network.road_network import Segment, LaneSegment, CrossingSegment, SegmentInfo

from mlsl_simulation.game_model.reservations.car_reservation_store import CarReservationStore
from mlsl_simulation.game_model.reservations.segment_occupancy_tracker import SegmentOccupancyTracker

class ReservationManagement:
    def __init__(self):
        self.__car_reservation_store: CarReservationStore = CarReservationStore()
        self.__segment_occupancy_tracker: SegmentOccupancyTracker = SegmentOccupancyTracker()

        self.__reserved_lane_change_segments: Dict[str, Tuple[int, LaneSegment] | None] = {}

    def add_car_reservation(self, car_id: str, segment_info: SegmentInfo) -> None:
        self.__car_reservation_store.add_reservation(car_id, segment_info)
        self.__segment_occupancy_tracker.add_segment_occupancy(segment_info.segment, car_id)


    def get_car_reservation(self, car_id: str, index: int) -> SegmentInfo:
        return self.__car_reservation_store.get_reservation(car_id, index)


    def pop_car_reservation(self, car_id: str, index: int) -> SegmentInfo:
        segment_info = self.__car_reservation_store.pop_reservation(car_id, index)
        self.__segment_occupancy_tracker.remove_segment_occupancy(segment_info.segment, car_id)

        if isinstance(segment_info.segment, CrossingSegment):
            segment_info.segment.crossing_segment_state.remove_time_to_leave(car_id)

        return segment_info

    
    def get_cars_on_segment(self, segment: Segment) -> List[str]:
        return self.__segment_occupancy_tracker.get_cars_on_segment(segment)

    def get_reserved_lane_change_segment(self, car_id: str) -> Tuple[int, LaneSegment] | None:
        return self.__reserved_lane_change_segments[car_id] 

    def update_reserved_lane_change_segment(self, car_id: str, segment: Tuple[int, LaneSegment]) -> None:
        self.__reserved_lane_change_segments[car_id] = segment

    def remove_reserved_lane_change_segment(self, car_id: str) -> None:
        self.__reserved_lane_change_segments[car_id] = None


    def update_car_reservation_begin(self, car_id: str, index: int, begin: int) -> None:
        self.__car_reservation_store.update_begin(car_id, index, begin)

    def update_car_reservation_end(self, car_id: str, index: int, end: int) -> None:
        self.__car_reservation_store.update_end(car_id, index, end)

    def update_car_reservation_turn(self, car_id: str, index: int, turn: bool) -> None:
        self.__car_reservation_store.update_turn(car_id, index, turn)


    def iterate_car_reservations(self, car_id: str) -> List[SegmentInfo]:
        return self.__car_reservation_store.iterate(car_id)
    

    def reset(self) -> None:
        self.__car_reservation_store.reset()
        self.__segment_occupancy_tracker.reset()
        self.__reserved_lane_change_segments.clear()