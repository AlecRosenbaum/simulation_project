"""All of the elevator classes"""

# standard imports
from enum import Enum, auto

# local imports
import settings


class Elevator:
    """base abstract class for elevators"""

    class States(Enum):
        """states implemented for elevators"""
        IDLE = auto()
        STOPPED = auto() # stopped at a floor for servicing
        MOVING = auto() # moving between floors

    def __init__(self, elevator_id, logger, capacity=settings.DEFAULT_CAPACITY):
        self.state = self.States.IDLE
        self.elevator_id = elevator_id
        self.logger = logger
        self.capacity = capacity


class NearestElevator(Elevator):
    """Uses the nearest elevator heuristic"""
    pass
