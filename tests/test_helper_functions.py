import os
import sys
import unittest
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mlsl_simulation.game_model.road_network.road_network import (
    Point, Direction, Road, LaneSegment, CrossingSegment, SegmentInfo,
    Intersection, Goal,
)
from mlsl_simulation.game_model.road_network.helper_functions import (
    dist, overlap, reached_goal, collision_check,
    create_fixed_npc, create_random_car,
)
from mlsl_simulation.game_model.constants import BLOCK_SIZE


# ── helpers ───────────────────────────────────────────────────────────────────

def make_lane_seg(begin=0, end=4000, top=100, horizontal=True):
    road = Road("r", horizontal, top, 1, 0)
    lane = road.right_lanes[0]
    seg = LaneSegment(lane, begin, end)
    seg.num = 0
    return seg


def seg_info(segment, begin=0, end=20, direction=Direction.RIGHT):
    return SegmentInfo(segment=segment, begin=begin, end=end, direction=direction)


def mock_car(car_id, size_segments):
    car = unittest.mock.MagicMock()
    car.id = car_id
    car.size = BLOCK_SIZE
    car.get_size_segments.return_value = size_segments
    return car


# ── dist ──────────────────────────────────────────────────────────────────────

class TestDist(unittest.TestCase):

    def test_same_point_is_zero(self):
        p = Point(0, 0)
        self.assertAlmostEqual(dist(p, p), 0.0)

    def test_horizontal_distance(self):
        self.assertAlmostEqual(dist(Point(0, 0), Point(5, 0)), 5.0)

    def test_vertical_distance(self):
        self.assertAlmostEqual(dist(Point(0, 0), Point(0, 7)), 7.0)

    def test_345_triangle(self):
        self.assertAlmostEqual(dist(Point(0, 0), Point(3, 4)), 5.0)

    def test_512_triangle(self):
        self.assertAlmostEqual(dist(Point(0, 0), Point(5, 12)), 13.0)

    def test_negative_coords(self):
        self.assertAlmostEqual(dist(Point(-3, 0), Point(0, 4)), 5.0)

    def test_symmetric(self):
        p1, p2 = Point(1, 2), Point(4, 6)
        self.assertAlmostEqual(dist(p1, p2), dist(p2, p1))

    def test_large_values(self):
        self.assertAlmostEqual(dist(Point(0, 0), Point(300, 400)), 500.0)

    def test_non_origin_start(self):
        self.assertAlmostEqual(dist(Point(10, 10), Point(13, 14)), 5.0)


# ── overlap ───────────────────────────────────────────────────────────────────

class TestOverlap(unittest.TestCase):

    def test_identical_rectangles(self):
        p = Point(0, 0)
        self.assertTrue(overlap(p, 10, 10, p, 10, 10))

    def test_partial_overlap_x(self):
        self.assertTrue(overlap(Point(0, 0), 10, 10, Point(5, 0), 10, 10))

    def test_partial_overlap_y(self):
        self.assertTrue(overlap(Point(0, 0), 10, 10, Point(0, 5), 10, 10))

    def test_one_inside_another(self):
        self.assertTrue(overlap(Point(0, 0), 100, 100, Point(10, 10), 10, 10))

    def test_other_inside_one(self):
        self.assertTrue(overlap(Point(10, 10), 10, 10, Point(0, 0), 100, 100))

    def test_no_overlap_gap_on_right(self):
        # p1 x-span [0, 10], p2 starts at 11
        self.assertFalse(overlap(Point(0, 0), 10, 10, Point(11, 0), 10, 10))

    def test_no_overlap_gap_on_left(self):
        self.assertFalse(overlap(Point(11, 0), 10, 10, Point(0, 0), 10, 10))

    def test_no_overlap_gap_above(self):
        self.assertFalse(overlap(Point(0, 0), 10, 10, Point(0, 11), 10, 10))

    def test_no_overlap_gap_below(self):
        self.assertFalse(overlap(Point(0, 11), 10, 10, Point(0, 0), 10, 10))

    def test_touching_right_edge_counts_as_overlap(self):
        # p1.x + w1 == p2.x → condition p2.x > p1.x + w1 is False → returns True
        self.assertTrue(overlap(Point(0, 0), 10, 10, Point(10, 0), 10, 10))

    def test_touching_bottom_edge_counts_as_overlap(self):
        self.assertTrue(overlap(Point(0, 0), 10, 10, Point(0, 10), 10, 10))

    def test_completely_separate(self):
        self.assertFalse(overlap(Point(-100, -100), 5, 5, Point(100, 100), 5, 5))

    def test_zero_width_rectangle_touching(self):
        # Zero-width rect at x=5 against a full rect [0,10]
        self.assertTrue(overlap(Point(5, 0), 0, 10, Point(0, 0), 10, 10))

    def test_both_zero_size_same_point(self):
        self.assertTrue(overlap(Point(5, 5), 0, 0, Point(5, 5), 0, 0))

    def test_both_zero_size_different_point(self):
        # p1.x=0 > p2.x + 0 = 1? No; p2.x=1 > p1.x + 0 = 0? Yes → False
        self.assertFalse(overlap(Point(0, 0), 0, 0, Point(1, 0), 0, 0))


