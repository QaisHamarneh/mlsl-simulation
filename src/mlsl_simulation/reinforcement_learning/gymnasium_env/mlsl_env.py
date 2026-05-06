import pyglet
import time

from abc import ABC, abstractmethod
from gymnasium import Env
from gymnasium import spaces
from typing import Tuple, Dict
from mlsl_simulation.game_model.game_model import TrafficEnv
from mlsl_simulation.constants import MAX_ACC, MAX_DEC, TIME_PER_FRAME
from mlsl_simulation.gui.pyglet_gui import GameWindow
from mlsl_simulation.gui.render_mode import RenderMode
from mlsl_simulation.reinforcement_learning.gymnasium_env.observation_spaces.abstract_observation import Observation

class MlslEnv(Env, ABC):
    """Abstract Gymnasium environment for MLSL traffic simulation.
    
    This class provides the bridge between the traffic simulation and reinforcement learning
    algorithms by implementing the Gymnasium API. It manages the simulation loop where the
    agent takes actions and receives observations and rewards.
    
    ## Core Gymnasium Loop
    
    The interaction follows the standard RL loop:
    ```
    obs, info = env.reset()
    while not done:
        obs, reward, terminated, truncated, info = env.step(action)
        env.render()  # optional
    ```
    
    ## How to Create a Concrete Environment
    
    Subclass MlslEnv with a specific reward function:
    
    ```python
    @register_reward_model(RewardType.MY_REWARD)
    class MyRewardEnv(MlslEnv):
        def compute_reward(self) -> float:
            # Return numeric reward based on game state
            if collision:
                return -10.0
            elif reached_goal:
                return 100.0
            else:
                return -0.01
    ```
    
    The decorator automatically registers it with the reward_registry for easy lookup.
    
    ## Action Space
    
    MultiDiscrete with 2 components:
    - Acceleration: [0, MAX_ACC + MAX_DEC - 1] → maps to [-MAX_DEC, MAX_ACC]
    - Lane change: [0, 1, 2] → maps to [-1, 0, 1]
    
    ## Episode Termination
    
    Episodes end when:
    - `done=True`: Agent reached goal or collision (terminal state)
    - `truncated=True`: Deadlock detected (time limit equivalent)
    
    ## Attributes
        game_model (TrafficEnv): The traffic simulation instance
        observation_model (Observation): Converts game state to observations
        game_window (GameWindow | None): Pygame window for rendering
        action_space (spaces.MultiDiscrete): Agent action space specification
        observation_space (spaces.Space): Agent observation space specification
        render_mode (str | None): Rendering mode ('human' or None)
    """

    def __init__(self, 
                 game_model: TrafficEnv,
                 observation_model: Observation,
                 render_mode: None | RenderMode = None,
                 show_reservation: bool = True,
                 ):
        """Initialize the Gymnasium environment.
        
        Args:
            game_model (TrafficEnv): The traffic simulation to control.
            observation_model (Observation): Model for generating observations from game state.
            render_mode (None | str): Rendering mode. 'human' for visual display, None for headless.
        """
        
        self.render_mode = render_mode
        self.show_reservation = show_reservation

        self.game_model: TrafficEnv = game_model

        if self.render_mode == RenderMode.GUI:
            self.game_window = GameWindow(
                self.game_model.cars, 
                self.game_model.roads, 
                self.game_model.reservation_management, 
                self.show_reservation
                )
        else:
            self.game_window = None

        self.agent_score: int = self.game_model.agent_car.score

        self.observation_model: Observation = observation_model

        # accelaration = [0, MAX_DEC + MAX_ACC - 1] and lange changes = [0, 2]
        self.action_space = spaces.MultiDiscrete([MAX_ACC + MAX_DEC, 3])
        self.observation_space = self.observation_model.space()

        self.done: bool = False
        self.truncated: bool = False

        self.map_history = self.game_model.game_history.map.copy()
        self.car_history = self.game_model.game_history.list_of_cars.copy()
        self.action_history = self.game_model.game_history.action_history_dict.copy()
        self.action_length_history = self.game_model.game_history.action_length

    def reset(self, seed: None | int = None, options: None | Dict = None) -> Tuple[spaces.Space, Dict[str, any]]:
        """Reset the environment to initial state.
        
        Resets the traffic simulation to its starting condition and returns the
        initial observation. This must be called before each episode.
        
        Args:
            seed (None | int): Random seed for reproducibility (currently unused).
            options (None | Dict): Additional options (currently unused).
        
        Returns:
            Tuple[spaces.Space, Dict]:
                - observation: Initial observation from the observation model
                - info: Dictionary with auxiliary information for debugging
        """
        self.game_model.reset()
        return (self.observation_model.observe(), self._get_info())
    
    def step(self, actions: Tuple[int, int]) -> Tuple[spaces.Space, float, bool, bool, Dict[str, any]]:
        """Execute one environment step.
        
        Processes the agent's action, updates the simulation, and returns the
        new observation, reward, and episode status.
        
        Args:
            actions (Tuple[int, int]): Two-element action vector:
                - actions[0]: Acceleration command [0, MAX_ACC + MAX_DEC - 1]
                - actions[1]: Lane change command [0, 1, 2]
        
        Returns:
            Tuple[observation, reward, done, truncated, info]:
                - observation: New observation from observation model
                - reward: Scalar reward from compute_reward()
                - done (bool): True if episode is terminal (goal/collision)
                - truncated (bool): True if episode ended by deadlock
                - info (dict): Debugging information
        """
        # accelaration = [-MAX_DEC, MAX_ACC] and lange changes = [-1, 0, 1]
        if actions[0] > MAX_DEC - 1:
            decoded_action = (actions[0] - MAX_DEC + 1, actions[1] - 1)
        else:
            decoded_action = (actions[0] - MAX_DEC, actions[1] - 1)

        self.result = self.game_model.play_step(action=decoded_action)

        observation = self.observation_model.observe()

        reward = self.compute_reward()

        self.done = False
        self.truncated = False

        if self.result == "game_over":
            self.done = True
        elif self.result == "deadlock":
            self.truncated = True

        info = self._get_info() # for debugging

        if self.done or self.truncated:
            self.map_history = self.game_model.game_history.map.copy()
            self.car_history = self.game_model.game_history.list_of_cars.copy()
            self.action_history = self.game_model.game_history.action_history_dict.copy()
            self.action_length_history = self.game_model.game_history.action_length

        return observation, reward, self.done, self.truncated, info
    
    def render(self):
        """Render the current game state visually.
        
        If render_mode is RenderMode.GUI, displays the traffic simulation on screen
        with appropriate frame rate control. Does nothing if render_mode is None.
        """
        if self.game_window:
            self._render_frame()
            time.sleep(1.0 / TIME_PER_FRAME)

    def _render_frame(self):
        """Render a single frame to the display window.
        
        Handles display events, drawing, and frame refresh using Pyglet.
        """
        self.game_window.dispatch_events()
        self.game_window.on_draw()
        pyglet.clock.tick()
        self.game_window.flip()

    @abstractmethod
    def compute_reward(self) -> float:
        """Compute the reward signal for the current step.
        
        This is implemented by subclasses to define the reward strategy.
        The reward signal guides learning by evaluating the quality of actions.
        
        Returns:
            float: Scalar reward value. Convention:
                - Positive for desirable outcomes (reaching goal, efficient progress)
                - Negative for undesirable outcomes (collisions, inefficient behavior)
                - Small magnitude for step-wise costs/bonuses
        
        Example:
            ```python
            def compute_reward(self) -> float:
                if self.game_model.collision_detected:
                    return -100.0
                elif self.game_model.agent_reached_goal:
                    return 1000.0
                else:
                    return -0.1  # small step cost
            ```
        """
        ...
    
    def _get_info(self) -> Dict:
        """Get auxiliary information for debugging.

        Returns:
            Dict: Debugging information (empty dict in base implementation).
        """
        return {}