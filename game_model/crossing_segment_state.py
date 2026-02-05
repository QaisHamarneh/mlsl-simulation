from dataclasses import dataclass, field
from typing import Dict

@dataclass
class CrossingSegmentState:
    __time_to_leave: Dict[int, int] = field(default_factory=dict) # first int is the id of a car, second int is its time to leave


    def get_time_to_leave(self, car_id: str) -> int:
        return self.__time_to_leave.get(car_id, None)


    def add_time_to_leave(self, car_id: str, time: int) -> None:
        self.__time_to_leave.setdefault(car_id, time)


    def remove_time_to_leave(self, car_id: str) -> int:
        self.__time_to_leave.pop(car_id, None)


    def reset(self) -> None:
        self.__time_to_leave.clear()