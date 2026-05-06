import pyglet
import time
from copy import deepcopy

from typing import Dict, List, Tuple
from mlsl_simulation.game_model.road_network.road_network import Road
from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.car_types import CarType
from mlsl_simulation.constants import TIME_PER_FRAME
from mlsl_simulation.gui.pyglet_gui import GameWindow


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


    def set_map(self, roads: List[Road]) -> None:
        self.map = roads.copy()


    def set_action_history_dict(self, action_history_dict: Dict) -> None:
        self.action_history_dict = action_history_dict


    def add_taken_action(self, car: Car, action: Tuple[int, int]) -> None:
        self.action_history_dict.get(self._car_entry_key(car.type, car.name)).append(action)
        self.action_length += 1


    def _create_new_car_entry(self, car_type: CarType, car_name: str) -> None:
        self.action_history_dict[self._car_entry_key(car_type, car_name)] = list()


    def _car_entry_key(self, car_type: CarType, car_name: str) -> str:
        return car_type.name + ":" + car_name
    

    def history_playback(self, show_reservations: bool) -> None:
        for car in self.list_of_cars:
            car.reset()
            print(type(car))

        self.game_window = GameWindow(cars=self.list_of_cars, roads=self.map, show_reservations=show_reservations)

        # for road in self.map:
        #     for lane in road.left_lanes + road.right_lanes:
        #         for segment in lane.segments:
        #             print(segment.cars)
        #             segment.cars = []

        for i in range(len(list(self.action_history_dict.values())[0])):
            for car in self.list_of_cars:
                acceleration, lane_change = self.action_history_dict.get(self._car_entry_key(car.type, car.name))[i]

                car.change_speed(acceleration)
                car.change_lane(lane_change)
                car.move()

                self._render_frame()
                time.sleep(1.0 / TIME_PER_FRAME)


    def _render_frame(self):
        self.game_window.dispatch_events()
        self.game_window.on_draw()
        pyglet.clock.tick()
        self.game_window.flip()


    def reset_history(self) -> None:
        self.map.clear()
        self.list_of_cars.clear()
        self.action_history_dict.clear()
        self.action_length = 0