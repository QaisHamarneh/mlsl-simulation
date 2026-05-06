

import random
from typing import List

from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.car_types import CarType
from mlsl_simulation.constants import BLOCK_SIZE
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from mlsl_simulation.game_model.road_network.road_network import Color, Goal, LaneSegment, Road, Segment
from mlsl_simulation.gui.colors import colors
from mlsl_simulation.gui.selected_colors import selected_colors

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
    name = ""
    color = (0, 0, 0)
    for c in selected_colors:
        if not any([car.name == c for car in cars]):
            name = c
            color = selected_colors[name]
    if name == "":
        for c in colors:
            if not any([car.name == c for car in cars]):
                name = c
                color = colors[name]
                
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

    max_speed = random.randint(BLOCK_SIZE // 4, BLOCK_SIZE // 3)
    speed = random.randint(BLOCK_SIZE // 10, max_speed)

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


def create_goal(color: Color, car_segment:LaneSegment, roads: List[Road], first_goal: Goal | None = None) -> Goal:
    """
    Place a goal for the specified car.

    Args:
        car (Car): The car.
    """

    if first_goal is None:
        road = random.choice(roads)
        lane = random.choice(road.right_lanes + road.left_lanes)
        segment = random.choice([ls for ls in lane.segments if isinstance(ls, LaneSegment) and \
                                 (ls.num != car_segment.num or road != car_segment.lane.road)])
        return Goal(segment, color)
    else:
        road = random.choice([r for r in roads if r != first_goal.lane_segment.lane.road])
        lane = random.choice(road.right_lanes + road.left_lanes)
        segment = random.choice([ls for ls in lane.segments if isinstance(ls, LaneSegment) and \
                                 (ls.num != car_segment.num or road != car_segment.lane.road) and \
                                 (ls.num != first_goal.lane_segment.num)])
        return Goal(segment, color)