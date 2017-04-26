"""All of the elevator classes"""

# standard imports
from enum import Enum, auto

# local imports
import settings

class Elevator:
    """base abstract class for elevator cars"""

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

                # add new passengers to elevator and remove them from the list
                # of arrivals
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
        for person in self.passengers[:]:
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
        person.curr_elevator = self
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


# SINGLE-ELEVATOR ALGORITHMS

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
                print("floor {} queue: {}".format(floor.name, floor.queue))
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
        self._load_passengers()

        # note their destinations
        for i in self.passengers:
            if i.destination not in self.destination_queue:
                self.destination_queue.append(i.destination)

class ScanElevator(Elevator):
    """
    This elevator travels up to the top, and down to the bottom.
    """
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.direction = "up"

    def get_next_dest(self):
        max_index = len(self._building.floor_order)-1
        max_floor = self._building.floor_order[max_index]
        min_floor = self._building.floor_order[0]
        print("Max Floor: ", max_floor)
        print("Min Floor: ", min_floor)
        print("Max Floor Index: ", max_index)
        print("Current Floor: ", self.curr_floor.name)
        current_floor_index = self._building.floor_order.index(self.curr_floor)

        if self.direction is "up" and self.curr_floor is not max_floor:
            return self._building.floor_order[current_floor_index + 1]
        elif self.direction is "up" and self.curr_floor is max_floor:
            self.direction = "down"
            return self._building.floor_order[current_floor_index -1]
        elif self.direction is "down" and self.curr_floor is not min_floor:
            return self._building.floor_order[current_floor_index - 1]
        elif self.direction is "down" and self.curr_floor is min_floor:
            self.direction = "up"
            return self._building.floor_order[1]

    def load(self):
        """load all the passengers at current floor"""
        self._load_passengers(None, "up")

class LookElevator(Elevator):
    """
    This elevator travels up/down as far as the highest destination/arrival.
    """
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.direction = "up"

    def get_next_dest(self):
        #if we're going up and we aren't at the top floor
        if self.direction is "up" and self.curr_floor is not self._building.floor_order[-1].name:
            #need to find the highest destination
            max_dest = 0
            for idx, i in self._building.all_arrivals:
                if i[2] > self._building.all_arrivals[max_dest][2]:
                    max_dest = idx

            #if we're still below the highest destination, keep going up
            if self.curr_floor < self._building.floor_order[max_dest]:
                return self._building.floor_order[self._building.floor_order.index(self.curr_floor) + 1]
            #otherwise, go down
            else:
                self.direction = "down"
                return self._building.floor_order[self._building.floor_order.index(self.curr_floor) - 1]
        #if we're going up and we're at the top floor, we need to go down
        elif self.direction is "up" and self.curr_floor is self._building.floor_order[-1].name:
            self.direction = "down"
            return self._building.floor_order[-1] - 1
        #if we're going down and we aren't at the bottom floor
        elif self.direction is "down" and self.curr_floor is not self._building.floor_order[0].name:
            #need to find the lowest destionation
            min_dest = 0
            for idx, i in self._building.all_arrivals:
                if i[2] < self._building.all_arrivals[min_dest][2]:
                    min_dest = idx
            #if we're still above the lowest destination, keep going down
            if self.curr_floor > self._building.floor_order[min_dest]:
                return self._building.floor_order[self._building.floor_order.index(self.curr_floor) - 1]
            #otherwise, go up
            else:
                self.direction = "up"
                return self._building.floor_order[self._building.floor_order.index(self.curr_floor) + 1]
        #if we're going down and we're at the bottom floow, we need to go up
        elif self.direction is "down" and self.curr_floor is self._building.floor_order[0].name:
            self.direction = "up"
            return self._building.floor_order[1]

    def load(self):
        """load all the passengers at current floor"""
        self._load_passengers(None, "up")


# MULTI-ELEVATOR ALGORITHMS

class ElevatorController:
    """Base Elevator Car Controller for algorithms that use several elevators"""

    def __init__(self, building):
        self._building = building
        self.elevators = []

    def spawn_elevators(self, num_elevators, *args, **kwargs):
        """creates controlled elevartors

        Args:
            num_elevators: number of elevators to spawn
            other: required and optional arguments pass to ControlledElevator constructor
        """
        self.elevators.extend([ControlledElevator(*args, **kwargs) for _ in range(num_elevators)])

    def get_next_dest(self, elevator):
        """called by each controlled elevator, must be implemented by each subclass"""
        raise NotImplementedError()

