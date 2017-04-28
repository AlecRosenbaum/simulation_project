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

            # start moving after some loading time (flat 15 seconds for now)
            settings.FEQ.put_nowait((settings.CURR_TIME + 15, self, next_state))

        elif self.state == self.States.MOVING:
            # determing how long until next destination is reached, add event to feq
            settings.FEQ.put_nowait((
                settings.CURR_TIME + 1 + settings.ELEVATOR_SPEED*abs(self.next_dest-self.curr_floor),
                self,
                self.States.STOPPED))

        if settings.VERBOSE:
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
        current_floor_index = self._building.floor_order.index(self.curr_floor.name)
        print("Current Floor: ", self.curr_floor.name)

        if self.direction is "up" and current_floor_index is not max_index:
            name = self._building.floor_order[current_floor_index+1]
            return self._building.floor[name]
        elif self.direction is "up" and current_floor_index is max_index:
            self.direction = "down"
            name = self._building.floor_order[current_floor_index-1]
            return self._building.floor[name]
        elif self.direction is "down" and current_floor_index is not 0:
            name = self._building.floor_order[current_floor_index-1]
            return self._building.floor[name]
        elif self.direction is "down" and current_floor_index is 0:
            self.direction = "up"
            name = self._building.floor_order[1]
            return self._building.floor[name]

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
        self.destination_queue = []

    def get_next_dest(self):
        max_index = len(self._building.floor_order)-1
        current_floor_index = self._building.floor_order.index(self.curr_floor.name)
        print("Current Floor: ", self.curr_floor.name)

        #if we're going up and we aren't at the top floor
        if self.direction is "up" and current_floor_index is not max_index:
            #need to find the highest destination
            max_dest = 0
            #TO-DO: Not look at all_arrivals but instead at
                #The current people on-board and where they want to go
                #AND the requests to go down from the current loc
            for tim, idx, i in self._building.all_arrivals:  #(time, person, floor)
                if i > self._building.all_arrivals[max_dest][2]:
                    max_dest = idx

            #if we're still below the highest destination, keep going up
            if current_floor_index < max_dest:
                name = self._building.floor_order[current_floor_index+1]
                return self._building.floor[name]
            #otherwise, go down
            else:
                self.direction = "down"
                name = self._building.floor_order[current_floor_index-1]
                return self._building.floor[name]
                #if we're going up and we're at the top floor, we need to go down
        elif self.direction is "up" and current_floor_index is max_dest:
            self.direction = "down"
            return self._building.floor_order[-1] - 1
        #if we're going down and we aren't at the bottom floor
        elif self.direction is "down" and current_floor_index is not 0:
            #need to find the lowest destionation
            min_dest = 0
            for tim, idx, i in self._building.all_arrivals:
                if i < self._building.all_arrivals[min_dest][2]: #(time, person, floor)
                    min_dest = idx
            #if we're still above the lowest destination, keep going down
            if current_floor_index > 0:
                name = self._building.floor_order[current_floor_index-1]
                return self._building.floor[name]
            #otherwise, go up
            else:
                self.direction = "up"
                name = self._building.floor_order[1]
                return self._building.floor[name]
        #if we're going down and we're at the bottom floow, we need to go up
        elif self.direction is "down" and current_floor_index is 0:
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

    Each elevator has a "Figure of Suitability".
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
    def _find_closest_caller(self, elevator):
        shortest = None
        for destination in elevator.destination_queue:
            if elevator.direction == "up":
                if destination > elevator.curr_floor:
                    if shortest is None:
                        shortest = destination
                    elif destination - elevator.curr_floor < shortest - elevator.curr_floor:
                        shortest = destination
            else:
                if destination < elevator.curr_floor:
                    if shortest is None:
                        shortest = destination
                    elif elevator.curr_floor - destination < elevator.curr_floor - shortest:
                        shortest = destination
        return shortest

    def _find_closest_passenger(self, elevator):
        closest = None
        for passenger in elevator.passengers:
            if elevator.direction == "up":
                if passenger.destination > elevator.curr_floor:
                    if closest is None:
                        closest = passenger.destination
                    elif (passenger.destination - elevator.curr_floor
                          < closest - elevator.curr_floor):
                        closest = passenger.destination
            else:
                if passenger.destination < elevator.curr_floor:
                    if closest is None:
                        closest = passenger.destination
                    elif (elevator.curr_floor - passenger.destination
                          < elevator.curr_floor - closest):
                        closest = passenger.destination
        return closest

    #return the closest destination in the current direction
    def get_next_dest(self, elevator):
        # remove current floor from destination queue
        if elevator.curr_floor in elevator.destination_queue:
            elevator.destination_queue.remove(elevator.curr_floor)

        self.update_dests()

        #check if theres a passenger destination coming up
        #floor where a passenger is going that is determined to be closest
        #(and in the right direction)
        closest_pass_dest = None
        if len(elevator.passengers) is not 0:
            closest_pass_dest = self._find_closest_passenger(elevator)

        closest_caller_dest = None #
        if len(elevator.destination_queue) is not 0:
            #find the closest caller in our direction
            closest_caller_dest = self._find_closest_caller(elevator)

        #if we have no closest call but have a closest passenger, go drop them off
        if closest_pass_dest is not None and closest_caller_dest is None:
            return closest_pass_dest
        #if we have no closest passenger but have a closest call, go get them
        elif closest_pass_dest is None and closest_caller_dest is not None:
            return closest_caller_dest
        #if we have both, we need to decide what to do
        elif closest_caller_dest is not None and closest_pass_dest is not None:
            if (abs(elevator.curr_floor - closest_caller_dest) <
                    abs(elevator.curr_floor - closest_pass_dest)):
                return closest_caller_dest
            else:
                return closest_pass_dest
        #otherwise, if we have neither, we need to see what happens when we change direction
        else:
            if elevator.direction == "up":
                elevator.direction = "down"
            else:
                elevator.direction = "up"

            closest_pass_dest = self._find_closest_passenger
            closest_caller_dest = self._find_closest_caller

            #if we have no closest call but have a closest passenger, go drop them off
            if closest_pass_dest is not None and closest_caller_dest is None:
                return closest_pass_dest
            #if we have no closest passenger but have a closest call, go get them
            elif closest_pass_dest is None and closest_caller_dest is not None:
                return closest_caller_dest
            #if we have both, we need to decide what to do
            elif closest_caller_dest is not None and closest_pass_dest is not None:
                if (abs(elevator.curr_floor - closest_caller_dest)
                        < abs(elevator.curr_floor - closest_pass_dest)):
                    return closest_caller_dest
                else:
                    return closest_pass_dest
            else:
                return None

    def update_dests(self):
        """Update the destinations of all elevators based on calculated scores"""
        fos = [] #figures of suitability for each elevator
        for arrival in self._building.all_arrivals:
            for idx, elevator in enumerate(self.elevators):
                # FS = 1 if elevator isn't moving towards the call
                if not elevator.direction == elevator.curr_floor.dir_to(arrival[2]):
                    fos[idx] = 1
                    continue

                # base fs score
                fos[idx] = (len(self._building.floor_order)
                            + 1 - abs(arrival[2] - elevator.curr_floor))

                # if the person is going in the opposite direction of the elevator, fs - 1
                if not elevator.direction == arrival[1].origin.dir_to(arrival[1].destination):
                    fos[idx] -= 1

            #find the greatest figure of suitability for this arrival
            max_idx = fos.index(max(fos))

            #add this floor to the destination queue of the best elevator
            self.elevators[max_idx].destination_queue.append(arrival[2])

            self._building.remove(arrival) #we're finished with this arrival

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
        self.elevators[0].sector = ["G", "1", "2", "3"]
        self.elevators[1].sector = ["G", "1", "2", "3"]
        self.elevators[2].sector = ["G", "1", "2", "3"]
        self.elevators[3].sector = ["G", "1", "2", "3", "10", "12"]
        self.elevators[4].sector = ["SB", "B", "1", "G"]
        self.elevators[5].sector = ["G", "1", "6", "8", "9"]

    def get_next_dest(self, elevator):
        pass
