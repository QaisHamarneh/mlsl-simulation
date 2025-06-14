from math import gamma
from typing import List, Tuple, Optional

from controller.astar_car_controller import AstarCarController
from game_model.game_model import TrafficEnv
from game_model.road_network import LaneSegment, CrossingSegment


class SimulationTester:
    def __init__(self, game_model: TrafficEnv, debug_mode: List[str],
                 rate: int = 100) -> None:
        """
        Initialize the SimulationTester.

        Args:
            game_model (TrafficEnv): The game environment.
            debug_mode (List[str]): The list of debug modes to run.
            rate (int): The rate at which to run the debug modes.
        """

        self.game_model = game_model
        self.controllers = game_model.controllers

        self.modes = {
            "reserved_check": self.reserved_check,
            "reservation_check": self.reservation_check,
            "consistency_check": self.consistency_check,
            "priority_check": self.priority_check
        }

        self.debug_mode = debug_mode if "all" not in debug_mode else self.modes.keys()
        self.rate = rate

    def run(self) -> Optional[List[Tuple[bool, str]]]:
        """
        Run the selected debug modes every rate time steps.

        Returns:
            Optional[List[Tuple[bool, str]]]: The results of the debug modes, None if tests were not conducted on that frame.
        """
        if self.controllers[0].car.time % self.rate != 0:
            return None

        results = []

        for mode in self.debug_mode:
            results.append(self.modes[mode]())

        return results

    def reserved_check(self) -> Tuple[bool, str]:
        """
        Checks if the last segment of each car is a lane segment.
        Prints the number of cars that are not in a lane segment.

        Returns:
            bool: True if all cars are in a lane segment, False otherwise.
            str: The result string of the check.
        """
        not_in_lane = 0

        for controller in self.controllers:
            car = controller.car
            if not isinstance(car.res[-1]["seg"], LaneSegment):
                not_in_lane += 1

        if not_in_lane > 0:
            res_string = f"Reserved Check: {not_in_lane} cars' last segment is not a lane segment"
        else:
            res_string = f"Reserved Check: Each car's last segment is a lane segment"

        return not not_in_lane, res_string

    def priority_check(self) -> Tuple[bool, str]:
        """
        Check if the priority of cars is correct:
        If the current segment is a crossing segment, the priority should be 0.
        If the current segment is a lane segment, the priority should be the index of the car in the segment.
        The function prints the number of cars with incorrect priority, seperated by segment type.

        Returns:
            bool: True if all cars have the correct priority, False otherwise.
            str: The result string of the check.

        """
        incorrect_priority = 0
        for controller in self.controllers:
            car = controller.car
            priority = car.res[0]["seg"].cars.index(car)
            if isinstance(car.res[0]["seg"], LaneSegment):
                if priority != car.res[0]["seg"].cars.index(car):
                    incorrect_priority += 1
            elif isinstance(car.res[0]["seg"], CrossingSegment):
                if priority != 0:
                    incorrect_priority += 1

        if incorrect_priority > 0:
            res_string = f"Priority Check: {incorrect_priority} cars have incorrect priority"
        else:
            res_string = "Priority Check: Each car has the correct priority"

        return not incorrect_priority, res_string

    def reservation_check(self) -> Tuple[bool, str]:
        """
        Check if the car's reserved space is at least as long as its breaking distance.
        If it is longer, the reserved segment must include a path through a crossing,
        and the reserved length in the last segment should be exactly the car's size.
        The function prints the number of cars with incorrect reservations.
        Returns:
            bool: True if all cars have correct reservations, False otherwise.
            str: The result string of the check.
        """
        too_short_reservations = 0
        no_correct_reservation_on_last_segment = 0

        for controller in self.controllers:
            car = controller.car
            reserved_length = sum([abs(seg["end"]) - abs(seg["begin"]) for seg in car.res])

            if reserved_length < car.get_braking_distance():
                if car.res[-1]["seg"] == controller.goal.lane_segment:
                    continue
                too_short_reservations += 1

            elif reserved_length > car.get_braking_distance():  # todo:check if this is correct
                if car.res[-1]["end"] - car.res[-1]["begin"] < car.size:
                    no_correct_reservation_on_last_segment += 1

        if too_short_reservations > 0 or no_correct_reservation_on_last_segment > 0:
            res_string = (
                f"Reservation Check: {too_short_reservations + no_correct_reservation_on_last_segment} cars have incorrect reservations, "
                f"{too_short_reservations} are too short, {no_correct_reservation_on_last_segment} have no correct reservation on the last segment")
        else:
            res_string = "Reservation Check: Each car has correct reservations"

        return not (too_short_reservations + no_correct_reservation_on_last_segment), res_string

    def consistency_check(self) -> Tuple[bool, str]:
        """
        Check if the cars' reserved spaces are consistent with the cars in the segments.
        The function prints the number of cars with inconsistent reservations.
        Returns:
            bool: True if all cars have consistent reservations, False otherwise.
            string: The result string of the check.
        """
        missing_reservations = 0
        additional_reservations = 0

        for controller in self.controllers:
            car = controller.car
            for seg in car.res:
                if car not in seg["seg"].cars:
                    missing_reservations += 1

        for seg in self.game_model.segments:
            for car in seg.cars:
                segs = [seg["seg"] for seg in car.res]
                if seg not in segs:
                    additional_reservations += 1

        if missing_reservations > 0 or additional_reservations > 0:
            res_string = (
                f"Consistency Check: {missing_reservations + additional_reservations} inconsistent reservations, "
                f"{missing_reservations} missing reservations, {additional_reservations} additional reservations")
        else:
            res_string = "Consistency Check: Each car has consistent reservations"

        return not (missing_reservations + additional_reservations), res_string
