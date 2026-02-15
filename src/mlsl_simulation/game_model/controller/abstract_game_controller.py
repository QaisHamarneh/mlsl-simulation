from abc import ABC, abstractmethod
from typing import List

from mlsl_simulation.game_model.road_network.road_network import Road
from mlsl_simulation.gui.render_mode import RenderMode

class AbstractGameController(ABC):
    def __init__(
            self,
            roads: List[Road],
            players: int,
            render_mode: RenderMode,
            show_reservation: bool,
            ):
        
        self.roads = roads
        self.players = players
        self.render_mode = render_mode
        self.show_reservation = show_reservation
        

    @abstractmethod
    def run() -> None:
        ...