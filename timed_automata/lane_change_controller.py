from game_model.constants import *
from game_model.road_network import LaneSegment
from timed_automata.timed_automata_classes import TimedAutomata, State, Transition

from game_model.game_model import TrafficEnv


def collision_check(game: TrafficEnv, player: int):
    car = game.cars[player]
    segment = car.res[0]
    seg_info = car.get_segment_info(segment)
    begin = abs(seg_info["begin"])
    end = abs(seg_info["end"])
    for other_car in segment.cars:
        if other_car != car:
            other_car_seg_info = other_car.get_segment_info(segment)
            o_begin = abs(other_car_seg_info["begin"])
            o_end = abs(other_car_seg_info["end"])
            if begin <= o_begin <= end:
                return False
            elif begin <= o_end <= end:
                return False
    return True


def potential_collision_check(game: TrafficEnv, player: int, lane_diff: int):
    car = game.cars[player]
    segment = car.get_adjacent_lane_segment(lane_diff)
    if segment is None:
        return False
    seg_info = {
        "seg": segment,
        "dir": car.direction,
        "turn": False,
        "begin": car.res[0]["begin"],
        "end": car.res[0]["end"]
    }
    begin = abs(seg_info["begin"])
    end = abs(seg_info["end"])
    for other_car in segment.cars:
        if other_car != car:
            other_car_seg_info = other_car.get_segment_info(segment)
            o_begin = abs(other_car_seg_info["begin"])
            o_end = abs(other_car_seg_info["end"])
            if begin <= o_begin <= end:
                return False
            elif begin <= o_end <= end:
                return False
    return True


def pc1(game: TrafficEnv, player: int):
    return potential_collision_check(game, player, 1)


def pc2(game: TrafficEnv, player: int):
    return potential_collision_check(game, player, -1)


class LaneChangeController:
    def __init__(self,
                 game: TrafficEnv,
                 player: int):
        self.game = game
        self.player = player

        self.clocks = [0]
        self.variables = {'l': 0}

        self.max_claim_time = LANE_CHANGE_LIMIT
        self.lane_change_time = LANE_CHANGE_LIMIT
        self.lane_change_step = LANE_CHANGE_STEPS

        # def set_automata(self):
        self.q0 = State("q0", game_invariants=[collision_check])
        self.q2 = State("q2",
                        game_invariants=[potential_collision_check],
                        time_invariants=[lambda l: l[0] <= self.max_claim_time])
        self.q3 = State("q3",
                        time_invariants=[lambda l: l[0] <= self.lane_change_time])

        self.t1 = Transition(start=self.q0,
                             end=self.q2,
                             reset=[0],
                             game_guards=[pc1],
                             updates=[self.l_1])
        self.t2 = Transition(start=self.q0,
                             end=self.q2,
                             reset=[0],
                             game_guards=[pc2],
                             updates=[self.l_2])
        self.t3 = Transition(start=self.q2,
                             end=self.q3,
                             reset=[0],
                             game_guards=[self.pc])
        self.t4 = Transition(start=self.q3,
                             end=self.q0,
                             reset=[0],
                             time_guards=[lambda l: l[0] <= self.lane_change_step])

        self.automata = TimedAutomata(
            game=self.game,
            player=self.player,
            states=[self.q0, self.q2, self.q3],
            start_state=self.q0,
            transitions=[self.t1, self.t2],
            clocks=self.clocks,
            variables=self.variables)

    def l_1(self):
        self.variables['l'] = 1

    def l_2(self):
        self.variables['l'] = -1

    def pc(self, game: TrafficEnv, player: int):
        return potential_collision_check(game, player, self.variables['l'])
