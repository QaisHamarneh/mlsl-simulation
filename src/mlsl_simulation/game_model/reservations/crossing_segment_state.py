from typing import Dict

class CrossingSegmentState:
    def __init__(self) -> None:
        # Absolute simulation time (matches Car.time) at which each car expects to
        # finish traversing this crossing segment.
        self.__time_to_leave: Dict[str, int] = dict()


    def get_time_to_leave(self, car_id: str) -> int | None:
        return self.__time_to_leave.get(car_id, None)

    def add_time_to_leave(self, car_id: str, time: int) -> None:
        self.__time_to_leave[car_id] = time

    def pop_time_to_leave(self, car_id: str) -> int | None:
        return self.__time_to_leave.pop(car_id, None)

    def reset(self) -> None:
        self.__time_to_leave.clear()