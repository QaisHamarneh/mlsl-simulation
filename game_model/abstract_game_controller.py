from abc import ABC, abstractmethod

class AbstractGameController(ABC):

    @abstractmethod
    def run() -> None:
        ...