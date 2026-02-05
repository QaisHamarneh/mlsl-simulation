from abc import ABC, abstractmethod
from mlsl_simulation.game_model.game_model import TrafficEnv
from mlsl_simulation.game_model.reservations.reservation_management import ReservationManagement
from gymnasium import spaces

class Observation(ABC):
    """Abstract base class for observation models in the RL environment.
    
    Observation models define how the agent perceives the traffic simulation state.
    They translate the internal game state into normalized numeric data suitable for
    machine learning algorithms.
    
    Different observation implementations can emphasize different aspects:
    - Numeric: Flattened vectors of normalized values
    - Image-based: Bird's eye view renderings (future)
    - Graph-based: Graph representations of road network (future)
    
    ## How to Create a Custom Observation Model
    
    1. Create an enum in `observation_model_types.py`:
        ```python
        class ObservationModelType(Enum):
            MY_OBSERVATION = auto()
        ```
    
    2. Create a class inheriting from Observation:
        ```python
        @register_observation_model(ObservationModelType.MY_OBSERVATION)
        class MyObservation(Observation):
            def space(self) -> spaces.Space:
                # Define gymnasium space
                return spaces.Box(...)
            
            def observe(self) -> numpy.ndarray:
                # Return current observation
                return np.array(...)
        ```
    
    3. The decorator registers it automatically with the observation_registry.
    
    ## Attributes
        game_model (TrafficEnv): Reference to the traffic simulation model
        reservation_management (ReservationManagement): Handles car reservations
    """
    
    def __init__(self, game_model: TrafficEnv) -> None:
        """Initialize the observation model.
        
        Args:
            game_model (TrafficEnv): The traffic simulation that will be observed.
        """
        self.game_model = game_model
        self.reservation_management: ReservationManagement = self.game_model.reservation_management

    @abstractmethod
    def space(self) -> spaces.Space:
        """Define the gymnasium observation space.
        
        This describes the structure and bounds of observations the agent will receive.
        It should match the output format of the observe() method.
        
        Returns:
            spaces.Space: A gymnasium space object (Box, Discrete, MultiDiscrete, etc.)
                that defines valid observation values and shapes.
        
        Example:
            >>> return spaces.Box(low=0, high=1, shape=(128,), dtype=np.float32)
        """
        ...

    @abstractmethod
    def observe(self):
        """Generate observation of current game state.
        
        This method is called every game step to provide the agent with information
        about the world. The returned observation should match the space() specification.
        
        Returns:
            Observation data in the format specified by space().
            Typically a normalized numpy array in range [0, 1].
        
        Example:
            >>> return np.array([normalized_lane_data, normalized_car_data, ...], dtype=np.float32)
        """
        ...