# ── reached_goal ──────────────────────────────────────────────────────────────

class TestReachedGoal(unittest.TestCase):

    def _setup(self, on_goal_seg=True, close=True):
        seg = make_lane_seg(0, 400)
        other_seg = make_lane_seg(0, 400, top=500)
        goal = Goal(seg, (255, 0, 0))

        car = unittest.mock.MagicMock()
        car.id = "c1"
        car.size = BLOCK_SIZE

        active_seg = seg if on_goal_seg else other_seg
        info = seg_info(active_seg)
        rm = unittest.mock.MagicMock()
        rm.get_car_reservation.return_value = info

        car.get_center.return_value = goal.pos if close else Point(0, 0)
        return car, goal, rm

    def test_reached_when_on_goal_segment_and_at_goal_pos(self):
        car, goal, rm = self._setup(on_goal_seg=True, close=True)
        self.assertTrue(reached_goal(car, goal, rm))

    def test_not_reached_on_different_segment(self):
        car, goal, rm = self._setup(on_goal_seg=False, close=True)
        self.assertFalse(reached_goal(car, goal, rm))

    def test_not_reached_on_goal_segment_but_far_away(self):
        car, goal, rm = self._setup(on_goal_seg=True, close=False)
        self.assertFalse(reached_goal(car, goal, rm))


# ── collision_check ───────────────────────────────────────────────────────────

class TestCollisionCheck(unittest.TestCase):

    def _info(self, segment, begin, end):
        return seg_info(segment, begin, end)

    def test_no_collision_different_segments(self):
        seg1 = make_lane_seg(top=100)
        seg2 = make_lane_seg(top=500)
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg1, 0, 20)])
        car2 = mock_car("c2", [self._info(seg2, 0, 20)])
        self.assertFalse(collision_check(car1, car2, rm))

    def test_collision_car1_begin_inside_car2(self):
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        # car2 occupies [10, 30], car1 starts at 15 inside it
        car1 = mock_car("c1", [self._info(seg, 15, 35)])
        car2 = mock_car("c2", [self._info(seg, 10, 30)])
        self.assertTrue(collision_check(car1, car2, rm))

    def test_collision_car1_end_inside_car2(self):
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        # car1 [5, 25] ends inside car2 [20, 40]
        car1 = mock_car("c1", [self._info(seg, 5, 25)])
        car2 = mock_car("c2", [self._info(seg, 20, 40)])
        self.assertTrue(collision_check(car1, car2, rm))

    def test_collision_car2_inside_car1(self):
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg, 0, 100)])
        car2 = mock_car("c2", [self._info(seg, 20, 50)])
        self.assertTrue(collision_check(car1, car2, rm))

    def test_collision_car1_inside_car2(self):
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg, 20, 50)])
        car2 = mock_car("c2", [self._info(seg, 0, 100)])
        self.assertTrue(collision_check(car1, car2, rm))

    def test_no_collision_car2_strictly_after_car1(self):
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg, 0, 10)])
        car2 = mock_car("c2", [self._info(seg, 20, 30)])
        self.assertFalse(collision_check(car1, car2, rm))

    def test_no_collision_car2_strictly_before_car1(self):
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg, 20, 30)])
        car2 = mock_car("c2", [self._info(seg, 0, 10)])
        self.assertFalse(collision_check(car1, car2, rm))

    def test_same_start_collision_is_detected(self):
        # When begin1 == begin2, the check `begin2 < end1 < end2` still fires
        # if end1 is strictly inside car2's range — collision IS detected.
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg, 10, 20)])
        car2 = mock_car("c2", [self._info(seg, 10, 30)])
        self.assertTrue(collision_check(car1, car2, rm))

    def test_end_boundary_equality_not_detected(self):
        # BUG: car1 end == car2 begin with strict < also misses the collision
        seg = make_lane_seg()
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg, 0, 20)])
        car2 = mock_car("c2", [self._info(seg, 20, 40)])
        # Documents current (buggy) behaviour; expected True if touching = collision
        self.assertFalse(collision_check(car1, car2, rm))

    def test_multi_segment_no_collision(self):
        seg1 = make_lane_seg(top=100)
        seg2 = make_lane_seg(top=500)
        rm = unittest.mock.MagicMock()
        car1 = mock_car("c1", [self._info(seg1, 0, 20), self._info(seg2, 0, 5)])
        car2 = mock_car("c2", [self._info(seg1, 50, 70)])
        self.assertFalse(collision_check(car1, car2, rm))


