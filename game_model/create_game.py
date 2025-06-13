from typing import Optional, List

from game_model.road_network import CrossingSegment, Direction, Intersection, LaneSegment, Road, Segment, true_direction

def create_segments(roads: List[Road]) -> Optional[List[Segment]]:
    """
    Create segments for the given roads.

    Args:
        roads (List[Road]): The list of roads to create segments for.

    Returns:
        Optional[List[Segment]]: The list of created segments, or None if there was an overlap.
    """
    roads.sort(key=lambda r: r.top)
    segments:list[Segment] = []
    intersections:list[Intersection] = []
    last_horiz = 0
    horiz_roads = (road for road in roads if road.horizontal)
    for horiz_road in horiz_roads:
        if last_horiz > horiz_road.top:
            print(f"\nRoad {horiz_road.name} overlaps with the previous road")
            return None
        last_vert = 0
        vert_roads = (road for road in roads if not road.horizontal)
        for vert_road in vert_roads:
            if last_vert > vert_road.top:
                print(f"\nRoad {vert_road.name} {vert_road.top} overlaps with previous road {last_vert}")
                return None
            
            intersection:Intersection = Intersection(horiz_road, vert_road)
            intersections.append(intersection)

            # Starting with lanes:
            for horiz_lane in horiz_road.right_lanes + horiz_road.left_lanes:
                # There horizontal exist a lane segment:
                for vert_lane in vert_road.right_lanes + vert_road.left_lanes:
                    horiz_lane_segment = None
                    vert_lane_segment = None
                    if vert_road.top > last_vert and \
                            (vert_lane.num == 0 and
                                (vert_lane.direction == Direction.DOWN or len(vert_road.right_lanes) == 0)):
                        horiz_lane_segment = LaneSegment(horiz_lane, last_vert, vert_road.top) \
                            if true_direction[horiz_lane.direction] \
                            else LaneSegment(horiz_lane, vert_road.top, last_vert)
                    if horiz_road.top > last_horiz and \
                            (horiz_lane.num == 0 and
                                (horiz_lane.direction == Direction.RIGHT or len(horiz_road.right_lanes) == 0)):
                        vert_lane_segment = LaneSegment(vert_lane, last_horiz, horiz_road.top) \
                            if true_direction[vert_lane.direction] \
                            else LaneSegment(vert_lane, horiz_road.top, last_horiz)

                    if horiz_lane_segment is not None:
                        horiz_lane.segments.append(horiz_lane_segment)
                        horiz_lane_segment.num = len(horiz_lane.segments) - 1
                        segments.append(horiz_lane_segment)
                    if vert_lane_segment is not None:
                        vert_lane.segments.append(vert_lane_segment)
                        vert_lane_segment.num = len(vert_lane.segments) - 1
                        segments.append(vert_lane_segment)

                    crossing_segment = CrossingSegment(horiz_lane, vert_lane, intersection)
                    horiz_lane.segments.append(crossing_segment)
                    vert_lane.segments.append(crossing_segment)
                    crossing_segment.horiz_num = len(horiz_lane.segments) - 1
                    crossing_segment.vert_num = len(vert_lane.segments) - 1
                    segments.append(crossing_segment)
                    intersection.segments.append(crossing_segment)

            last_vert = vert_road.bottom

        last_horiz = horiz_road.bottom

    for road in roads:
        for lane in road.right_lanes + road.left_lanes:
            if true_direction[lane.direction]:
                for i in range(len(lane.segments) - 1):
                    match lane.segments[i]:
                        case LaneSegment():
                            lane.segments[i].end_crossing = lane.segments[i + 1]
                        case CrossingSegment():
                            if lane.direction == Direction.RIGHT:
                                lane.segments[i].connected_segments[Direction.RIGHT] = lane.segments[i + 1]
                                # if isinstance(lane.segments[i + 1], CrossingSegment):
                                #     lane.segments[i + 1].left = lane.segments[i]
                            elif lane.direction == Direction.UP:
                                lane.segments[i].connected_segments[Direction.UP] = lane.segments[i + 1]
                                # if isinstance(lane.segments[i + 1], CrossingSegment):
                                #     lane.segments[i + 1].down = lane.segments[i]
            else:
                for j in range(1, len(lane.segments)):
                    match lane.segments[j]:
                        case LaneSegment():
                            lane.segments[j].end_crossing = lane.segments[j - 1]
                        case CrossingSegment():
                            if lane.direction == Direction.LEFT:
                                lane.segments[j].connected_segments[Direction.LEFT] = lane.segments[j - 1]
                                # if isinstance(lane.segments[j - 1], CrossingSegment):
                                #     lane.segments[j - 1].right = lane.segments[j]
                            elif lane.direction == Direction.DOWN:
                                lane.segments[j].connected_segments[Direction.DOWN] = lane.segments[j - 1]
                                # if isinstance(lane.segments[j - 1], CrossingSegment):
                                #     lane.segments[j - 1].up = lane.segments[j]

    return segments, intersections

