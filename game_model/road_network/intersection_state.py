from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass
class IntersectionState:
    __priority: Dict[int, int] = field(default_factory=dict) # first int is the id of a car, second int is its priority


    def get_car_priority(self, car_id: str) -> int:
        return self.__priority.get(car_id, None)
    

    def add_car_priority(self, car_id: str, time: int) -> None:
        self.__priority.setdefault(car_id, time)


    def remove_car_priority(self, car_id: str) -> int:
        self.__priority.pop(car_id, None) 


    def iterate_priority_items(self) -> Tuple[Tuple[int, int], ...]:
        return tuple(self.__priority.items())
    

    def reset(self) -> None:
        self.__priority.clear()