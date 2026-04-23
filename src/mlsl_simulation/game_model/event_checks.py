import math

from mlsl_simulation.game_model.car import Car
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from mlsl_simulation.game_model.road_network.road_network import Goal


def reached_goal(car: Car, reservation_management: ReservationManagement) -> bool:
    """
    Check if a car has reached its goal.

    Args:
        car (Car): The car to check.
        goal (Goal): The goal to check against.

    Returns:
        bool: True if the car has reached the goal, False otherwise.
    """
    
    if reservation_management.get_car_reservation(car.id, 0).segment == car.goal.lane_segment:
        if math.dist(car.get_center(reservation_management), [car.goal.pos.x, car.goal.pos.y]) < car.size // 3:
            return True
    return False


    
def collision_check(car1: Car, car2:Car, reservation_managemnent: ReservationManagement) -> bool:
    """
    Check if a car is in collision with any other car.

    Args:
        car (Car): The car to check.

    Returns:
        bool: True if there is a collision, False otherwise.
    """
    car1_segments = car1.get_size_segments(reservation_managemnent)
    car2_segments = car2.get_size_segments(reservation_managemnent)
    for segment_car1 in car1_segments:
        segment_car2 = next((seg for seg in car2_segments if segment_car1.segment == seg.segment), None)
        if segment_car2 is not None:
            begin1 = abs(segment_car1.begin)
            end1 = abs(segment_car1.end)
            begin2 = abs(segment_car2.begin)
            end2 = abs(segment_car2.end)

            if begin2 < begin1 < end2:
                return True
            elif begin2 < end1 < end2:
                return True
            
            elif begin1 < begin2 < end1:
                return True
            elif begin1 < end2 < end1:
                return True

    return False