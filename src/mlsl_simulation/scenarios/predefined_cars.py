from dataclasses import dataclass
from typing import List, Optional, Tuple

from mlsl_simulation.game_model.car_types import CarType
from mlsl_simulation.game_model.road_network.road_network import LaneSegment, Road


@dataclass
class SegmentRef:
    """Reference to a specific lane segment by road / direction / lane / segment index.

    `direction` is "right" or "left" — selects from `road.right_lanes` or
    `road.left_lanes`. `segment` is the index counting only `LaneSegment`s
    on the lane (CrossingSegments are skipped).
    """
    road: str
    direction: str
    lane: int
    segment: int

    @classmethod
    def from_dict(cls, data: dict) -> "SegmentRef":
        return cls(
            road=data["road"],
            direction=data["direction"],
            lane=int(data["lane"]),
            segment=int(data["segment"]),
        )


@dataclass
class GoalSpec:
    segment: SegmentRef
    loc: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "GoalSpec":
        return cls(
            segment=SegmentRef.from_dict(data["segment"]),
            loc=int(data["loc"]) if "loc" in data and data["loc"] is not None else None,
        )


@dataclass
class CarSpec:
    """Predefined car configuration. Any field left as None falls back to the
    existing random logic in `create_random_car` / `create_goal`.
    """
    type: CarType = CarType.NPC
    start: Optional[SegmentRef] = None
    loc: Optional[int] = None
    speed: Optional[int] = None
    max_speed: Optional[int] = None
    first_goal: Optional[GoalSpec] = None
    second_goal: Optional[GoalSpec] = None
    name: Optional[str] = None
    size: Optional[int] = None
    color: Optional[Tuple[int, int, int]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CarSpec":
        type_str = data.get("type", "NPC").upper()
        try:
            car_type = CarType[type_str]
        except KeyError as exc:
            raise ValueError(f"Unknown car type {data.get('type')!r}; expected NPC or AGENT") from exc

        color = data.get("color")
        if color is not None:
            color = tuple(color)

        return cls(
            type=car_type,
            start=SegmentRef.from_dict(data["start"]) if "start" in data else None,
            loc=int(data["loc"]) if "loc" in data and data["loc"] is not None else None,
            speed=int(data["speed"]) if "speed" in data and data["speed"] is not None else None,
            max_speed=int(data["max_speed"]) if "max_speed" in data and data["max_speed"] is not None else None,
            first_goal=GoalSpec.from_dict(data["first_goal"]) if "first_goal" in data else None,
            second_goal=GoalSpec.from_dict(data["second_goal"]) if "second_goal" in data else None,
            name=data.get("name"),
            size=int(data["size"]) if "size" in data and data["size"] is not None else None,
            color=color,
        )


def resolve_segment(roads: List[Road], ref: SegmentRef) -> LaneSegment:
    """Resolve a SegmentRef against the active road network."""
    road = next((r for r in roads if r.name == ref.road), None)
    if road is None:
        raise ValueError(f"Road {ref.road!r} not found in scenario")

    direction = ref.direction.lower()
    if direction == "right":
        lanes = road.right_lanes
    elif direction == "left":
        lanes = road.left_lanes
    else:
        raise ValueError(
            f"SegmentRef.direction must be 'right' or 'left', got {ref.direction!r}"
        )

    if not (0 <= ref.lane < len(lanes)):
        raise ValueError(
            f"Lane index {ref.lane} out of range for road {ref.road!r} "
            f"({direction} has {len(lanes)} lanes)"
        )
    lane = lanes[ref.lane]

    lane_segments = [s for s in lane.segments if isinstance(s, LaneSegment)]
    if not (0 <= ref.segment < len(lane_segments)):
        raise ValueError(
            f"Segment index {ref.segment} out of range for "
            f"{ref.road}:{direction}:{ref.lane} (has {len(lane_segments)} lane segments)"
        )
    return lane_segments[ref.segment]
