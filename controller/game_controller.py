from typing import List
from game_model.constants import TIME_PER_FRAME, FLASH_CYCLE
from game_model.game_model import TrafficEnv
from game_model.Tester import SimulationTester
from game_model.road_network import Road
from gui.pyglet_gui import CarsWindow
from gymnasium_env.mlsl_env import MlslEnv
from learning.qlearning import Qlearning
from learning.epsilon_greedy import EpsilonGreedy
from learning.params import Params
import numpy as np
import pyglet

class GameController:
    def __init__(self, 
                 gui: bool, 
                 roads: List[Road], 
                 npcs: int,
                 agents: int = 0,  
                 debug: bool = False, 
                 test_mode: List[str] = None):
        
        self.gui = gui

        self.game_model: TrafficEnv = TrafficEnv(roads=roads, npcs=npcs, agents=agents)
        self.game_over: bool = False

        self.debug: bool = debug
        self.test_mode = test_mode
        if test_mode is not None:
            self.sim_tester: SimulationTester = SimulationTester(self.game_model, self.test_mode)

        params = Params(
            total_episodes=2000,
            learning_rate=0.8,
            gamma=0.95,
            epsilon=0.1,
            seed=123,
            n_runs=20,
            action_size=None,
            state_size=None,
        )
        rng = np.random.default_rng(params.seed)

        self.learner = Qlearning(
            learning_rate=params.learning_rate,
            gamma=params.gamma,
            state_size=params.state_size,
            action_size=params.action_size,
        )
        self.explorer = EpsilonGreedy(
            epsilon=params.epsilon,
            rng=rng
        )

    def run_game(self) -> None:
        if self.gui:
            self.frame_count = 0
            self._run_gui()
        else:
            self._run_headless()

    def _run_headless(self) -> None:
        self.env = MlslEnv(game_model=self.game_model)

        while not self.game_over:
            actions = [(1,0) for i in range(self.game_model.agents)]
            self.game_over, self.observation, self.reward = self.env.step(actions=actions)

            if not self.game_over:
                self.game_over = self._check_deadlock()

        self._game_over_state(self.game_model)

    def _run_gui(self) -> None:
        self.window = CarsWindow(debug=self.debug, game_model=self.game_model)
        self.env = MlslEnv(game_model=self.game_model)

        self.learner.reset_qtable
        self.state = self.env.reset()

        pyglet.clock.schedule_interval(self._update_gui, (1 / TIME_PER_FRAME))
        pyglet.app.run()

    def _update_gui(self, delta_time: float) -> None:
        if not self.window.pause and self.frame_count % TIME_PER_FRAME == 0:
            self.frame_count = 0

            actions = [self.explorer.choose_action(self.env.action_space, self.state) for i in range(self.game_model.agents)]
            self.game_over, new_state, self.reward = self.env.step(actions=actions)

            self.learner.update(self.state, actions, self.reward, new_state)
            self.state = new_state

            if not self.game_over:
                self.game_over = self._check_deadlock()

            if self.game_over:
                self._game_over_state(self.game_model)
                self.window.pause = True

        elif not self.window.pause:
            self.frame_count += TIME_PER_FRAME

    def _check_deadlock(self) -> bool:
        deadlock = [True if car.speed == 0 else False for car in self.game_model.cars]
        if all(deadlock):
            print("___________________________________________________________________________")
            print("Deadlock between all cars.")
            print("___________________________________________________________________________")
            return True
        else:
            return False
        
    def _game_over_state(self, game_model: TrafficEnv) -> None:
        print(f"Game Over:")
        for car in game_model.cars:
            print(f"car {car.name} score {car.score}")
            #Todo: print reason, if car is dead
