from typing import Dict, List, Tuple
from game_model.road_network import Road
from game_model.car import Car
from game_model.car_types import CarType
from gui.pyglet_gui import GameWindow


class GameHistory():
    def __init__(self):
        self.map: List[Road] = list()
        self.list_of_cars: List[Car] = list()
        self.action_history_dict: Dict[str, List[Tuple[int, int]]] = dict()
        self.action_length = 0


    def set_list_of_cars(self, list_of_cars: List[Car]) -> None:
        self.list_of_cars = list_of_cars.copy()

        for car in self.list_of_cars:
            self._create_new_car_entry(car.type, car.name)


    def set_map(self, segments: List[Road]) -> None:
        self.map = segments.copy()


    def add_taken_action(self, car: Car, action: Tuple[int, int]) -> None:
        self.action_history_dict.get(self._car_entry_key(car.type, car.name)).append(action)
        self.action_length += 1


    def _create_new_car_entry(self, car_type: CarType, car_name: str) -> None:
        self.action_history_dict[self._car_entry_key(car_type, car_name)] = list()


    def _car_entry_key(self, car_type: CarType, car_name: str) -> str:
        return car_type.name + ":" + car_name
    

    def history_playback(self, show_reservations: bool) -> None:
        window = GameWindow(cars=self.list_of_cars, roads=self.map, show_reservations=show_reservations)
        
        for i in range(self.action_length / len(self.list_of_cars)):
            for car in self.list_of_cars:
                acceleration, lane_change = self.action_history_dict.get(car.name)[i]

                car.change_speed(acceleration)
                car.change_lane(lane_change)

                window.on_draw()


    def reset_history(self) -> None:
        self.map = list()
        self.list_of_cars = list()
        self.action_history_dict = dict()
        self.action_length = 0