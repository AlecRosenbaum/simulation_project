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

    def __init__(self, elevator_id, logger, building, capacity=settings.DEFAULT_CAPACITY):
        self.state = self.States.IDLE
        self.elevator_id = elevator_id
        self.logger = logger
        self.building = building
        self.capacity = capacity
        self.floor = building.floor[0]
        self.passengers = []
        self.curr_dest = None

    def fill_elevator(self):
        """Fill the elevator with passengers using the generator"""
        if len(self.passengers) <= 0:
            return
        #Check if the elevator is going up or down
        #Then, fill it with as many passengers as that floor has
        #Also, remove the passenger from the floor if they get on the elevator
        #and update their state
        if self.curr_dest > self.floor:
            for entry in self.floor.get_up(self.capacity-len(self.passengers)):
                entry[1].update_state(entry[1].States.PRE_SERVICE)
                self.passengers.append(entry[1])
                self.floor.remove_from_queue(entry[0])
                self.capacity += 1
        else:
            for entry in self.floor.get_down(self.capacity-len(self.passengers)):
                entry[1].update_state(entry[1].States.PRE_SERVICE)
                self.passengers.append(entry[1])
                self.floor.remove_from_queue(entry[0])
                self.capacity += 1


    def empty_elevator(self):
        """Empty anyone who is getting off on this floor
        Once they've gotten off, they're discarded from the simulation.
        """
        for person in self.passengers:
            if person.destination == self.floor:
                person.update_state(person.States.POST_SERVICE)
                self.passengers.remove(person)

    def update_state(self, new_state):
        """Update the state of the elevator
        For now it just uses a generic time.
        """
        self.state = new_state
        #log state

        if self.state == self.States.IDLE or self.state == self.States.STOPPED:
            self.curr_dest = self.next_dest()

            if self.curr_dest is None:
                settings.FEQ.put_nowait((settings.CURR_TIME + 1, self, self.States.IDLE))
            else:
                settings.FEQ.put_nowait((settings.CURR_TIME + 1, self, self.States.MOVING))
        else:
            settings.FEQ.put_nowait((settings.CURR_TIME + 1, self, self.States.STOPPED))


    def next_dest(self):
        """This must be implented in each subclass, based on the algorithm"""
        raise NotImplementedError()


class BasicElevator(Elevator):
    """This simple elevator will just repond to calls as they come,
    and drop people off if its their floor.
    """
    def next_dest(self):


#class NearestElevator(Elevator):
#    """Uses the nearest elevator heuristic"""
#    pass
