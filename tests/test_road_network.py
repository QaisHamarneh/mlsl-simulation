import os
import sys
import unittest
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mlsl_simulation.game_model.road_network.road_network import (
    Point, Direction, Problem,
    direction_axis, true_direction, horiz_direction, right_direction,
    clock_wise,
    Road, Intersection, Lane, LaneSegment, CrossingSegment,
    SegmentInfo, Goal,
)
from mlsl_simulation.game_model.create_items.create_segments import create_segments
from mlsl_simulation.constants import (
    BLOCK_SIZE, LANE_DISPLACEMENT, LANE_MAX_SPEED, CROSSING_MAX_SPEED,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def horiz_road(name="h", top=100, right=1, left=1):
    return Road(name, True, top, right, left)


def vert_road(name="v", top=100, right=1, left=1):
    return Road(name, False, top, right, left)


def make_lane_segment(begin=0, end=400, horizontal=True, top=100, right=1):
    road = Road("r", horizontal, top, right, 0)
    lane = road.right_lanes[0]
    seg = LaneSegment(lane, begin, end)
    seg.num = 0
    return seg, lane, road


def make_crossing():
    h = horiz_road(right=1, left=0)
    v = vert_road(right=1, left=0)
    ix = Intersection(h, v)
    cs = CrossingSegment(h.right_lanes[0], v.right_lanes[0], ix)
    return cs, h, v, ix


# ── Point ─────────────────────────────────────────────────────────────────────

class TestPoint(unittest.TestCase):

    def test_stores_x_y(self):
        p = Point(3, 7)
        self.assertEqual(p.x, 3)
        self.assertEqual(p.y, 7)

    def test_negative_coords(self):
        p = Point(-1, -99)
        self.assertEqual(p.x, -1)
        self.assertEqual(p.y, -99)

    def test_zero_coords(self):
        p = Point(0, 0)
        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)

    def test_equality(self):
        self.assertEqual(Point(1, 2), Point(1, 2))
        self.assertNotEqual(Point(1, 2), Point(2, 1))


# ── Direction ─────────────────────────────────────────────────────────────────

class TestDirectionEnum(unittest.TestCase):

    def test_right_value(self):
        self.assertEqual(Direction.RIGHT.value, 1)

    def test_down_value(self):
        self.assertEqual(Direction.DOWN.value, 2)

    def test_left_value(self):
        self.assertEqual(Direction.LEFT.value, 3)

    def test_up_value(self):
        self.assertEqual(Direction.UP.value, 4)

    def test_enum_has_four_canonical_members(self):
        # Because DIRECTIONS is an alias for UP, list(Direction) has only 4 members.
        self.assertEqual(len(list(Direction)), 4)


# ── Problem ───────────────────────────────────────────────────────────────────

class TestProblemEnum(unittest.TestCase):

    def test_all_values_exist(self):
        expected = {
            "NO_NEXT_SEGMENT", "CHANGE_LANE_WHILE_CROSSING",
            "SLOWER_WHILE_0", "FASTER_WHILE_MAX",
            "NO_ADJACENT_LANE", "LANE_TOO_SHORT",
        }
        actual = {m.name for m in Problem}
        self.assertEqual(actual, expected)


# ── Direction lookup dicts ────────────────────────────────────────────────────

class TestDirectionAxis(unittest.TestCase):

    def test_right(self):
        self.assertEqual(direction_axis[Direction.RIGHT], (1, 0))

    def test_left(self):
        self.assertEqual(direction_axis[Direction.LEFT], (-1, 0))

    def test_up(self):
        self.assertEqual(direction_axis[Direction.UP], (0, 1))

    def test_down(self):
        self.assertEqual(direction_axis[Direction.DOWN], (0, -1))


