from typing import Dict, List, Tuple

class IntersectionState:
    def __init__(self):
        self.__priority: Dict[str, int] = dict() # first str is the id of a car, second int is its priority


    def get_car_priority(self, car_id: str) -> None | int:
        return self.__priority.get(car_id, None)
    

    def add_car_priority(self, car_id: str, time: int) -> None:
        self.__priority.setdefault(car_id, time)


    def pop_car_priority(self, car_id: str) -> None | int:
        return self.__priority.pop(car_id, None) 


    def get_priority_items(self) -> List[Tuple[str, int]]:
        return list(self.__priority.items())
    

    def reset(self) -> None:
        self.__priority.clear()