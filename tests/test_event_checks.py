import os
import sys
import unittest
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


from mlsl_simulation.game_model.road_network.road_network import (
    Point, Direction, Road, LaneSegment, CrossingSegment, SegmentInfo,
    Intersection, Goal,
)
from mlsl_simulation.game_model.event_checks import (
    reached_goal, collision_check
)
from mlsl_simulation.constants import BLOCK_SIZE


# ── helpers ───────────────────────────────────────────────────────────────────
def make_road(top=100, horizontal=True):
    return Road("r", horizontal, top, 1, 0)

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

    def test_not_reached_on_different_segment(self):
        car, goal, rm = self._setup(on_goal_seg=False, close=True)
        self.assertFalse(reached_goal(car, rm))

    def test_not_reached_on_goal_segment_but_far_away(self):
        car, goal, rm = self._setup(on_goal_seg=True, close=False)
        self.assertFalse(reached_goal(car, rm))


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


if __name__ == '__main__':
    unittest.main()