class TestTrueDirection(unittest.TestCase):

    def test_right_is_true(self):
        self.assertTrue(true_direction[Direction.RIGHT])

    def test_up_is_true(self):
        self.assertTrue(true_direction[Direction.UP])

    def test_left_is_false(self):
        self.assertFalse(true_direction[Direction.LEFT])

    def test_down_is_false(self):
        self.assertFalse(true_direction[Direction.DOWN])


class TestHorizDirection(unittest.TestCase):

    def test_right_is_horizontal(self):
        self.assertTrue(horiz_direction[Direction.RIGHT])

    def test_left_is_horizontal(self):
        self.assertTrue(horiz_direction[Direction.LEFT])

    def test_up_is_not_horizontal(self):
        self.assertFalse(horiz_direction[Direction.UP])

    def test_down_is_not_horizontal(self):
        self.assertFalse(horiz_direction[Direction.DOWN])


class TestRightDirection(unittest.TestCase):

    def test_right_is_true(self):
        self.assertTrue(right_direction[Direction.RIGHT])

    def test_down_is_true(self):
        self.assertTrue(right_direction[Direction.DOWN])

    def test_left_is_false(self):
        self.assertFalse(right_direction[Direction.LEFT])

    def test_up_is_false(self):
        self.assertFalse(right_direction[Direction.UP])


class TestClockWise(unittest.TestCase):

    def test_has_four_elements(self):
        self.assertEqual(len(clock_wise), 4)

    def test_correct_order(self):
        self.assertEqual(
            clock_wise,
            [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP],
        )


# ── Road ──────────────────────────────────────────────────────────────────────

class TestRoad(unittest.TestCase):

    def test_horizontal_flag(self):
        self.assertTrue(horiz_road().horizontal)
        self.assertFalse(vert_road().horizontal)

    def test_name_stored(self):
        self.assertEqual(horiz_road("myroad").name, "myroad")

    def test_right_lane_count(self):
        self.assertEqual(len(horiz_road(right=3, left=1).right_lanes), 3)

    def test_left_lane_count(self):
        self.assertEqual(len(horiz_road(right=1, left=2).left_lanes), 2)

    def test_zero_right_lanes(self):
        self.assertEqual(len(horiz_road(right=0, left=1).right_lanes), 0)

    def test_zero_left_lanes(self):
        self.assertEqual(len(horiz_road(right=1, left=0).left_lanes), 0)

    def test_horiz_right_lane_direction(self):
        self.assertEqual(horiz_road(right=1, left=0).right_lanes[0].direction, Direction.RIGHT)

    def test_horiz_left_lane_direction(self):
        self.assertEqual(horiz_road(right=0, left=1).left_lanes[0].direction, Direction.LEFT)

    def test_vert_right_lane_direction(self):
        self.assertEqual(vert_road(right=1, left=0).right_lanes[0].direction, Direction.DOWN)

    def test_vert_left_lane_direction(self):
        self.assertEqual(vert_road(right=0, left=1).left_lanes[0].direction, Direction.UP)

    def test_first_right_lane_top_equals_road_top(self):
        road = horiz_road(top=100, right=2, left=0)
        self.assertEqual(road.right_lanes[0].top, 100)

    def test_second_right_lane_top(self):
        road = horiz_road(top=100, right=2, left=0)
        self.assertEqual(road.right_lanes[1].top, 100 + BLOCK_SIZE + LANE_DISPLACEMENT)

    def test_bottom_with_one_right_one_left_lane(self):
        road = horiz_road(top=0, right=1, left=1)
        self.assertEqual(road.bottom, 2 * BLOCK_SIZE + LANE_DISPLACEMENT)

    def test_get_outer_lane_segment_right_is_none_when_no_right_lanes(self):
        road = horiz_road(right=0, left=1)
        fake = unittest.mock.MagicMock()
        fake.num = 0
        self.assertIsNone(road.get_outer_lane_segment(fake, right_lanes=True))

    def test_get_outer_lane_segment_left_is_none_when_no_left_lanes(self):
        road = horiz_road(right=1, left=0)
        fake = unittest.mock.MagicMock()
        fake.num = 0
        self.assertIsNone(road.get_outer_lane_segment(fake, right_lanes=False))

    def test_get_outer_lane_segment_right_returns_first_right_lane_segment(self):
        # get_outer_lane_segment uses segment.num to index into the lane's segments list;
        # pass a LaneSegment that has been numbered by create_segments.
        h = horiz_road(right=2, left=0)
        v = vert_road(right=1, left=0)
        segments, _ = create_segments([h, v])
        lane_seg = next(s for s in segments if isinstance(s, LaneSegment) and s.lane.road is h)
        result = h.get_outer_lane_segment(lane_seg, right_lanes=True)
        self.assertIn(result, h.right_lanes[0].segments)

    def test_get_outer_lane_segment_left_returns_last_left_lane_segment(self):
        h = horiz_road(right=0, left=2)
        v = vert_road(right=1, left=0)
        segments, _ = create_segments([h, v])
        lane_seg = next(s for s in segments if isinstance(s, LaneSegment) and s.lane.road is h)
        result = h.get_outer_lane_segment(lane_seg, right_lanes=False)
        self.assertIn(result, h.left_lanes[-1].segments)


