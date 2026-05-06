import os
import sys
import unittest
import unittest.mock

from mlsl_simulation.game_model.create_items.create_segments import create_segments
from tests.test_event_checks import make_lane_seg, make_road

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mlsl_simulation.game_model.create_items.create_cars import create_random_car
from mlsl_simulation.game_model.road_network.road_network import (
    Road, LaneSegment, CrossingSegment, Intersection,
)
from mlsl_simulation.constants import BLOCK_SIZE

# ── create_random_car ─────────────────────────────────────────────────────────

class TestCreateRandomCar(unittest.TestCase):

    def _rm(self):
        from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
        return ReservationManagement()

    def test_creates_car_with_non_empty_name(self):
        from mlsl_simulation.game_model.car_types import CarType
        roads = [make_road()]
        create_segments(roads)
        car = create_random_car(roads, [], CarType.NPC, self._rm())
        self.assertNotEqual(car.name, "")

    def test_created_car_type(self):
        from mlsl_simulation.game_model.car_types import CarType
        roads = [make_road()]
        create_segments(roads)
        car = create_random_car(roads, [], CarType.NPC, self._rm())
        self.assertEqual(car.type, CarType.NPC)

    def test_car_placed_on_lane_segment(self):
        from mlsl_simulation.game_model.car_types import CarType
        rm = self._rm()
        roads = [make_road()]
        create_segments(roads)
        car = create_random_car(roads, [], CarType.NPC, rm)
        reservation = rm.get_car_reservation(car.id, 0)
        self.assertIsInstance(reservation.segment, LaneSegment)

    def test_car_initial_loc_is_zero(self):
        from mlsl_simulation.game_model.car_types import CarType
        roads = [make_road(horizontal=True, top=500), make_road(horizontal=False, top=500)]
        create_segments(roads)
        car = create_random_car(roads, [], CarType.NPC, self._rm())
        self.assertEqual(car.loc, 0)

    def test_speed_within_bounds(self):
        from mlsl_simulation.game_model.car_types import CarType
        roads = [make_road()]
        create_segments(roads)
        car = create_random_car(roads, [], CarType.NPC, self._rm())
        self.assertGreaterEqual(car.speed, 0)
        self.assertLessEqual(car.speed, car.max_speed)

    def test_second_car_placed_on_different_segment(self):
        from mlsl_simulation.game_model.car_types import CarType
        roads = [make_road(top=100), make_road(top=500)]
        create_segments(roads)
        rm = self._rm()
        car1 = create_random_car(roads, [], CarType.NPC, rm)
        car2 = create_random_car(roads, [car1], CarType.NPC, rm)
        r1 = rm.get_car_reservation(car1.id, 0)
        r2 = rm.get_car_reservation(car2.id, 0)
        self.assertIsNot(r1.segment, r2.segment)

    def test_only_lane_segments_chosen(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        h = Road("h", True, 200, 1, 0)
        v = Road("v", False, 200, 1, 0)
        create_segments([h, v])
        rm = self._rm()
        cars = [create_random_car([h, v], [], CarType.NPC, rm) for i in range(4)]
        for i in range(4):
            reservation = rm.get_car_reservation(cars[i].id, 0)
            self.assertIsInstance(reservation.segment, LaneSegment)