class ControlledElevator(Elevator):
    """Elevator used by the elevator controller
    """

    def __init__(self, controller, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._controller = controller
        self.destination_queue = []
        self.direction = "up"
        self.sector = None

    def load(self):
        """load_passengers into the elevator"""
        self._load_passengers(self)

    def get_next_dest(self):
        """Must be implemented by each algorithm subclass"""
        self._controller.get_next_dest(self)

class NearestCarElevatorController(ElevatorController):
    """
    This controller implements the Nearest Car First algorithm

    Each elevator has a "Figure of Suitability", fig_suit.
    If an elevator is moving towards a call, and the call is in the same direction,
    FS = (N + 2) - d, where N is one less than the number of floors in the building,
    and d is the distance in floors between the elevator and the passenger call.
    If the elevator is moving towards the call, but the call is in the opposite direction,
    FS = (N + 1) - d.
    If the elevator is moving away from the point of call, FS = 1.
    The elevator with the highest FS for each call is sent to answer it.

    Source: https://www.quora.com/Is-there-any-public-elevator-scheduling-algorithm-standard
    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.spawn_elevators(6) #get 6 elevators

    #return the closest index in the queue of destinations, or None
    #if there is no destination in that direction
    def _find_shortest(self, elevator):
        shortest = None
        for idx, destination in enumerate(elevator.destination_queue):
            if elevator.direction == "up":
                if destination > elevator.curr_floor:
                    if shortest is None:
                        shortest = idx
                    elif destination - elevator.curr_floor < elevator.destination_queue[shortest]:
                        shortest = idx
            else:
                if destination < elevator.curr_floor:
                    if shortest is None:
                        shortest = idx
                    elif elevator.curr_floor - destination < elevator.destination_queue[shortest]:
                        shortest = idx
        return shortest

    #return the closest destination in the current direction
    def get_next_dest(self, elevator):
        # remove current floor from destination queue
        if elevator.curr_floor in elevator.destination_queue:
            elevator.destination_queue.remove(elevator.curr_floor)

        self.update_dests()

        if len(elevator.destination_queue) is not 0:
            #find the shortest destination in our direction as the next destination
            #if there is none, go the other way

            shortest = self._find_shortest(elevator)

            if shortest is None:
                if elevator.direction == "up":
                    elevator.direction = "down"
                else:
                    elevator.direction = "up"
                shortest = self._find_shortest(elevator)

            return elevator.destination_queue[shortest]
        else:
            return None

    def update_dests(self):
        """Update the destinations of all elevators based on calculated scores"""
        fos = [] #figures of suitability for each elevator
        for arrival in self._building.all_arrivals:
            for idx, elevator in enumerate(self.elevators):
                #if the person is on a floor we're going up to
                if elevator.direction == "up" and arrival[2] > elevator.curr_floor:
                    #if the person's destination is up
                    if arrival[1].destination > arrival[2]:
                        fos[idx] = (14 + 2) - abs((arrival[2] - elevator.curr_floor))
                    #if the person's destination is down
                    else:
                        fos[idx] = (14 + 1) - abs((arrival[2] - elevator.curr_floor))
                #if the person is on a floor we're going down to
                elif elevator.direction == "down" and arrival[2] < elevator.curr_floor:
                    #if the person's destination is down
                    if arrival[1].destination < arrival[2]:
                        fos[idx] = (14 + 2) - abs((arrival[2] - elevator.curr_floor))
                    #if the person's destination is up
                    else:
                        fos[idx] = (14 + 1) - abs((arrival[2] - elevator.curr_floor))
                #if the person is in the opposite direction that we're moving
                else:
                    fos[idx] = 1

            #find the greatest figure of suitability for this arrival
            max_idx = 0
            for i, _ in enumerate(fos):
                if fos[i] > fos[max_idx]:
                    max_idx = i

            #add this floor to the destination queue of the best elevator
            self.elevators[max_idx].destination_queue.append(arrival[2])

            self._building.remove(arrival[1]) #we're finished with this arrival

class FixedSectorsElevatorController(ElevatorController):
    """This controller implements the Fixed Sector algorithm

    The building is divided into as many sectors as there are elevators,
    and elevators will respond to calls within their sector.

    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.spawn_elevators(6) #get 6 elevators
        self._set_sectors()


    def _set_sectors(self):
        """Set the sectors for each elevator, as a range in the
        buildings floor_order"""
        #self.elevators[0].sector = self._building.floor_order[]
        #self.elevators[1].sector = self._building.floor_order[]
        #self.elevators[2].sector = self._building.floor_order[]
        #self.elevators[3].sector = self._building.floor_order[]
        #self.elevators[4].sector = self._building.floor_order[]
        #self.elevators[5].sector = self._building.floor_order[]


    def get_next_dest(self, elevator):
        pass