# ── Intersection ──────────────────────────────────────────────────────────────

class TestIntersection(unittest.TestCase):

    def setUp(self):
        self.h = horiz_road()
        self.v = vert_road()
        self.ix = Intersection(self.h, self.v)

    def test_horizontal_road_stored(self):
        self.assertIs(self.ix.horizontal_road, self.h)

    def test_vertical_road_stored(self):
        self.assertIs(self.ix.vertical_road, self.v)

    def test_segments_starts_empty(self):
        self.assertEqual(self.ix.segments, [])

    def test_intersection_state_initialized(self):
        self.assertIsNotNone(self.ix.intersection_state)

    def test_str_contains_both_road_names(self):
        s = str(self.ix)
        self.assertIn(self.h.name, s)
        self.assertIn(self.v.name, s)


# ── Lane ──────────────────────────────────────────────────────────────────────

class TestLane(unittest.TestCase):

    def test_attributes_stored(self):
        road = horiz_road(top=0, right=1, left=0)
        lane = road.right_lanes[0]
        self.assertIs(lane.road, road)
        self.assertEqual(lane.num, 0)
        self.assertEqual(lane.direction, Direction.RIGHT)
        self.assertEqual(lane.top, 0)

    def test_segments_starts_empty(self):
        road = horiz_road(right=1, left=0)
        self.assertEqual(road.right_lanes[0].segments, [])

    def test_multiple_lanes_have_correct_nums(self):
        road = horiz_road(right=3, left=0)
        for i, lane in enumerate(road.right_lanes):
            self.assertEqual(lane.num, i)


# ── LaneSegment ───────────────────────────────────────────────────────────────

