"""All of the elevator classes"""

# standard imports
from enum import Enum, auto

# local imports
import settings

class Elevator:
    """base abstract class for elevators"""

    elevator_cnt = 0

    class States(Enum):
        """states implemented for elevators"""
        IDLE = auto()
        STOPPED = auto() # stopped at a floor for servicing
        MOVING = auto() # moving between floors

    def __init__(self, logger, building, capacity=settings.DEFAULT_CAPACITY):
        self.state = self.States.IDLE
        self.id = self.__class__.elevator_cnt
        self._logger = logger
        self._building = building
        self.capacity = capacity # max capacity
        self.curr_floor = building.floor['1'] # starts on 1st floor
        self.passengers = []
        self.next_dest = None

        self.__class__.elevator_cnt += 1

    def _load_passengers(self, destinations=None, direction=None):
        """load passengers from queue at current floor

        Loads passengers. If destinations is specified, loads only passengers traveling particular
        destinations. If direction is specified, load only those going that direction. If neither
        are specified, loads all at that floor.

        Accpets at most one parameter.

        Args:
            destinations: (optional) List of floors. Loads passengers traveling to these floors.
                          First floors specified are prioritized if capacity is met.
            direction: (optional) "up" or "down"
        """

        # if elevator has no capacity, return
        if not len(self.passengers) < self.capacity:
            return

        # only one argument may be specified
        if destinations is not None and direction is not None:
            raise Exception("Only one argument may be specified (either desitnation or direction).")

        if destinations is not None: # destinations specified
            for floor in destinations: # for each specified floor
                # quanitify new passengers
                new_passengers = []
                for _, i in self.curr_floor.queue:
                    if len(self.passengers)+len(new_passengers) >= self.capacity:
                        break
                    if i.destination == floor:
                        new_passengers.append(i)

                # add new passengers to elevator
                for i in new_passengers:
                    self._add_passenger(i)

        elif direction is not None: # direction is specified
            if direction == "up":
                for i in self.curr_floor.up(self.rem_cap()):
                    self._add_passenger(i)
            elif direction == "down":
                for i in self.curr_floor.down(self.rem_cap()):
                    self._add_passenger(i)

        else: # load all at floor in order of arrival
            for i in self.curr_floor.queue[:self.rem_cap()]:
                self._add_passenger(i[1])

    def unload_passengers(self):
        """unload passengers for current floor

        anyone who has arrived at their destination is removed from the elevator
        """
        for person in self.passengers:
            if person.destination == self.curr_floor:
                self.passengers.remove(person)
                person.update_state(person.States.IDLE)

    def _add_passenger(self, person):
        """adds a passenger from the current floor

        Args:
            person: person instance to be added to the elevator
        """
        self.passengers.append(person)
        self.curr_floor.remove(person)
        person.update_state(person.States.SERVICE)

    def update_state(self, state=None):
        """Update the state of the elevator
        """

        # make sure elevator is aware of people waiting
        if state is None:
            if self.state == self.States.IDLE:
                # if theres someone to pick up
                self.next_dest = self.get_next_dest()
                if self.next_dest is not None:
                    if self.next_dest == self.curr_floor:
                        self.update_state(self.States.STOPPED)
                    else:
                        self.update_state(self.States.MOVING)
            return

        # update to new state
        self.state = state
        # TODO: log state change

        # act for current state, decide next state
        if self.state == self.States.STOPPED:
            # update current floor
            self.curr_floor = self.next_dest

            # unload passengers
            if len(self.passengers) > 0:
                self.unload_passengers()

            # load new passengers (specific to algorithm)
            self.load()

            # get next destination
            self.next_dest = self.get_next_dest()

            if self.next_dest is None:
                next_state = self.States.IDLE
            else:
                next_state = self.States.MOVING

            # start moving after some loading time (flat 30 seconds for now)
            settings.FEQ.put_nowait((settings.CURR_TIME + 30, self, next_state))

        elif self.state == self.States.MOVING:
            # determing how long until next destination is reached, add event to feq
            settings.FEQ.put_nowait((
                settings.CURR_TIME + settings.ELEVATOR_SPEED*abs(self.next_dest-self.curr_floor),
                self,
                self.States.STOPPED))

        print("{:.2f} Elevator: {} {} -> {}, {}".format(
            settings.CURR_TIME,
            self.state,
            self.curr_floor,
            self.next_dest,
            self.passengers))



    def get_next_dest(self):
        """This must be implented in each subclass, based on the algorithm"""
        raise NotImplementedError()

    def load(self):
        """algorithm-specific passenger-loading

        How passengers are loaded is specific to the algorithm. should call
        self._load_passengers(...) function according to specific logic
        """
        raise NotImplementedError()

    def rem_cap(self):
        """returns the remaining capacity of the elevator"""
        return self.capacity - len(self.passengers)


