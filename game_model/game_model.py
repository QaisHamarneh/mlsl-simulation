import random
from typing import Optional, Tuple, List

from game_model.car import Car
from game_model.road_network import Goal, Road, CrossingSegment, LaneSegment, Problem, clock_wise, Point
from game_model.helper_functions import create_random_car, overlap, create_segments, reached_goal, collision_check
from game_model.constants import *


class TrafficEnv:
    """
    A class to represent the traffic environment.

    Attributes:
        roads (List[Road]): List of roads in the environment.
        segments (List[Segment]): List of segments created from the roads.
        players (int): Number of players in the environment.
        cars (List[Car]): List of cars in the environment.
        n_actions (int): Number of possible actions.
        gui (Optional[GUI]): GUI for the environment.
        moved (bool): Flag to indicate if a car has moved.
        time (int): Current time in the environment.
        scores (List[int]): Scores of the players.
        goals (List[Goal]): Goals for the players.
        useless_iterations (List[int]): Count of useless iterations for each player.
    """

    def __init__(self, roads: List[Road], players: int, cars: Optional[List[Car]] = None, goals: Optional[List[Goal]] = None):
        """
        Initialize the TrafficEnv.

        Args:
            roads (List[Road]): List of roads in the environment.
            players (int): Number of players in the environment.
            cars (Optional[List[Car]]): List of cars in the environment.
            goals (Optional[List[Goal]]): List of goals for the players.
        """
        super().__init__()
        self.useless_iterations = None
        self.goals = None
        self.second_goals = None
        self.scores = None
        self.roads = roads
        self.segments = create_segments(roads)
        self.players = players

        self.cars = cars
        self.n_actions = N_ACTIONS
        # init display
        self.moved = True
        
        self.time = 0

        self.crashes = 0

        if cars is None or goals is None:
            self.reset()

    def reset(self) -> None:
        """
        Reset the environment to its initial state.
        """
        self.scores: list[int] = [0] * self.players
        self.goals: list[Goal] = [None] * self.players
        self.second_goals: list[Goal] = [None] * self.players
        self.useless_iterations: list[int] = [0] * self.players
        self.cars = []
        for i in range(self.players):
            self.cars.append(create_random_car(self.segments, self.cars))
        for i in range(self.players):
            self._place_goal(i)
        for i in range(self.players):
            self.cars[i].goal = self.goals[i]
            self.cars[i].second_goal = self.second_goals[i]
        self.time = 0

    def _place_goal(self, player: int) -> None:
        """
        Place a goal for the specified player.

        Args:
            player (int): The index of the player.
        """
        self.useless_iterations[player] = 0

        if self.goals[player] is None and self.second_goals[player] is None:
            road = random.choice(self.roads)
            lane = random.choice(road.right_lanes + road.left_lanes)
            lane_segment = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
            roads = self.roads.copy()
            roads.remove(road)
            road = random.choice(roads)
            lane = random.choice(road.right_lanes + road.left_lanes)
            lane_segment_second = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
            self.goals[player] = Goal(lane_segment, self.cars[player].color)
            self.second_goals[player] = Goal(lane_segment_second, self.cars[player].color)
        else:
            roads_copy = self.roads.copy()
            #remove the road used by the first goal
            roads_copy.remove(self.goals[player].lane_segment.road)
            road = random.choice(roads_copy)
            lane = random.choice(road.right_lanes + road.left_lanes)
            lane_segment = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
            self.goals[player].lane_segment = self.second_goals[player].lane_segment
            self.second_goals[player].lane_segment = lane_segment
            self.goals[player].update_position()
            self.second_goals[player].update_position()

    def play_step(self, player: int, action: Tuple[int, int]) -> Tuple[bool, int]:
        """
        Execute a step in the environment for the specified player.

        Args:
            player (int): The index of the player.
            action (Tuple[int, int]): The action to be executed.

        Returns:
            Tuple[bool, int]: A tuple containing a boolean indicating if the game is over and the player's score.
        """

        self.useless_iterations[player] += 1
        car = self.cars[player]
        game_over = False

        # Execute selected action
        moved = self._move(player, action)  # update the head

        #increment time
        self.time += 1

        # Check if the action was possible
        if isinstance(moved, Problem):
            game_over = True
            car.dead = True
            return game_over, self.scores[player]

        # Crash detection:
        for other_car in self.cars:
            if other_car != car:
                # if overlap(car.pos, car.w, car.h,
                #            other_car.pos, other_car.w, other_car.h):
                if collision_check(car, other_car):
                    self.crashes += 1
                    print("___________________________________________________________________________")
                    print(f"Frame = {self.time // len(self.cars)},  Crash: {self.crashes}")
                    print(f"First car {car.name} loc {car.loc} speed {car.speed}")
                    for seg in car.res:
                        print(seg)
                    print(f"Second car {other_car.name} loc {other_car.loc} speed {other_car.speed}")
                    for seg in other_car.res:
                        print(seg)
                    print("___________________________________________________________________________")
                    game_over = True
                    car.dead = True
                    return game_over, self.scores[player]

        # Place new goal if the goal is reached
        if reached_goal(car, self.goals[player]):
            self.scores[player] += 1
            self._place_goal(player)

        # Player won!
        if self.scores[player] > 100:
            game_over = True
            car.dead = True
            return game_over, self.scores[player]

        # 7. return game over and score
        return game_over, self.scores[player]

    def _move(self, player: int, action: Tuple[int, int]) -> bool:
        """
        Move the car of the specified player based on the action.

        Args:
            player (int): The index of the player.
            action (Tuple[int, int]): The action to be executed.

        Returns:
            bool: True if the action was successful, False otherwise.
        """
        car = self.cars[player]
        acceleration, lane_change = action
        car.change_speed(acceleration)

        action_worked = True
        if lane_change != 0:
            action_worked = action_worked and car.change_lane(lane_change)

        action_worked = car.move() and action_worked
        return action_worked


    def is_collision(self, player: int, pt: Optional[Point] = None) -> bool:
        """
        Check if the car of the given player is in collision with other cars.

        Args:
            player (int): The index of the player whose car is being checked.
            pt (Optional[Point]): The point to check for collision. If None, the car's current position is used.

        Returns:
            bool: True if there is a collision, False otherwise.
        """
        car = self.cars[player]
        if pt is None:
            pt = self.cars[player].pos
        if pt.x > WINDOW_WIDTH - 1 or pt.x < 0 or pt.y > WINDOW_HEIGHT - 1 or pt.y < 0:
            return True
        if any([overlap(pt, car.w, car.h, self.cars[i].pos, self.cars[i].w, self.cars[i].h) for i in range(self.players) if
                i != player]):
            return True
        return False

