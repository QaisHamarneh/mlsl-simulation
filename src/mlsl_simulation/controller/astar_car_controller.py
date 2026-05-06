import math
from typing import Tuple

from mlsl_simulation.game_model.car import Car 
from mlsl_simulation.game_model.road_network.road_network import Intersection, LaneSegment, CrossingSegment, SegmentInfo, \
    right_direction, direction_sign
from mlsl_simulation.constants import BUFFER, MAX_ACC, MAX_DEC, LANE_MAX_SPEED, CROSSING_MAX_SPEED, LEFT_LANE_CHANGE, \
      RIGHT_LANE_CHANGE, NO_LANE_CHANGE, JUMP_TIME_STEPS, LANECHANGE_TIME_STEPS
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement


class AstarCarController:
    def __init__(self, car: Car, cars:list[Car], reservation_management: ReservationManagement) -> None:
        """
        Initialize the AstarCarController.

        Args:
            game (TrafficEnv): The game environment.
            player (int): The player index.
        """
        self.car = car
        self.cars = cars
        self.first_go = True
        self.reservation_management: ReservationManagement = reservation_management
        # Set by get_accelerate after each call: True iff at least one tried
        # acceleration was rejected solely because of an intersection priority
        # check. get_action uses this to drop a stuck priority and break deadlocks.
        self._last_call_priority_blocked: bool = False

    def get_action(self) -> Tuple[int, int]:
        """
        Determine the next action for the car.

        Args:
            cars (list[car]): A list of all other cars in the game model.
        Returns:
            Tuple[int, int]: A tuple containing the acceleration and lane change values.
        """
        if self.first_go:
            self.first_go = False
            return 0, 0
        
        lane_change = NO_LANE_CHANGE
        reservations = self.reservation_management.get_car_reservations(self.car.id)

        max_possible_acc = self.get_accelerate(reservations)
        priority_blocked = self._last_call_priority_blocked

        if self.car.changing_lane:
            lane_change_segment = self.reservation_management.get_reserved_lane_change_segment(self.car.id)
            if lane_change_segment is None:
                print(f"Issue 4: {self.car.name}")
            else:
                lane_change_segment_info = SegmentInfo(
                        lane_change_segment[1],
                        reservations[0].begin,
                        reservations[0].end,
                        self.car.direction
                    )
                max_possible_acc = min(max_possible_acc,
                                       self.get_accelerate([lane_change_segment_info]))

        elif len(reservations) == 1  \
                and isinstance(reservations[0].segment, LaneSegment) \
                and reservations[0].segment != self.car.goal.lane_segment:
            lane_change = self._choose_lane_change(reservations, max_possible_acc)

        # Break intersection deadlocks: if the only thing forcing us to brake
        # fully was a lower-priority contender at the upcoming intersection,
        # yield our priority so they can proceed.
        max_dec_floor = -min(MAX_DEC, self.car.speed)
        if max_possible_acc <= max_dec_floor and priority_blocked:
            self._drop_pending_priority(reservations)

        return max_possible_acc, lane_change

    def _choose_lane_change(self, reservations: list[SegmentInfo], current_acc: int) -> int:
        """
        Decide a single-step lane change action by comparing the safe acceleration
        of every lane on the current road. The car moves toward the lane with the
        highest acceleration, breaking ties in favor of lanes to the right.
        """
        current_seg_info = reservations[0]
        current_lane_seg = current_seg_info.segment
        assert isinstance(current_lane_seg, LaneSegment)
        current_lane_num = current_lane_seg.lane.num
        is_right_dir = right_direction[current_lane_seg.lane.direction]

        # Reject if the lane change cannot complete before the segment ends.
        remaining_space = current_lane_seg.length - abs(current_seg_info.end)
        if remaining_space < self.car.speed * LANECHANGE_TIME_STEPS:
            return NO_LANE_CHANGE

        adjacent_segments = self.car.get_adjacent_lane_segments(self.reservation_management) or []

        # Map signed lane_diff -> safe acceleration for each collision-free candidate.
        # Sign convention matches the action: negative = right step, positive = left step.
        lane_options: dict[int, int] = {}
        for target_seg in adjacent_segments:
            if target_seg.lane.num == current_lane_num:
                continue
            num_diff = target_seg.lane.num - current_lane_num
            lane_diff = num_diff if is_right_dir else -num_diff
            target_seg_info = SegmentInfo(
                target_seg,
                current_seg_info.begin,
                current_seg_info.end,
                self.car.direction,
            )
            if self._check_collision(target_seg_info):
                continue
            lane_options[lane_diff] = self.get_accelerate([target_seg_info])

        # Best reachable acceleration on each side (only counts if the immediate
        # adjacent lane in that direction is collision-free, since we can only step one).
        right_reachable = RIGHT_LANE_CHANGE in lane_options
        left_reachable = LEFT_LANE_CHANGE in lane_options
        best_right_acc = max((acc for diff, acc in lane_options.items() if diff < 0), default=MAX_DEC) \
            if right_reachable else MAX_DEC
        best_left_acc = max((acc for diff, acc in lane_options.items() if diff > 0), default=MAX_DEC) \
            if left_reachable else MAX_DEC

        if right_reachable and best_right_acc >= current_acc and best_right_acc >= best_left_acc:
            right_seg = self.car.get_adjacent_lane_segment(self.reservation_management, RIGHT_LANE_CHANGE)
            right_seg_info = SegmentInfo(
                right_seg,
                current_seg_info.begin,
                current_seg_info.end,
                self.car.direction,
            )
            if self._check_collision(right_seg_info):
                return RIGHT_LANE_CHANGE
        if left_reachable and best_left_acc > current_acc:
            left_seg = self.car.get_adjacent_lane_segment(self.reservation_management, LEFT_LANE_CHANGE)
            left_seg_info = SegmentInfo(
                left_seg,
                current_seg_info.begin,
                current_seg_info.end,
                self.car.direction,
            )
            if self._check_collision(left_seg_info):
                return LEFT_LANE_CHANGE
            return LEFT_LANE_CHANGE
        return NO_LANE_CHANGE

    def get_accelerate(self, segments: list[SegmentInfo]) -> int:
        """
        Return the largest legal-and-safe acceleration in [-MAX_DEC, MAX_ACC]
        for the supplied reservation list.

        Legal: keeps speed below the car's max_speed and the slowest reserved
        segment's max_speed.

        Safe: the projected reservation does not overlap a leading car, every
        crossing-segment time-of-arrival is strictly later than every earlier-
        reserved car's time-of-departure, and any newly entered crossing
        respects the intersection-priority ordering.

        Side effect: writes self._last_call_priority_blocked. get_action reads
        it to decide whether to drop a stuck priority and break a deadlock.
        """
        self._last_call_priority_blocked = False
        if not segments:
            return MAX_ACC

        seg_speed_cap = min(s.segment.max_speed for s in segments)
        legal_max = min(MAX_ACC,
                        self.car.max_speed - self.car.speed,
                        seg_speed_cap - self.car.speed)
        max_dec = -min(MAX_DEC, self.car.speed)

        if legal_max < max_dec:
            return max_dec

        for acceleration in range(legal_max, max_dec - 1, -1):
            new_speed = self.car.speed + acceleration

            if self.car.changing_lane and not self._lane_change_will_complete(segments, new_speed):
                continue

            projected = self._project_reservation(segments, new_speed)
            if projected is None:
                continue

            unsafe, by_priority = self._violates_safety(segments, projected, new_speed)
            if by_priority:
                self._last_call_priority_blocked = True
            if not unsafe:
                return acceleration

        return max_dec

    def _lane_change_will_complete(self, segments: list[SegmentInfo], new_speed: int) -> bool:
        """During a lane change the car must remain inside the current lane segment
        for the remaining LANECHANGE_TIME_STEPS. Reject any acceleration that would
        push it past the segment end too early."""
        info = self.reservation_management.get_reserved_lane_change_segment(self.car.id)
        if info is None:
            return False
        remaining_time = LANECHANGE_TIME_STEPS - (self.car.time - info[0])
        if remaining_time <= 0:
            return True
        required_space = new_speed * remaining_time
        available_space = segments[-1].segment.length - abs(segments[-1].end)
        return available_space >= required_space

    def _project_reservation(self, segments: list[SegmentInfo], new_speed: int) -> list[SegmentInfo] | None:
        """Build the full reservation list that would result from advancing the
        car by new_speed for one tick (extending into the next planned segments
        when the new braking distance no longer fits inside the current one).

        Returns None when extension is required but no next segments are known."""
        last = segments[-1]
        last_sign = direction_sign[last.direction]
        new_brk_dist = self.car.get_braking_distance(new_speed) + new_speed
        reserved_length = sum(abs(s.end - s.begin) for s in segments)
        prefix = list(segments[:-1])

        if new_brk_dist <= reserved_length:
            upto_last = reserved_length - abs(last.end - last.begin)
            new_end_off = max(self.car.size + BUFFER, new_brk_dist - upto_last + abs(last.begin))
            return prefix + [SegmentInfo(last.segment, last.begin,
                                         last_sign * new_end_off, last.direction)]

        potential_jump = new_brk_dist - reserved_length

        if abs(last.end) + potential_jump < last.segment.length:
            new_end_off = max(self.car.size + BUFFER, abs(last.end) + potential_jump)
            return prefix + [SegmentInfo(last.segment, last.begin,
                                         last_sign * new_end_off, last.direction)]

        next_segments = self.car.get_next_segment(self.reservation_management, last.segment)
        if not next_segments or len(next_segments) < 2:
            return None

        full_last = SegmentInfo(last.segment, last.begin,
                                last_sign * last.segment.length, last.direction)
        projected = prefix + [full_last]
        potential_jump -= (last.segment.length - abs(last.end))

        new_segs = next_segments[1:]
        prev_dir = last.direction
        for i, seg in enumerate(new_segs):
            if isinstance(seg, CrossingSegment):
                next_after = new_segs[i + 1] if i + 1 < len(new_segs) else None
                seg_dir = next(
                    (d for d, s in seg.connected_segments.items() if s is next_after),
                    prev_dir,
                )
                projected.append(SegmentInfo(seg, 0, direction_sign[seg_dir] * seg.length,
                                             seg_dir, seg_dir != prev_dir))
                potential_jump -= seg.length
            elif isinstance(seg, LaneSegment):
                seg_dir = seg.lane.direction
                end_off = max(self.car.size + BUFFER, potential_jump)
                projected.append(SegmentInfo(seg, 0, direction_sign[seg_dir] * end_off,
                                             seg_dir, seg_dir != prev_dir))
            else:
                continue
            prev_dir = seg_dir

        return projected

    def _violates_safety(self, current_segments: list[SegmentInfo],
                         projected: list[SegmentInfo],
                         new_speed: int) -> Tuple[bool, bool]:
        """Return (unsafe, blocked_by_priority).

        Order of checks:
          1. Time-of-arrival vs every earlier-reserved car at every crossing in
             the projection. The car must enter strictly after each earlier car
             has finished traversing.
          2. Intersection priority for crossings that are NEW in the projection
             (not already in the car's current reservation). The car may only
             enter when no other contender at the same intersection holds an
             earlier (smaller) priority value.
          3. Trailing-car overlap on the projection's final lane segment.
        """
        # CROSSING_MAX_SPEED is the cap inside any crossing; on the upstream
        # lane the car can be travelling faster, so use the larger of (new_speed,
        # CROSSING_MAX_SPEED) as the upper bound on approach speed -- this gives
        # the smallest plausible time-to-enter, which is the conservative side
        # for "must enter strictly after others leave".
        approach_speed = max(new_speed, CROSSING_MAX_SPEED)
        cumulative = 0
        for i, seg_info in enumerate(projected):
            seg = seg_info.segment
            cars_on_seg = self.reservation_management.get_cars_on_segment(seg)
            if self.car.id in cars_on_seg:
                prior = cars_on_seg[:cars_on_seg.index(self.car.id)]
            else:
                prior = list(cars_on_seg)
            if isinstance(seg, CrossingSegment):
                time_to_enter_abs = self.car.time + math.ceil(cumulative / approach_speed)
                if prior:
                    leave_times = [seg.crossing_segment_state.get_time_to_leave(other)
                                   for other in prior]
                    leave_times = [t for t in leave_times if t is not None]
                    if leave_times and time_to_enter_abs <= max(leave_times):
                        return True, False
            else:
                if len(projected) > 1:
                    for o_car_id in prior :
                        o_seg_info = self.reservation_management.get_car_reservation(o_car_id, 0)
                        if o_seg_info.segment == seg:
                            if abs(projected[-1].end) > abs(o_seg_info.end):
                                return True, False

            cumulative += abs(seg_info.end - seg_info.begin)

        current_segment_ids = {id(s.segment) for s in current_segments}
        for seg_info in projected:
            if isinstance(seg_info.segment, CrossingSegment) and id(seg_info.segment) not in current_segment_ids:
                intersection: Intersection = seg_info.segment.intersection
                my_priority = intersection.intersection_state.get_car_priority(self.car.id)
                if my_priority is not None:
                    for other_id, other_time in intersection.intersection_state.get_priority_items():
                        if other_id != self.car.id and other_time < my_priority:
                            return True, True
                break

        final = projected[-1]
        if isinstance(final.segment, LaneSegment) and self._final_lane_overlap(final):
            return True, False

        return False, False

    def _final_lane_overlap(self, seg_info: SegmentInfo) -> bool:
        """True if the projection's tail in this lane segment would overlap a
        leading car's worst-case forward-projected reservation in the same
        segment. The leading car's worst case shifts its reservation forward by
        speed + min(MAX_DEC, speed) -- the most it could move next tick."""
        my_end = abs(seg_info.end)
        for other_id in self.reservation_management.get_cars_on_segment(seg_info.segment):
            if other_id == self.car.id:
                continue
            other_segs = self.reservation_management.get_car_reservations(other_id)
            if [segment_info.segment for segment_info in other_segs].index(seg_info.segment) > 0:
                continue
            other_seg_info = next((s for s in other_segs if s.segment == seg_info.segment), None)
            if other_seg_info is None:
                continue
            other_car = next((c for c in self.cars if c.id == other_id), None)
            if other_car is None:
                continue
            forward = other_car.speed + min(MAX_DEC, other_car.speed)
            o_begin = abs(other_seg_info.begin) + forward
            o_end = abs(other_seg_info.end) + forward
            if min(o_begin, o_end) <= my_end <= max(o_begin, o_end):
                return True
        return False

    def _drop_pending_priority(self, segments: list[SegmentInfo]) -> None:
        """Yield this car's intersection priority at the upcoming intersection.
        Called by get_action when get_accelerate was forced to brake fully and
        the priority check rejected at least one tried acceleration -- this
        prevents priority FIFO from holding the queue when the head of the
        queue cannot move for unrelated reasons."""
        for seg_info in reversed(segments):
            seg = seg_info.segment
            if isinstance(seg, LaneSegment) and seg.end_crossing is not None:
                state = seg.end_crossing.intersection.intersection_state
                if state.get_car_priority(self.car.id) is not None:
                    state.pop_car_priority(self.car.id)
                return
            if isinstance(seg, CrossingSegment):
                return
    
    def _check_collision(self, seg_info: SegmentInfo):
        for other_car_id in self.reservation_management.get_cars_on_segment(seg_info.segment):
            if other_car_id != self.car.id:
                other_car_seg_info = next(o_seg_info for o_seg_info in self.reservation_management.get_car_reservations(other_car_id) if o_seg_info.segment == seg_info.segment)
                begin = abs(seg_info.begin)
                end = abs(seg_info.end)
                o_begin = abs(other_car_seg_info.begin)
                o_end = abs(other_car_seg_info.end)
                if self.getOverlap(min(begin, end), max(begin, end), 
                               min(o_begin, end), max(o_begin, o_end)) > 0: 
                    return True
        return False
    
    def getOverlap(self, begin_1, end_1, begin_2, end_2):
        return max(0, min(end_1, end_2) - max(begin_1, begin_2))