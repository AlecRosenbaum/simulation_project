"""handles person and arrival models"""

# imports
from enum import Enum, auto


class Person:
    """models a person"""

    class States(Enum):
        """states implemented for stations"""
        IDLE = auto()
        QUEUED = auto()
        PRE_SERVICE = auto() # walking onto elevator
        SERVICE = auto() # elevator moving between floors
        POST_SERVICE = auto() # walking off of elevator

    def __init__(self, person_id, logger):
        """ Person Constructor

        Args:
            person_id: unique id
            logger: instance of a logger
        """
        self.state = self.States.IDLE
        self.person_id = person_id
        self.logger = logger
        self.curr_elevator = None

    def update_state(self, state):
        """updates current state. if none specified, updates based on current state variables.

        Args:
            state: instance of self.States class
        """
        self.state = state


class ArrivalGenerator:
    """models floor arrivals based on source data (can save/load data)"""
    pass
