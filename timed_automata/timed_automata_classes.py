from typing import Callable

from game_model.game_model import TrafficEnv


class State:
    def __init__(self,
                 name: str,
                 time_invariants: list[Callable[[list[int]], bool]] = None,
                 game_invariants: list[Callable[[TrafficEnv, int], bool]] = None,
                 transitions: list = None):
        self.name = name
        self.time_invariants = []
        if time_invariants is not None:
            self.time_invariants = time_invariants
        self.game_invariants = []
        if game_invariants is not None:
            self.game_invariants = game_invariants
        self.transitions = []
        if transitions is not None:
            self.transitions = transitions

    def valid(self, game: TrafficEnv, player: int, clocks: list[int]):
        valid_time = all([invariant(clocks) for invariant in self.time_invariants])
        valid_game = all([invariant(game, player) for invariant in self.game_invariants])
        return valid_time and valid_game


class Transition:
    def __init__(self,
                 start: State,
                 end: State,
                 reset: list[int],
                 time_guards: list[Callable[[list[int]], bool]] = None,
                 game_guards: list[Callable[[TrafficEnv, int], bool]] = None,
                 updates: list[Callable[[], None]] = None):
        self.start = start
        self.end = end
        self.reset = reset
        self.time_guards = []
        if time_guards is not None:
            self.time_guards = time_guards
        self.game_guards = []
        if game_guards is not None:
            self.game_guards = game_guards
        self.updates = []
        if updates is not None:
            self.updates = updates

    def enabled(self, game: TrafficEnv, player: int, clocks: list[int]):
        time_guards_enabled = all([guard(clocks) for guard in self.time_guards])
        game_guards_enabled = all([guard(game, player) for guard in self.game_guards])
        new_clocks = clocks.copy()
        for clock in self.reset:
            new_clocks[clock] = 0
        end_state_valid = self.end.valid(game, new_clocks)
        return time_guards_enabled and game_guards_enabled and end_state_valid


class TimedAutomata:
    def __init__(self,
                 game: TrafficEnv,
                 player: int,
                 states: list[State],
                 start_state: State,
                 transitions: list[Transition],
                 clocks: int = None,
                 variables: dict[str, int] = None):

        self.player = player
        self.game = game
        self.states = states
        self.start_state = start_state
        self.transitions = transitions
        self.variables = variables
        if self.variables is None:
            self.variables = {}
        self.clocks = clocks
        if self.clocks is None:
            self.clocks = []

        self.current_state = start_state

    def valid(self):
        return self.current_state.valid(self.game, self.player, self.clocks)

    def delay(self, delay):
        return [clock + delay for clock in self.clocks]

    def move(self, delay: float = None, transition: Transition = None):
        if delay is None:
            if self.current_state != transition.start:
                return False
            if not transition.enabled(self.game, self.player, self.clocks):
                return False
            for clock in transition.reset:
                self.clocks[clock] = 0
            self.current_state = transition.end
            for update in transition.updates:
                update()
        else:
            self.clocks = self.delay(delay)
        return self.valid()


if __name__ == '__main__':
    s0 = State('s0', time_invariants=[lambda l:l[0] < 5])
    s1 = State('s1', time_invariants=[lambda l:l[0] > 4])

    t1 = Transition(s0, s1, [], time_guards=[lambda l: l[0] >= 4])
    t2 = Transition(s1, s0, [0])

    a = TimedAutomata(None, 0, [s0, s1], s0, [t1, t2], 1, None)

    print(a.current_state.name)
    print(a.clocks)
    a.move(delay=2)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t1)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t2)
    print(a.current_state.name)
    print(a.clocks)
    a.move(delay=2)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t1)
    print(a.current_state.name)
    print(a.clocks)
    a.move(delay=0.1)
    a.move(transition=t1)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t2)
    print(a.current_state.name)
    print(a.clocks)