class TestLaneSegment(unittest.TestCase):

    def test_length_equals_abs_diff(self):
        seg, _, _ = make_lane_segment(0, 400)
        self.assertEqual(seg.length, 400)

    def test_length_reversed_begin_end(self):
        seg, _, _ = make_lane_segment(400, 0)
        self.assertEqual(seg.length, 400)

    def test_zero_length_segment(self):
        seg, _, _ = make_lane_segment(100, 100)
        self.assertEqual(seg.length, 0)

    def test_max_speed(self):
        seg, _, _ = make_lane_segment()
        self.assertEqual(seg.max_speed, LANE_MAX_SPEED)

    def test_num_starts_none(self):
        road = horiz_road(right=1, left=0)
        lane = road.right_lanes[0]
        seg = LaneSegment(lane, 0, 400)
        self.assertIsNone(seg.num)

    def test_end_crossing_starts_none(self):
        seg, _, _ = make_lane_segment()
        # end_crossing is None before create_segments wires it up
        road = horiz_road(right=1, left=0)
        lane = road.right_lanes[0]
        raw_seg = LaneSegment(lane, 0, 400)
        self.assertIsNone(raw_seg.end_crossing)

    def test_road_reference(self):
        seg, lane, road = make_lane_segment()
        self.assertIs(seg.road, road)

    def test_lane_reference(self):
        seg, lane, _ = make_lane_segment()
        self.assertIs(seg.lane, lane)

    def test_begin_and_end_stored(self):
        seg, _, _ = make_lane_segment(50, 300)
        self.assertEqual(seg.begin, 50)
        self.assertEqual(seg.end, 300)

    def test_str_contains_road_name(self):
        seg, lane, _ = make_lane_segment()
        self.assertIn(lane.road.name, str(seg))

    def test_str_contains_direction(self):
        seg, lane, _ = make_lane_segment()
        self.assertIn(lane.direction.name, str(seg))

    def test_str_contains_lane_num(self):
        seg, lane, _ = make_lane_segment()
        self.assertIn(str(lane.num), str(seg))


# ── CrossingSegment ───────────────────────────────────────────────────────────

class TestCrossingSegment(unittest.TestCase):

    def test_length_equals_block_size(self):
        cs, _, _, _ = make_crossing()
        self.assertEqual(cs.length, BLOCK_SIZE)

    def test_max_speed(self):
        cs, _, _, _ = make_crossing()
        self.assertEqual(cs.max_speed, CROSSING_MAX_SPEED)

    def test_horiz_num_starts_none(self):
        cs, _, _, _ = make_crossing()
        self.assertIsNone(cs.horiz_num)

    def test_vert_num_starts_none(self):
        cs, _, _, _ = make_crossing()
        self.assertIsNone(cs.vert_num)

    def test_all_connected_segments_start_none(self):
        cs, _, _, _ = make_crossing()
        for d in [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]:
            self.assertIsNone(cs.connected_segments[d])

    def test_all_four_directions_present(self):
        cs, _, _, _ = make_crossing()
        for d in [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]:
            self.assertIn(d, cs.connected_segments)

    def test_get_road_horiz_not_opposite_returns_horiz_road(self):
        cs, h, v, _ = make_crossing()
        self.assertIs(cs.get_road(Direction.RIGHT, opposite=False), h)

    def test_get_road_horiz_not_opposite_left(self):
        cs, h, v, _ = make_crossing()
        self.assertIs(cs.get_road(Direction.LEFT, opposite=False), h)

    def test_get_road_vert_not_opposite_returns_vert_road(self):
        cs, h, v, _ = make_crossing()
        self.assertIs(cs.get_road(Direction.DOWN, opposite=False), v)

    def test_get_road_vert_not_opposite_up(self):
        cs, h, v, _ = make_crossing()
        self.assertIs(cs.get_road(Direction.UP, opposite=False), v)

    def test_get_road_horiz_opposite_returns_vert_road(self):
        cs, h, v, _ = make_crossing()
        self.assertIs(cs.get_road(Direction.RIGHT, opposite=True), v)

    def test_intersection_reference(self):
        cs, _, _, ix = make_crossing()
        self.assertIs(cs.intersection, ix)

    def test_crossing_segment_state_initialized(self):
        cs, _, _, _ = make_crossing()
        self.assertIsNotNone(cs.crossing_segment_state)

    def test_str_contains_both_road_names(self):
        cs, h, v, _ = make_crossing()
        s = str(cs)
        self.assertIn(h.name, s)
        self.assertIn(v.name, s)

    def test_horiz_lane_reference(self):
        h = horiz_road(right=1, left=0)
        v = vert_road(right=1, left=0)
        ix = Intersection(h, v)
        hl = h.right_lanes[0]
        vl = v.right_lanes[0]
        cs = CrossingSegment(hl, vl, ix)
        self.assertIs(cs.horiz_lane, hl)
        self.assertIs(cs.vert_lane, vl)


