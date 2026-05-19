

import random
from typing import List, Tuple

from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.car_types import CarType
from mlsl_simulation.constants import BLOCK_SIZE, CROSSING_MAX_SPEED, LANE_MAX_SPEED, MINIMAL_SPEED
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from mlsl_simulation.game_model.road_network.road_network import Color, Goal, LaneSegment, Road, Segment
from mlsl_simulation.gui.colors import colors
from mlsl_simulation.gui.selected_colors import selected_colors
from mlsl_simulation.scenario_parser.predefined_cars import CarSpec, GoalSpec, resolve_segment


def _pick_name_color(cars: List['Car']) -> Tuple[str, Color]:
    for c in selected_colors:
        if not any(car.name == c for car in cars):
            return c, selected_colors[c]
    for c in colors:
        if not any(car.name == c for car in cars):
            return c, colors[c]
    return "", (0, 0, 0)

def create_random_car(roads: List[Road], cars: List['Car'], car_type: CarType, reservation_management: ReservationManagement) -> 'Car':
    """
    Create a random car that does not overlap with existing cars.
    Randomly selects a color, lane segment, speed, size. The location is set to 0.

    Args:
        segments (List[Segment]): The list of segments to place the car in.
        cars (List[Car]): The list of existing cars.

    Returns:
        Car: The randomly created car.
    """
    name, color = _pick_name_color(cars)

    empty_lane_segments = [
        ls
        for road in roads
        for lane in road.right_lanes + road.left_lanes
        for ls in lane.segments
        if isinstance(ls, LaneSegment)and not any(
                ls == reservation_management.get_car_reservation(car.id, 0).segment
                for car in cars
            )
    ]

    lane_segment = random.choice(empty_lane_segments)

    first_goal = create_goal(color, lane_segment, roads)
    second_goal = create_goal(color, lane_segment, roads, first_goal)

    if len(cars) % 2 == 0:
        max_speed = random.randint(CROSSING_MAX_SPEED, LANE_MAX_SPEED)
    else:
        max_speed = random.randint(MINIMAL_SPEED, CROSSING_MAX_SPEED)
    speed = random.randint(1, max_speed)

    size = random.randint(BLOCK_SIZE // 2, 3 * BLOCK_SIZE // 2)
    loc = 0

    return Car(name=name,
               type=car_type,
               loc=loc,
               segment=lane_segment,
               speed=speed,
               size=size,
               color=color,
               max_speed=max_speed,
               first_goal=first_goal,
               second_goal=second_goal,
               reservation_management=reservation_management)


def create_predefined_car(spec: CarSpec,
                          roads: List[Road],
                          cars: List['Car'],
                          reservation_management: ReservationManagement) -> 'Car':
    """
    Create a car from a predefined spec, falling back to the random logic
    used by `create_random_car` for any field left as None on the spec.
    """
    if spec.start is not None:
        lane_segment = resolve_segment(roads, spec.start)
        occupied = any(
            lane_segment == reservation_management.get_car_reservation(car.id, 0).segment
            for car in cars
        )
        if occupied:
            raise ValueError(
                f"Predefined start segment {spec.start} is already occupied by another car"
            )
    else:
        empty_lane_segments = [
            ls
            for road in roads
            for lane in road.right_lanes + road.left_lanes
            for ls in lane.segments
            if isinstance(ls, LaneSegment) and not any(
                ls == reservation_management.get_car_reservation(car.id, 0).segment
                for car in cars
            )
        ]
        lane_segment = random.choice(empty_lane_segments)

    if spec.name is not None and spec.color is not None:
        name, color = spec.name, spec.color
    else:
        auto_name, auto_color = _pick_name_color(cars)
        name = spec.name if spec.name is not None else auto_name
        color = spec.color if spec.color is not None else auto_color

    if spec.first_goal is not None:
        first_goal_seg = resolve_segment(roads, spec.first_goal.segment)
        first_goal = Goal(first_goal_seg, color, loc=spec.first_goal.loc)
    else:
        first_goal = create_goal(color, lane_segment, roads)

    if spec.second_goal is not None:
        second_goal_seg = resolve_segment(roads, spec.second_goal.segment)
        second_goal = Goal(second_goal_seg, color, loc=spec.second_goal.loc)
    else:
        second_goal = create_goal(color, lane_segment, roads, first_goal)

    if spec.max_speed is not None:
        max_speed = spec.max_speed
    elif len(cars) % 2 == 0:
        max_speed = random.randint(CROSSING_MAX_SPEED, LANE_MAX_SPEED)
    else:
        max_speed = random.randint(MINIMAL_SPEED, CROSSING_MAX_SPEED)

    speed = spec.speed if spec.speed is not None else random.randint(1, max_speed)
    size = spec.size if spec.size is not None else random.randint(BLOCK_SIZE // 2, 3 * BLOCK_SIZE // 2)
    loc = spec.loc if spec.loc is not None else 0

    return Car(name=name,
               type=spec.type,
               loc=loc,
               segment=lane_segment,
               speed=speed,
               size=size,
               color=color,
               max_speed=max_speed,
               first_goal=first_goal,
               second_goal=second_goal,
               reservation_management=reservation_management)


def create_goal(color: Color, car_segment:LaneSegment, roads: List[Road], first_goal: Goal | None = None) -> Goal:
    """
    Place a goal for the specified car.

    Args:
        car (Car): The car.
    """

    empty_lane_segments = [
        ls
        for road in roads
        for lane in road.right_lanes + road.left_lanes
        for ls in lane.segments
        if isinstance(ls, LaneSegment) and \
            not (road == car_segment.lane.road and lane.direction == car_segment.lane.direction and ls.num == car_segment.num) and \
            (first_goal is None or not (road == first_goal.lane_segment.lane.road and lane.direction == first_goal.lane_segment.lane.direction and ls.num == first_goal.lane_segment.num))
    ]
    lane_segment = random.choice(empty_lane_segments)
    return Goal(lane_segment, color)