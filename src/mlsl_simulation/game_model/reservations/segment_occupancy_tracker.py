from typing import Dict, List
from mlsl_simulation.game_model.road_network.road_network import Segment

class SegmentOccupancyTracker:
    def __init__(self):
        self.__segment_occupancy_dict: Dict[Segment, List[str]] = dict()


    def add_segment_occupancy(self, segment: Segment, car_id: str) -> None:
        if segment not in self.__segment_occupancy_dict:
            self.__segment_occupancy_dict[segment] = [car_id]
        else:
            self.__segment_occupancy_dict[segment].append(car_id)


    def remove_segment_occupancy(self, segment: Segment, car_id: str) -> None:
        self.__segment_occupancy_dict[segment].remove(car_id)


    def get_cars_on_segment(self, segment: Segment) -> List[str]:
        if segment not in self.__segment_occupancy_dict:
            self.__segment_occupancy_dict[segment] = []
        return list(self.__segment_occupancy_dict[segment])
    

    def reset(self) -> None:
        self.__segment_occupancy_dict.clear()