# ── SegmentInfo ───────────────────────────────────────────────────────────────

class TestSegmentInfo(unittest.TestCase):

    def _seg(self):
        seg, _, _ = make_lane_segment()
        return seg

    def test_default_turn_is_false(self):
        info = SegmentInfo(self._seg(), 0, 400, Direction.RIGHT)
        self.assertFalse(info.turn)

    def test_explicit_turn_true(self):
        info = SegmentInfo(self._seg(), 0, 400, Direction.RIGHT, turn=True)
        self.assertTrue(info.turn)

    def test_all_attributes_stored(self):
        seg = self._seg()
        info = SegmentInfo(seg, 10, 200, Direction.LEFT)
        self.assertIs(info.segment, seg)
        self.assertEqual(info.begin, 10)
        self.assertEqual(info.end, 200)
        self.assertEqual(info.direction, Direction.LEFT)

    def test_str_contains_begin_and_end(self):
        info = SegmentInfo(self._seg(), 10, 200, Direction.RIGHT)
        s = str(info)
        self.assertIn("10", s)
        self.assertIn("200", s)


# ── Goal ──────────────────────────────────────────────────────────────────────

class TestGoal(unittest.TestCase):

    def _horiz_goal(self, begin=0, end=400, top=100):
        road = horiz_road(top=top, right=1, left=0)
        lane = road.right_lanes[0]
        seg = LaneSegment(lane, begin, end)
        seg.num = 0
        return Goal(seg, (255, 0, 0)), lane

    def _vert_goal(self, begin=0, end=400, top=100):
        road = vert_road(top=top, right=1, left=0)
        lane = road.right_lanes[0]
        seg = LaneSegment(lane, begin, end)
        seg.num = 0
        return Goal(seg, (0, 255, 0)), lane

    def test_pos_initialized_at_construction(self):
        goal, _ = self._horiz_goal()
        self.assertIsNotNone(goal.pos)

    def test_horizontal_goal_x_is_midpoint(self):
        goal, _ = self._horiz_goal(begin=0, end=400)
        self.assertEqual(goal.pos.x, 200)

    def test_horizontal_goal_y_uses_lane_top(self):
        goal, lane = self._horiz_goal(begin=0, end=400)
        self.assertEqual(goal.pos.y, lane.top + BLOCK_SIZE // 2)

    def test_vertical_goal_y_is_midpoint(self):
        goal, _ = self._vert_goal(begin=0, end=400)
        self.assertEqual(goal.pos.y, 200)

    def test_vertical_goal_x_uses_lane_top(self):
        goal, lane = self._vert_goal(begin=0, end=400)
        self.assertEqual(goal.pos.x, lane.top + BLOCK_SIZE // 2)

    def test_color_stored(self):
        color = (128, 64, 32)
        road = horiz_road(right=1, left=0)
        lane = road.right_lanes[0]
        seg = LaneSegment(lane, 0, 400)
        seg.num = 0
        goal = Goal(seg, color)
        self.assertEqual(goal.color, color)

    def test_horizontal_midpoint_integer_division(self):
        goal, _ = self._horiz_goal(begin=0, end=401)
        self.assertEqual(goal.pos.x, 200)  # (0 + 401) // 2

    def test_non_zero_begin_midpoint(self):
        goal, _ = self._horiz_goal(begin=100, end=300)
        self.assertEqual(goal.pos.x, 200)  # (100 + 300) // 2

    def test_lane_segment_reference(self):
        road = horiz_road(right=1, left=0)
        lane = road.right_lanes[0]
        seg = LaneSegment(lane, 0, 400)
        seg.num = 0
        goal = Goal(seg, (0, 0, 0))
        self.assertIs(goal.lane_segment, seg)


if __name__ == '__main__':
    unittest.main()
