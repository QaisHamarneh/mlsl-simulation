import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mlsl_simulation.game_model.create_items.create_segments import create_segments
from mlsl_simulation.game_model.road_network.road_network import (
    CrossingSegment, Direction, Intersection, LaneSegment, Road,
)
from mlsl_simulation.constants import BLOCK_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT


# ── helpers ──────────────────────────────────────────────────────────────────

def horiz(name, top, right=1, left=1):
    return Road(name, True, top, right, left)


def vert(name, top, right=1, left=1):
    return Road(name, False, top, right, left)


def circuit_roads():
    """Four boundary roads that form a minimal closed loop."""
    return [
        Road("bottom", True,  0,                        1, 0),
        Road("top",    True,  WINDOW_HEIGHT - BLOCK_SIZE, 0, 1),
        Road("left",   False, 0,                        1, 0),
        Road("right",  False, WINDOW_WIDTH  - BLOCK_SIZE, 0, 1),
    ]


# Each road's bottom = top + (r+l)*BLOCK_SIZE + (r+l-1)*LANE_DISPLACEMENT.
# GAP is large enough that two default (1,1) roads placed GAP apart never overlap.
GAP = 500


# ── no-intersection cases ─────────────────────────────────────────────────────

class TestNoIntersections(unittest.TestCase):

    def test_empty_roads_returns_empty(self):
        segments, intersections = create_segments([])
        self.assertEqual(segments, [])
        self.assertEqual(intersections, [])

    def test_only_horizontal_road_produces_no_segments(self):
        segments, intersections = create_segments([horiz("h1", 200)])
        self.assertEqual(segments, [])
        self.assertEqual(intersections, [])

    def test_only_vertical_road_produces_no_segments(self):
        segments, intersections = create_segments([vert("v1", 200)])
        self.assertEqual(segments, [])
        self.assertEqual(intersections, [])

    def test_multiple_horizontal_no_vertical_produces_no_segments(self):
        roads = [horiz("h1", 100), horiz("h2", 100 + GAP)]
        segments, intersections = create_segments(roads)
        self.assertEqual(segments, [])
        self.assertEqual(intersections, [])


# ── intersection creation ─────────────────────────────────────────────────────

class TestIntersectionCreation(unittest.TestCase):

    def test_single_intersection(self):
        _, intersections = create_segments([horiz("h1", 200), vert("v1", 200)])
        self.assertEqual(len(intersections), 1)

    def test_intersection_references_correct_roads(self):
        h = horiz("h1", 200)
        v = vert("v1", 200)
        _, intersections = create_segments([h, v])
        ix = intersections[0]
        self.assertIs(ix.horizontal_road, h)
        self.assertIs(ix.vertical_road, v)

    def test_two_horiz_one_vert_gives_two_intersections(self):
        roads = [horiz("h1", 100), horiz("h2", 100 + GAP), vert("v1", 100)]
        _, intersections = create_segments(roads)
        self.assertEqual(len(intersections), 2)

    def test_intersection_count_is_horiz_times_vert(self):
        """2 horizontal × 3 vertical = 6 intersections."""
        roads = [
            horiz("h1", 100), horiz("h2", 100 + GAP),
            vert("v1", 100), vert("v2", 100 + GAP), vert("v3", 100 + 2 * GAP),
        ]
        _, intersections = create_segments(roads)
        self.assertEqual(len(intersections), 6)

    def test_circuit_has_four_intersections(self):
        """2 horiz × 2 vert boundary roads → 4 intersections."""
        _, intersections = create_segments(circuit_roads())
        self.assertEqual(len(intersections), 4)

    def test_intersection_segments_list_populated(self):
        _, intersections = create_segments([horiz("h1", 200), vert("v1", 200)])
        self.assertGreater(len(intersections[0].segments), 0)


# ── segment types and counts ──────────────────────────────────────────────────

class TestSegmentTypes(unittest.TestCase):

    def test_all_segments_are_lane_or_crossing(self):
        segments, _ = create_segments([horiz("h1", 200), vert("v1", 200)])
        for seg in segments:
            self.assertIsInstance(seg, (LaneSegment, CrossingSegment))

    def test_crossing_count_equals_lane_product(self):
        """4 horiz lanes × 2 vert lanes at one intersection = 8 crossings."""
        h = horiz("h1", 200, right=2, left=2)
        v = vert("v1", 200, right=1, left=1)
        segments, _ = create_segments([h, v])
        crossings = [s for s in segments if isinstance(s, CrossingSegment)]
        self.assertEqual(len(crossings), 8)

    def test_circuit_total_segment_count(self):
        """Circuit: 4 lane segments + 4 crossing segments = 8."""
        segments, _ = create_segments(circuit_roads())
        self.assertEqual(len(segments), 8)

    def test_circuit_has_four_lane_segments(self):
        segments, _ = create_segments(circuit_roads())
        lane_segs = [s for s in segments if isinstance(s, LaneSegment)]
        self.assertEqual(len(lane_segs), 4)

    def test_circuit_has_four_crossing_segments(self):
        segments, _ = create_segments(circuit_roads())
        crossings = [s for s in segments if isinstance(s, CrossingSegment)]
        self.assertEqual(len(crossings), 4)

    def test_lane_segment_length_equals_abs_diff(self):
        segments, _ = create_segments(circuit_roads())
        for seg in segments:
            if isinstance(seg, LaneSegment):
                self.assertEqual(seg.length, abs(seg.end - seg.begin))

    def test_crossing_segment_length_equals_block_size(self):
        segments, _ = create_segments([horiz("h1", 200), vert("v1", 200)])
        for seg in segments:
            if isinstance(seg, CrossingSegment):
                self.assertEqual(seg.length, BLOCK_SIZE)


