import random

from game_model.car import Car
from game_model.road_network import Goal, Road, CrossingSegment, LaneSegment, Problem, clock_wise
from game_model.helper_functions import create_random_car, overlap, create_segments, reached_goal, collision_check
from game_model.constants import *


class TrafficEnv:

    def __init__(self, roads: list[Road], players: int, cars: list[Car] = None, goals: list[Goal] = None):
        super().__init__()
        self.roads = roads
        self.segments = create_segments(roads)
        self.players = players

        self.cars = cars
        self.n_actions = 3

        # init display
        self.gui = None
        self.moved = True
        self.time = 0

        if cars is None or goals is None:
            self.reset()

    def reset(self):
        # init game state
        self.scores: list[int] = [0] * self.players
        self.goals: list[Goal] = [None] * self.players
        self.useless_iterations: list[int] = [0] * self.players
        self.cars = []
        for i in range(self.players):
            self.cars.append(create_random_car(self.segments, self.cars))
        for i in range(self.players):
            self._place_goal(i)
        for i in range(self.players):
            self.cars[i].goal = self.goals[i]
        self.time = 0

    def _place_goal(self, player):
        self.useless_iterations[player] = 0

        road = random.choice(self.roads)
        lane = random.choice(road.right_lanes + road.left_lanes)
        lane_segment = random.choice([seg for seg in lane.segments if isinstance(seg, LaneSegment)])
        if self.goals[player] is None:
            self.goals[player] = Goal(lane_segment, self.cars[player].color)
        else:
            self.goals[player].lane_segment = lane_segment
            self.goals[player].update_position()

    def play_step(self, player, action):
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
            print(f"Illegal Action: {car.color} {car.pos}")
            print(moved)
            return game_over, self.scores[player]

        # Crash detection:
        for other_car in self.cars:
            if other_car != car:
                # if overlap(car.pos, car.w, car.h,
                #            other_car.pos, other_car.w, other_car.h):
                if collision_check(car):
                    print("Crash:")
                    print(f"First car {car.name} loc {car.loc} speed {car.speed}")
                    for seg in car.res:
                        print(f"{seg['seg']} {seg['begin']} {seg['end']}")
                    print(f"Second car {other_car.name} loc {other_car.loc} speed {other_car.speed}")
                    for seg in other_car.res:
                        print(f"{seg['seg']} {seg['begin']} {seg['end']}")
                    print("___________________________________________________________________________")
                    game_over = True
                    car.dead = True
                    return game_over, self.scores[player]

        # Place new goal if the goal is reached
        if reached_goal(car, self.goals[player]):
            self.scores[player] += 1
            self._place_goal(player)
            # print(f"Player {player}: Score {self.scores[player]}")

        # Player won!
        if self.scores[player] > 100:
            game_over = True
            car.dead = True
            return game_over, self.scores[player]

        # 7. return game over and score
        return game_over, self.scores[player]

    def _move(self, player, action):
        # -1, 0, 1 just acceleration
        # 9, 11 turn and acceleration
        # 99, 101 turn and acceleration
        car = self.cars[player]
        idx = clock_wise.index(car.direction)
        match action:
            case -1:
                car.change_speed(-1)
            case 1:
                car.change_speed(1)
            case 9:
                car.change_speed(-1)
                next_idx = (idx + 1) % 4
                new_dir = clock_wise[next_idx]  # right turn r -> d -> l -> u ->
                action_worked = car.turn(new_dir)
                if not action_worked:
                    return action_worked
            case 11:
                car.change_speed(1)
                next_idx = (idx + 1) % 4
                new_dir = clock_wise[next_idx]  # right turn r -> d -> l -> u ->
                action_worked = car.turn(new_dir)
                if not action_worked:
                    return action_worked
            case 19:
                car.change_speed(-1)
                next_idx = (idx - 1) % 4
                new_dir = clock_wise[next_idx]  # left turn u -> l -> d -> r ->
                action_worked = car.turn(new_dir)
                if not action_worked:
                    return action_worked
            case 21:
                car.change_speed(1)
                next_idx = (idx - 1) % 4
                new_dir = clock_wise[next_idx]  # left turn u -> l -> d -> r ->
                action_worked = car.turn(new_dir)
                if not action_worked:
                    return action_worked
            case -99:
                car.change_speed(1)
                action_worked = car.change_lane(-1)
                if not action_worked:
                    return action_worked
            case -101:
                car.change_speed(-1)
                action_worked = car.change_lane(1)
                if not action_worked:
                    return action_worked
            case 99:
                car.change_speed(-1)
                action_worked = car.change_lane(-1)
                if not action_worked:
                    return action_worked
            case 101:
                car.change_speed(1)
                action_worked = car.change_lane(1)
                if not action_worked:
                    return action_worked

        action_worked = car.move()
        return action_worked

    def is_collision(self, player, pt=None) -> bool:
        car = self.cars[player]
        if pt is None:
            pt = self.cars[player].pos
        # hits boundary
        if pt.x > WINDOW_WIDTH - 1 or pt.x < 0 or pt.y > WINDOW_HEIGHT - 1 or pt.y < 0:
            return True
        # hits other cars
        if any([overlap(pt,
                        car.w,
                        car.h,
                        self.cars[i].pos,
                        self.cars[i].w,
                        self.cars[i].h)
                for i in range(self.players) if i != player]):
            return True
        return False
