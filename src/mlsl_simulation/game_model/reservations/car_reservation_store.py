from typing import Dict, List, Tuple
from mlsl_simulation.game_model.road_network.road_network import SegmentInfo

class CarReservationStore:
    def __init__(self):
        self.__reservation_dict: Dict[str, List[SegmentInfo]] = {}

    def add_reservation(self, car_id: str, segment_info: SegmentInfo) -> None:
        if not car_id in self.__reservation_dict:
            self.__reservation_dict[car_id] = [segment_info]
        else:
            self.__reservation_dict[car_id].append(segment_info)

    def pop_reservation(self, car_id: str, index: int) -> SegmentInfo:
        return self.__reservation_dict[car_id].pop(index)

    def get_reservation(self, car_id: str, index: int) -> SegmentInfo:
        return self.__reservation_dict[car_id][index]

    def update_begin(self, car_id: str, index: int, begin: int) -> None:
        self.__reservation_dict[car_id][index].begin = begin

    def update_end(self, car_id: str, index: int, end: int) -> None:
        self.__reservation_dict[car_id][index].end = end

    def update_turn(self, car_id: str, index: int, turn: bool) -> None:
        self.__reservation_dict[car_id][index].turn = turn

    def iterate(self, car_id: str) -> List[SegmentInfo]:
        return self.__reservation_dict[car_id]
    
    def reset(self) -> None:
        self.__reservation_dict.clear()