# ── lane assignment ───────────────────────────────────────────────────────────

class TestLaneAssignment(unittest.TestCase):

    def test_segments_appended_to_horizontal_lane(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        create_segments([h, v])
        self.assertGreater(len(h.right_lanes[0].segments), 0)

    def test_segments_appended_to_vertical_lane(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        create_segments([h, v])
        self.assertGreater(len(v.right_lanes[0].segments), 0)

    def test_crossing_segment_shared_by_both_lanes(self):
        """The same CrossingSegment object appears in both its horiz and vert lane."""
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        segments, _ = create_segments([h, v])
        for cs in segments:
            if isinstance(cs, CrossingSegment):
                self.assertIn(cs, cs.horiz_lane.segments)
                self.assertIn(cs, cs.vert_lane.segments)

    def test_crossing_segment_appears_once_in_segments_list(self):
        """CrossingSegment is appended once to the global segments list."""
        segments, _ = create_segments([horiz("h1", 200), vert("v1", 200)])
        crossings = [s for s in segments if isinstance(s, CrossingSegment)]
        for cs in crossings:
            self.assertEqual(segments.count(cs), 1)


# ── segment connectivity ──────────────────────────────────────────────────────

class TestSegmentConnectivity(unittest.TestCase):

    def test_lane_segment_end_crossing_is_crossing_segment(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        segments, _ = create_segments([h, v])
        for seg in segments:
            if isinstance(seg, LaneSegment):
                self.assertIsInstance(seg.end_crossing, CrossingSegment)

    def test_right_lane_crossing_has_right_connection(self):
        """CrossingSegments on a RIGHT lane must have a non-None RIGHT connection."""
        segments, _ = create_segments(circuit_roads())
        for cs in segments:
            if isinstance(cs, CrossingSegment) and cs.horiz_lane.direction == Direction.RIGHT:
                self.assertIsNotNone(cs.connected_segments[Direction.RIGHT])

    def test_left_lane_crossing_has_left_connection(self):
        segments, _ = create_segments(circuit_roads())
        for cs in segments:
            if isinstance(cs, CrossingSegment) and cs.horiz_lane.direction == Direction.LEFT:
                self.assertIsNotNone(cs.connected_segments[Direction.LEFT])

    def test_up_lane_crossing_has_up_connection(self):
        segments, _ = create_segments(circuit_roads())
        for cs in segments:
            if isinstance(cs, CrossingSegment) and cs.vert_lane.direction == Direction.UP:
                self.assertIsNotNone(cs.connected_segments[Direction.UP])

    def test_down_lane_crossing_has_down_connection(self):
        segments, _ = create_segments(circuit_roads())
        for cs in segments:
            if isinstance(cs, CrossingSegment) and cs.vert_lane.direction == Direction.DOWN:
                self.assertIsNotNone(cs.connected_segments[Direction.DOWN])

    def test_circuit_lane_segment_end_crossing_connectivity(self):
        """In the circuit each LaneSegment.end_crossing must be in segments."""
        segments, _ = create_segments(circuit_roads())
        for seg in segments:
            if isinstance(seg, LaneSegment):
                self.assertIn(seg.end_crossing, segments)


# ── segment numbering ─────────────────────────────────────────────────────────

class TestSegmentNumbering(unittest.TestCase):

    def test_lane_segment_num_is_set(self):
        segments, _ = create_segments([horiz("h1", 200, 1, 0), vert("v1", 200, 1, 0)])
        for seg in segments:
            if isinstance(seg, LaneSegment):
                self.assertIsNotNone(seg.num)

    def test_lane_segment_num_matches_position_in_lane(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        create_segments([h, v])
        lane = h.right_lanes[0]
        for i, seg in enumerate(lane.segments):
            if isinstance(seg, LaneSegment):
                self.assertEqual(seg.num, i)

    def test_crossing_segment_horiz_num_is_set(self):
        segments, _ = create_segments([horiz("h1", 200, 1, 0), vert("v1", 200, 1, 0)])
        for seg in segments:
            if isinstance(seg, CrossingSegment):
                self.assertIsNotNone(seg.horiz_num)

    def test_crossing_segment_vert_num_is_set(self):
        segments, _ = create_segments([horiz("h1", 200, 1, 0), vert("v1", 200, 1, 0)])
        for seg in segments:
            if isinstance(seg, CrossingSegment):
                self.assertIsNotNone(seg.vert_num)

    def test_crossing_horiz_num_matches_position_in_horiz_lane(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        create_segments([h, v])
        lane = h.right_lanes[0]
        for i, seg in enumerate(lane.segments):
            if isinstance(seg, CrossingSegment):
                self.assertEqual(seg.horiz_num, i)

    def test_crossing_vert_num_matches_position_in_vert_lane(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        create_segments([h, v])
        lane = v.right_lanes[0]
        for i, seg in enumerate(lane.segments):
            if isinstance(seg, CrossingSegment):
                self.assertEqual(seg.vert_num, i)


# ── overlap detection ─────────────────────────────────────────────────────────

class TestOverlapDetection(unittest.TestCase):

    def test_overlapping_horizontal_roads_raises_system_exit(self):
        # h1 bottom = 100 + 2*40 + 1*2 = 182; h2 top = 101 < 182 → overlap
        h1 = horiz("h1", 100)
        h2 = horiz("h2", 101)
        with self.assertRaises(SystemExit) as ctx:
            with unittest.mock.patch('builtins.print'):
                create_segments([h1, h2, vert("v1", 100)])
        self.assertEqual(ctx.exception.code, 1)

    def test_overlapping_vertical_roads_raises_system_exit(self):
        # v1 bottom = 182; v2 top = 101 < 182 → overlap
        v1 = vert("v1", 100)
        v2 = vert("v2", 101)
        with self.assertRaises(SystemExit) as ctx:
            with unittest.mock.patch('builtins.print'):
                create_segments([horiz("h1", 100), v1, v2])
        self.assertEqual(ctx.exception.code, 1)

    def test_non_overlapping_roads_do_not_exit(self):
        # h1 bottom = 182; h2 top = 300 > 182 → no overlap
        h1 = horiz("h1", 100)
        h2 = horiz("h2", 300)
        v1 = vert("v1", 100)
        # Should complete without raising
        create_segments([h1, h2, v1])


# ── single-direction lane roads ───────────────────────────────────────────────

class TestSingleDirectionLanes(unittest.TestCase):

    def test_right_lanes_only_creates_crossing_segments(self):
        h = horiz("h1", 200, right=2, left=0)
        v = vert("v1", 200, right=2, left=0)
        segments, intersections = create_segments([h, v])
        self.assertEqual(len(intersections), 1)
        crossings = [s for s in segments if isinstance(s, CrossingSegment)]
        self.assertEqual(len(crossings), 4)  # 2 × 2

    def test_left_lanes_only_creates_crossing_segments(self):
        h = horiz("h1", 200, right=0, left=2)
        v = vert("v1", 200, right=0, left=2)
        segments, intersections = create_segments([h, v])
        self.assertEqual(len(intersections), 1)
        crossings = [s for s in segments if isinstance(s, CrossingSegment)]
        self.assertEqual(len(crossings), 4)  # 2 × 2

    def test_right_only_lane_direction_is_correct(self):
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)
        create_segments([h, v])
        self.assertEqual(h.right_lanes[0].direction, Direction.RIGHT)
        self.assertEqual(v.right_lanes[0].direction, Direction.DOWN)

    def test_left_only_lane_direction_is_correct(self):
        h = horiz("h1", 200, right=0, left=1)
        v = vert("v1", 200, right=0, left=1)
        create_segments([h, v])
        self.assertEqual(h.left_lanes[0].direction, Direction.LEFT)
        self.assertEqual(v.left_lanes[0].direction, Direction.UP)


# ── road sorting ──────────────────────────────────────────────────────────────

class TestRoadSorting(unittest.TestCase):

    def test_roads_processed_regardless_of_input_order(self):
        """Segment count should be the same no matter the input order."""
        h = horiz("h1", 200, right=1, left=0)
        v = vert("v1", 200, right=1, left=0)

        seg_a, ix_a = create_segments([h, v])
        # Reset lane state for a fresh run
        h2 = horiz("h1", 200, right=1, left=0)
        v2 = vert("v1", 200, right=1, left=0)
        seg_b, ix_b = create_segments([v2, h2])

        self.assertEqual(len(seg_a), len(seg_b))
        self.assertEqual(len(ix_a), len(ix_b))


import unittest.mock  # noqa: E402 – imported at bottom to keep the top clean

if __name__ == '__main__':
    unittest.main()
