from game_model.constants import *
from game_model.helper_functions import dist
from game_model.road_network import LaneSegment, CrossingSegment, Point, Segment


def astar_heuristic(current_seg: Segment, goal_seg: LaneSegment) -> float:
    """
    Calculate the heuristic distance between the current segment and the goal segment for the A* algorithm.

    Args:
        current_seg (Segment): The current segment the car is on.
        goal_seg (LaneSegment): The goal segment the car is trying to reach.

    Returns:
        float: The heuristic distance between the current segment and the goal segment.
    """
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
                return dist(Point(current_seg.horiz_lane.top + MID_LANE, current_seg.vert_lane.top + MID_LANE),
                            Point(goal_seg.begin, goal_seg.lane.top))
            else:
                return dist(Point(current_seg.horiz_lane.top + MID_LANE, current_seg.vert_lane.top + MID_LANE),
                            Point(goal_seg.lane.top, goal_seg.begin))


def reconstruct_path(came_from: Dict[Segment, Segment],
                     current: LaneSegment) -> List[Segment]:
    """
    Reconstruct the path from the start segment to the goal segment using the came_from map.

    Args:
        came_from (Dict[Segment, Segment]): A dictionary mapping each segment to the segment it came from.
        current (LaneSegment): The current segment (goal segment).

    Returns:
        List[Segment]: The reconstructed path from the start segment to the goal segment.
    """
    path: list[Segment] = [current]
    while current in came_from:
        current = came_from[current]
        path.insert(0, current)
    return path
