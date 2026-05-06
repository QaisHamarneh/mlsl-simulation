import math
import random
import logging

from typing import Optional, Tuple, List
from mlsl_simulation.controller.astar_car_controller import AstarCarController
from mlsl_simulation.game_model.create_items.create_cars import create_goal, create_random_car
from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.car_types import CarType
from mlsl_simulation.game_model.event_checks import collision_check, reached_goal
from mlsl_simulation.game_model.road_network.road_network import Direction, Goal, Road, LaneSegment, Problem
from mlsl_simulation.game_model.create_items.create_segments import create_segments
from mlsl_simulation.constants import *
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from mlsl_simulation.game_model.game_history import GameHistory
from mlsl_simulation.reinforcement_learning.rl_modes import RLMode

class TrafficEnv:
    """
    A class to represent the traffic environment.

    Attributes:
        roads (List[Road]): List of roads in the environment.
        segments (List[Segment]): List of segments created from the roads.
        npcs (int): Number of npcs in the environment.
        agents (int): Number of ai controlled agents in the environment.
        cars_controllers (Dict[Car, Optional[AstarCarController]]): Dictionary of cars and corresponding controllers.
        moved (bool): Flag to indicate if a car has moved.
        time (int): Current time in the environment.
    """

    def __init__(self, 
                 roads: List[Road], 
                 players: int,
                 npc_cars: None | List[Car] = None, 
                 rl_mode: None | RLMode = None):
        """
        Initialize the TrafficEnv.

        Args:
            roads (List[Road]): List of roads in the environment.
            npcs (int): Number of npcs in the environment.
            cars (Optional[List[Car]]): List of cars in the environment.
            controllers (Optional[List[AstarCarController]]): List of car controllers.
        """
        super().__init__()
        self.roads = roads
        self.segments, self.intersections = create_segments(roads)
        self.npcs: int = players
        self.agent: bool = False if rl_mode is None else True

        # self.scores = None
        self.moved: bool = True
        self.time: int = 0

        self.cars: List[Car] = []
        self.npc_cars_init = npc_cars
        self.npc_cars: List[Car] = []
        self.agent_car: None | Car = None
        self.controllers: List[AstarCarController] = []

        self.total_crashes: int = 0
        self.crashes: dict = {}

        self.reservation_management: ReservationManagement = ReservationManagement()
        self.game_history: GameHistory = GameHistory()

        self.reset()

    def reset(self) -> None:
        """
        Reset the environment to its initial state.
        """
        for intersection in self.intersections:
            intersection.intersection_state.reset()
            for crossing_segment in intersection.segments:
                crossing_segment.crossing_segment_state.reset()

        # init display
        self.moved = True
        self.time = 0

        self.cars.clear()
        self.npc_cars.clear()
        self.agent_car = None
        self.controllers.clear()

        self.reservation_management.reset() 
        self.game_history.reset_history()

        if self.agent:
            self.agent_car = create_random_car(self.roads, self.npc_cars, CarType.AGENT, self.reservation_management)
            self.cars.append(self.agent_car)

        if self.npc_cars_init is None:
            for i in range(self.npcs):
                car = create_random_car(self.roads, self.cars, CarType.NPC, self.reservation_management)
                self.cars.append(car)
                self.npc_cars.append(car)
        else:
            self.npc_cars = self.npc_cars_init.copy()
        for car in self.npc_cars:
            self.controllers.append(AstarCarController(car, self.cars, self.reservation_management))

        self.game_history.set_list_of_cars(self.cars)
        self.game_history.set_map(self.roads)

        self.total_crashes = 0
        self.crashes = {Direction.RIGHT: 0, Direction.UP: 0, Direction.LEFT: 0, Direction.DOWN: 0}

    def play_step(self, action: None | Tuple[int, int] = None) -> None | str:
        """
        Execute a step in the environment for each car.

        Returns:
            bool: A boolean indicating if the game is over.
        """
        game_over = []

        if self.agent:
            if self.agent_car is not None and action is not None:
                game_over.append(
                    self._execute_action(car=self.agent_car, action=action) if not self.agent_car.get_death_status() else True
                )
                self.game_history.add_taken_action(self.agent_car, action)

        for controller in self.controllers:
            car = controller.car
            npc_action = controller.get_action()
            game_over.append(
                self._execute_action(car=car, action=npc_action) if not car.get_death_status() else True
            )
            self.game_history.add_taken_action(car, npc_action)

        deadlock = [True if car.speed == 0 else False for car in self.cars]
        if all(game_over):
            print("Game Over!")
            return 'game_over'
        if all(deadlock):
            print("Deadlock!")
            return 'deadlock'
        
        for controller in self.controllers:
            car = controller.car
            reservations = self.reservation_management.get_car_reservations(car.id)
            for i, res_seg in enumerate(reservations):
                issues = False
                if i == 0 and abs(res_seg.end) < res_seg.segment.length and len(reservations) > 1:
                    print(f"Issue 1: {car.name} - {res_seg.end} {res_seg.segment.length} - {len(reservations)}")
                    issues = True
                elif i > 0 and abs(res_seg.begin) > 0:
                    print(f"Issue 2: {car.name} - {i} - {res_seg.begin}")
                    issues = True
                if issues:
                    print("------------------")

        return None
    
    def _execute_action(self, car: Car, action: Tuple[int, int]) -> bool:
        """
        Execute an action for a car.

        Returns:
            bool: A boolean indicating if the game is over for this car.
        """
        # update the head
        moved = self._move(car, action)

        # increment time
        self.time += 1
        # Check if the action was possible
        if isinstance(moved, Problem):
            if car is self.agent_car:
                car.illegal_move = True
            else:
                car.handle_car_death(self.reservation_management)
                return True

        # Crash detection:
        for other_car in self.cars:
            if other_car != car:
                if collision_check(car, other_car, self.reservation_management):
                    self.total_crashes += 1
                    self.crashes[car.direction] += 1
                    car.handle_car_death(self.reservation_management)
                    other_car.handle_car_death(self.reservation_management)
                    print(f"Collision Detected! {car.name} Car with {other_car.name} Car!")
                    return True

        # Place new goal if the goal is reached
        if reached_goal(car, self.reservation_management):
            car.score += 1
            car.goal = car.second_goal
            car_segment = self.reservation_management.get_car_reservation(car.id, 0).segment
            car.second_goal = create_goal(car.color, car_segment, self.roads, car.goal)

        # Player won!
        return car.score > WINNING_SCORE

    def _move(self, car: Car, action: Tuple[int, int]) -> bool | Problem:
        """
        Move the car based on the action.

        Args:
            car (Car): The car to move.
            action (Tuple[int, int]): The action to be executed.

        Returns:
            bool: True if the action was successful, False otherwise.
        """
        acceleration, lane_change = action
        car.change_speed(acceleration)

        action_worked = True
        if lane_change != 0:
            action_worked = action_worked and car.change_lane(self.reservation_management, lane_change)

        action_worked = car.move(self.reservation_management) and action_worked

        return action_worked

    def current_state(self):
        print("---------------------")
        print("Game State:\n")
        game_over = True

        for car in self.cars:
            print(f"{car.type}: {car.name} | Score: {car.score} | Dead: {car.get_death_status()}")
            game_over = car.get_death_status() and game_over

        print(f"\nWinning Score -> {WINNING_SCORE}")
        print(f"Game Over -> {game_over}")
        print("---------------------\n")

