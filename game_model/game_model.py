import random
import logging

from typing import Optional, Tuple, List
from controller.astar_car_controller import AstarCarController
from game_model.car import Car
from game_model.car_types import CarType
from game_model.road_network.road_network import Direction, Goal, Road, LaneSegment, Problem, Point
from game_model.helper_functions import create_random_car, overlap, reached_goal, collision_check
from game_model.create_game import create_segments
from game_model.constants import *
from game_model.reservations.reservation_management import ReservationManagement
from game_model.game_history import GameHistory
from reinforcement_learning.rl_modes import RLMode

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

        self.cars = []
        self.npc_cars = []
        self.agent_car = None
        self.controllers = []

        self.reservation_management.reset() 
        self.game_history.reset_history()

        if self.agent:
            self.agent_car = create_random_car(self.segments, self.npc_cars, CarType.AGENT, self.reservation_management)
            self._place_goals(self.agent_car)
            self.cars.append(self.agent_car)

        for i in range(self.npcs):
            car = create_random_car(self.segments, self.cars, CarType.NPC, self.reservation_management)
            self.cars.append(car)
            self.npc_cars.append(car)
        for car in self.npc_cars:
            self._place_goals(car)
            self.controllers.append(AstarCarController(car, car.goal, self.reservation_management))

        self.game_history.set_list_of_cars(self.cars)
        self.game_history.set_map(self.roads)

        self.total_crashes = 0
        self.crashes = {Direction.RIGHT: 0, Direction.UP: 0, Direction.LEFT: 0, Direction.DOWN: 0}

    def _place_goals(self, car: Car) -> None:
        """
        Place a goal for the specified car.

        Args:
            car (Car): The car.
        """

        if car.goal is None and car.second_goal is None:
            road = random.choice(self.roads)
            lane = random.choice(road.right_lanes + road.left_lanes)
            lane_segment = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
            roads_copy = self.roads.copy()
            roads_copy.remove(road)
            road = random.choice(roads_copy)
            lane = random.choice(road.right_lanes + road.left_lanes)
            lane_segment_second = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
            car.goal = Goal(lane_segment, car.color)
            car.second_goal = Goal(lane_segment_second, car.color)
        else:
            roads_copy = self.roads.copy()
            #remove the road used by the first goal
            roads_copy.remove(car.goal.lane_segment.road)
            road = random.choice(roads_copy)
            lane = random.choice(road.right_lanes + road.left_lanes)
            lane_segment = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
            car.goal.lane_segment = car.second_goal.lane_segment
            car.second_goal.lane_segment = lane_segment
            car.goal.update_position()
            car.second_goal.update_position()

    def play_step(self, action: None | Tuple[int, int] = None) -> None | str:
        """
        Execute a step in the environment for each car.

        Returns:
            bool: A boolean indicating if the game is over.
        """
        game_over = []

        if self.agent:
            game_over.append(
                self._execute_action(car=self.agent_car, action=action) if not self.agent_car.get_death_status() else True
            )
            self.game_history.add_taken_action(self.agent_car, action)

        for controller in self.controllers:
            car = controller.car
            npc_action = controller.get_action(self.cars)
            game_over.append(
                self._execute_action(car=car, action=npc_action) if not car.get_death_status() else True
            )
            self.game_history.add_taken_action(car, npc_action)

        deadlock = [True if car.speed == 0 else False for car in self.cars]
        if not all(game_over) and all(deadlock):
            # log_msg = "Deadlock between all cars:\n"
            # log_msg += f"Frame: {self.time // len(self.cars)}\n"
            # logging.warning(log_msg)
            return 'deadlock'
        
        if all(game_over):
            return 'game_over'
        
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
                    # log_msg = (
                    #     f"Frame = {self.time // len(self.cars)},  Crash: {self.total_crashes}\n"
                    #     f"First car {car.type}:{car.name} Second car {other_car.type}:{other_car.name}\n"
                    # )
                    # logging.warning(log_msg)
                    car.handle_car_death(self.reservation_management)
                    other_car.handle_car_death(self.reservation_management)
                    return True

        # Place new goal if the goal is reached
        if reached_goal(car, car.goal, self.reservation_management):
            car.score += 1
            self._place_goals(car)

        # Player won!
        return car.score > WINNING_SCORE

    def _move(self, car: Car, action: Tuple[int, int]) -> bool:
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


    def is_collision(self, car: Car, pt: Optional[Point] = None) -> bool:
        """
        Check if the given car is in collision with other cars.

        Args:
            car (Car): The car which is being checked.
            pt (Optional[Point]): The point to check for collision. If None, the car's current position is used.

        Returns:
            bool: True if there is a collision, False otherwise.
        """
        if pt is None:
            pt = car.pos
        if pt.x > WINDOW_WIDTH - 1 or pt.x < 0 or pt.y > WINDOW_HEIGHT - 1 or pt.y < 0:
            return True
        if any([overlap(pt, car.w, car.h, other_car.pos, other_car.w, other_car.h) for other_car in self.cars if
                car != other_car]):
            return True
        return False
    
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