class BasicElevator(Elevator):
    """Basic elevator simply used for testing other code

    This simple elevator will just repond to calls as they come, and drop people off if its
    their floor.
    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.destination_queue = []

    def get_next_dest(self):
        # remove current floor from destination queue
        if self.curr_floor in self.destination_queue:
            self.destination_queue.remove(self.curr_floor)

        # look for waiting passengers, add destinations
        for floor in [i for i in self._building.floor.values()]:
            if len(floor.queue) > 0 and floor not in self.destination_queue:
                self.destination_queue.append(floor)

        # if someone is waiting at current floor
        if len(self.curr_floor.queue) > 0 and self.rem_cap() > 0:
            return self.curr_floor

        # return next destination if there is one
        print("destinations", self.destination_queue)
        if len(self.destination_queue) > 0:
            return self.destination_queue[0]
        else:
            return None

    def load(self):
        """load all the passengers at current floor"""

        # load all passengers
        self._load_passengers(self.destination_queue, None)

        # note their destinations
        for i in self.passengers:
            if i.destination not in self.destination_queue:
                self.destination_queue.append(i.destination)

class ScanElevator(Elevator):
    """
    This elevator travels up to the top, and down to the bottom
    It stops if someone is on the floor waiting for it or there
    is passengers who want to get off there
    """
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.direction = "up"

    def get_next_dest(self):
        if self.direction is "up" and self.curr_floor is not self._building.floor_order[-1].name:
            return self._building.floor_order[self._building.floor_order.index(self.curr_floor) + 1]
        elif self.direction is "up" and self.curr_floor is self._building.floor_order[-1].name:
            self.direction = "down"
            return self._building.floor_order[-1] - 1
        elif self.direction is "down" and self.curr_floor is not self._building.floor_order[0].name:
            return self._building.floor_order[self._building.floor_order.index(self.curr_floor) - 1]
        elif self.direction is "down" and self.curr_floor is self._building.floor_order[0].name:
            self.direction = "up"
            return self._building.floor_order[1]

    def load(self):
        """load all the passengers at current floor"""
        self._load_passengers(None, "up")

class ElevatorController:
    """Base Controller for algorithms that use several elevators"""

    def __init__(self, building, num_elevators):
        self._building = building
        self.elevators = []
        for i in range(0, num_elevators):
            self.elevators[i] = ControlledElevator

    def load_passengers(self, destinations=None, direction=None):
        """load_passengers into the elevator, must be implented by subclass"""
        raise NotImplementedError()

    def get_next_dest(self):
        """Must be implemented by each subclass"""
        raise NotImplementedError()

class ControlledElevator(Elevator):
    """Elevator used by the elevator controller"""

    def __init__(self, controller, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._controller = controller

    def load(self):
        """load_passengers into the elevator"""
        self._controller.load_passengers()

    def get_next_dest(self):
        """Must be implemented by each algorithm subclass"""
        self._controller.get_next_dest()