# ── create_fixed_npc ──────────────────────────────────────────────────────────

class TestCreateFixedNpc(unittest.TestCase):

    def _rm(self):
        from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
        return ReservationManagement()

    def test_car_name_matches_color_name(self):
        seg = make_lane_seg()
        car = create_fixed_npc("Red", seg, self._rm())
        self.assertEqual(car.name, "Red")

    def test_car_speed_is_zero(self):
        seg = make_lane_seg()
        car = create_fixed_npc("Red", seg, self._rm())
        self.assertEqual(car.speed, 0)

    def test_car_loc_is_zero(self):
        seg = make_lane_seg()
        car = create_fixed_npc("Blue", seg, self._rm())
        self.assertEqual(car.loc, 0)

    def test_default_size_is_block_size(self):
        seg = make_lane_seg()
        car = create_fixed_npc("Green", seg, self._rm())
        self.assertEqual(car.size, BLOCK_SIZE)

    def test_custom_size(self):
        seg = make_lane_seg()
        car = create_fixed_npc("Teal", seg, self._rm(), size=20)
        self.assertEqual(car.size, 20)

    def test_custom_max_speed(self):
        seg = make_lane_seg()
        car = create_fixed_npc("Navy", seg, self._rm(), max_speed=5)
        self.assertEqual(car.max_speed, 5)

    def test_car_color_matches_selected_colors(self):
        from mlsl_simulation.gui.selected_colors import selected_colors
        seg = make_lane_seg()
        car = create_fixed_npc("Red", seg, self._rm())
        self.assertEqual(car.color, selected_colors["Red"])


# ── create_random_car ─────────────────────────────────────────────────────────

class TestCreateRandomCar(unittest.TestCase):

    def _rm(self):
        from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
        return ReservationManagement()

    def test_creates_car_with_non_empty_name(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        car = create_random_car([seg], [], CarType.NPC, self._rm())
        self.assertNotEqual(car.name, "")

    def test_created_car_type(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        car = create_random_car([seg], [], CarType.NPC, self._rm())
        self.assertEqual(car.type, CarType.NPC)

    def test_car_placed_on_lane_segment(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        rm = self._rm()
        car = create_random_car([seg], [], CarType.NPC, rm)
        reservation = rm.get_car_reservation(car.id, 0)
        self.assertIsInstance(reservation.segment, LaneSegment)

    def test_car_initial_loc_is_zero(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        car = create_random_car([seg], [], CarType.NPC, self._rm())
        self.assertEqual(car.loc, 0)

    def test_speed_within_bounds(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        car = create_random_car([seg], [], CarType.NPC, self._rm())
        self.assertGreaterEqual(car.speed, 0)
        self.assertLessEqual(car.speed, car.max_speed)

    def test_second_car_placed_on_different_segment(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg1 = make_lane_seg(begin=0, end=4000, top=100)
        seg2 = make_lane_seg(begin=0, end=4000, top=500)
        rm = self._rm()
        car1 = create_random_car([seg1, seg2], [], CarType.NPC, rm)
        car2 = create_random_car([seg1, seg2], [car1], CarType.NPC, rm)
        r1 = rm.get_car_reservation(car1.id, 0)
        r2 = rm.get_car_reservation(car2.id, 0)
        self.assertIsNot(r1.segment, r2.segment)

    def test_only_lane_segments_chosen(self):
        from mlsl_simulation.game_model.car_types import CarType
        seg = make_lane_seg()
        h = Road("h", True, 200, 1, 0)
        v = Road("v", False, 200, 1, 0)
        ix = Intersection(h, v)
        crossing = CrossingSegment(h.right_lanes[0], v.right_lanes[0], ix)
        rm = self._rm()
        car = create_random_car([seg, crossing], [], CarType.NPC, rm)
        reservation = rm.get_car_reservation(car.id, 0)
        self.assertIsInstance(reservation.segment, LaneSegment)


if __name__ == '__main__':
    unittest.main()
