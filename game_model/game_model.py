import random
from typing import Optional, Tuple, List, Dict

from controller.astar_car_controller import AstarCarController
from game_model.car import Car
from game_model.road_network import Direction, Goal, Road, CrossingSegment, LaneSegment, Problem, clock_wise, Point
from game_model.helper_functions import create_random_car, overlap, reached_goal, collision_check
from game_model.create_game import create_segments
from game_model.constants import *


class TrafficEnv:
    """
    A class to represent the traffic environment.

    Attributes:
        roads (List[Road]): List of roads in the environment.
        segments (List[Segment]): List of segments created from the roads.
        players (int): Number of players in the environment.
        cars_controllers (Dict[Car, Optional[AstarCarController]]): Dictionary of cars and corresponding controllers.
        n_actions (int): Number of possible actions.
        moved (bool): Flag to indicate if a car has moved.
        time (int): Current time in the environment.
    """

    def __init__(self, roads: List[Road], players: int, cars: Optional[List[Car]] = None, controllers: Optional[List[AstarCarController]] = None):
        """
        Initialize the TrafficEnv.

        Args:
            roads (List[Road]): List of roads in the environment.
            players (int): Number of players in the environment.
            cars (Optional[List[Car]]): List of cars in the environment.
            controllers (Optional[List[AstarCarController]]): List of car controllers.
        """
        super().__init__()
        self.scores = None
        self.roads = roads
        self.segments, self.intersections = create_segments(roads)
        self.players = players
        self.cars = cars
        self.controllers = controllers
        self.n_actions = N_ACTIONS
        # init display
        self.moved = True
        
        self.time = 0

        self.total_crashes = 0
        self.crashes: dict = {}
        self.crashes[Direction.RIGHT] = 0
        self.crashes[Direction.UP] = 0
        self.crashes[Direction.LEFT] = 0
        self.crashes[Direction.DOWN] = 0

        if cars is None or controllers is None:
            self.reset()

    def reset(self) -> None:
        """
        Reset the environment to its initial state.
        """
        self.cars: List[Car] = []
        self.controllers: List[AstarCarController] = []
        for i in range(self.players):
            self.cars.append(create_random_car(self.segments, self.cars))
        for car in self.cars:
            self._place_goals(car)
            self.controllers.append(AstarCarController(car, car.goal))
        self.time = 0

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
            roads = self.roads.copy()
            roads.remove(road)
            road = random.choice(roads)
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

    def play_step(self) -> bool:
        """
        Execute a step in the environment for each car.

        Returns:
            bool: A boolean indicating if the game is over.
        """
        game_over = True

        for controller in self.controllers:
            car = controller.car
            if car.dead:
                continue

            action = controller.get_action()
            moved = self._move(car, action)  # update the head

            # increment time
            self.time += 1

            # Check if the action was possible
            if isinstance(moved, Problem):
                car.dead = True
                continue

            # Crash detection:
            for other_car in self.cars:
                if other_car != car:
                    # if overlap(car.pos, car.w, car.h,
                    #            other_car.pos, other_car.w, other_car.h):
                    if collision_check(car, other_car):
                        self.total_crashes += 1
                        self.crashes[car.direction] += 1
                        print("___________________________________________________________________________")
                        print(f"Frame = {self.time // len(self.cars)},  Crash: {self.total_crashes}")
                        print(f"Direction = {car.direction},  Crash: {self.crashes[car.direction]}")
                        print(f"First car {car.name} loc {car.loc} speed {car.speed}")
                        for seg in car.res:
                            print(seg)
                        print(f"Second car {other_car.name} loc {other_car.loc} speed {other_car.speed}")
                        for seg in other_car.res:
                            print(seg)
                        print("___________________________________________________________________________")
                        car.dead = True
                        other_car.dead = True
                        continue

            # Place new goal if the goal is reached
            if reached_goal(car, car.goal):
                car.score += 1
                self._place_goals(car)

            # Player won!
            if car.score > WINNING_SCORE:
                # car.dead = True
                continue

            game_over = False

        # return game over
        return game_over

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
            action_worked = action_worked and car.change_lane(lane_change)

        action_worked = car.move() and action_worked
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

