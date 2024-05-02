from game_model.constants import *
from game_model.helper_functions import dist
from game_model.road_network import LaneSegment, CrossingSegment, Point, Segment


def astar_heuristic(current_seg: Segment, goal_seg: LaneSegment):
    mid_lane = BLOCK_SIZE // 2
    match current_seg:
        case LaneSegment():
            if goal_seg.lane.road.horizontal:
                if current_seg.lane.road.horizontal:
                    return dist(Point(current_seg.end, current_seg.lane.top),
                                Point(goal_seg.begin, goal_seg.lane.top))
                else:
                    return dist(Point(current_seg.lane.top, current_seg.end),
                                Point(goal_seg.begin, goal_seg.lane.top))
            else:
                if current_seg.lane.road.horizontal:
                    return dist(Point(current_seg.end, current_seg.lane.top),
                                Point(goal_seg.lane.top, goal_seg.begin))
                else:
                    return dist(Point(current_seg.lane.top, current_seg.end),
                                Point(goal_seg.lane.top, goal_seg.begin))
        case CrossingSegment():
            if goal_seg.lane.road.horizontal:
                return dist(Point(current_seg.horiz_lane.top + mid_lane, current_seg.vert_lane.top + mid_lane),
                            Point(goal_seg.begin, goal_seg.lane.top))
            else:
                return dist(Point(current_seg.horiz_lane.top + mid_lane, current_seg.vert_lane.top + mid_lane),
                            Point(goal_seg.lane.top, goal_seg.begin))


def reconstruct_path(came_from: dict[Segment, Segment],
                     current: LaneSegment) -> list[Segment]:
    path: list[Segment] = [current]
    while current in came_from:
        current = came_from[current]
        path.insert(0, current)
    return path
