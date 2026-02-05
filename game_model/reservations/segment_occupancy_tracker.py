from typing import Dict, List
from game_model.road_network import Segment

class SegmentOccupancyTracker:
    def __init__(self):
        self.__segment_occupancy_dict: Dict[Segment, List[int]] = {}


    def add_segment_occupancy(self, segment: Segment, car_id: str) -> None:
        if segment not in self.__segment_occupancy_dict:
            self.__segment_occupancy_dict[segment] = [car_id]
        else:
            self.__segment_occupancy_dict[segment].append(car_id)


    def remove_segment_occupancy(self, segment: Segment, car_id: str) -> List[int]:
        assert segment in self.__segment_occupancy_dict and car_id in self.__segment_occupancy_dict[segment]
        self.__segment_occupancy_dict[segment].remove(car_id)
        return self.__segment_occupancy_dict[segment]


    def get_cars_on_segment(self, segment: Segment) -> List[int]:
        if segment not in self.__segment_occupancy_dict:
            self.__segment_occupancy_dict[segment] = []
        return self.__segment_occupancy_dict[segment]
    

    def reset(self) -> None:
        self.__segment_occupancy_dict.clear()