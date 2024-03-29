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
        self.sectors = []
        self.direction = None

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
                self.load()
                self.next_dest = self.get_next_dest()
                if self.next_dest is not None:
                    if self.next_dest == self.curr_floor:
                        self.update_state(self.States.STOPPED)
                    else:
                        self.update_state(self.States.MOVING)
            return

        # update to new state
        self.state = state

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
                settings.CURR_TIME + 1
                + settings.ELEVATOR_SPEED*abs(self.next_dest-self.curr_floor),
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

    def change_direction(self):
        """change directions"""
        if self.direction == "up":
            self.direction = "down"
        else:
            self.direction = "up"

    def __str__(self):
        return "Elevator[{}, {}, {} -> {} ({}), {}]".format(
            self.id,
            self.state,
            self.curr_floor,
            self.next_dest,
            self.direction,
            self.passengers)

    def __lt__(self, cmp):
        return self.id < cmp.id


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
        if settings.VERBOSE:
            print("Current Floor: ", self.curr_floor.name)

        # go to idle if no passengers and no one waitin
        if (sum([len(i.queue) for i in self._building.floor.values()]) == 0
                and len(self.passengers) == 0):
            return None

        # if at the edge swap directions
        if current_floor_index == max_index or current_floor_index == 0:
            self.change_direction()

        # get the next destination in that direction
        # passenger pickup locations in the same direction
        pickup_loc = [
            i.origin for floor in self._building.floor_order
            for _, i in self._building.floor[floor].queue
            if self.curr_floor.dir_to(i.origin) == self.direction]
        # passenger dropoff locations in the same direction
        dropoff_loc = [
            i.destination for i in self.passengers
            if self.curr_floor.dir_to(i.destination) == self.direction]

        if len(pickup_loc + dropoff_loc) > 0:
            return min(pickup_loc + dropoff_loc, key=lambda x: abs(self.curr_floor - x))
        else:
            if self.direction == "up":
                # return top floor
                return self._building.floor[self._building.floor_order[-1]]
            else:
                # return bottom floor
                return self._building.floor[self._building.floor_order[0]]

    def load(self):
        """load all the passengers at current floor"""
        self._load_passengers()

class LookElevator(Elevator):
    """
    This elevator travels up/down as far as the highest destination/arrival.
    """
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.direction = "up"

    def get_next_dest(self, recurse=True):
        max_index = len(self._building.floor_order)-1
        current_floor_index = self._building.floor_order.index(self.curr_floor.name)
        if settings.VERBOSE:
            print("Current Floor: ", self.curr_floor.name)

        # return to idle if no passengers are waiting and there are no more arrivals
        if (sum([len(i.queue) for i in self._building.floor.values()]) == 0 and
                settings.FEQ.qsize() == 0 and len(self.passengers) == 0):
            return None

        # if at the edge swap directions
        if current_floor_index == max_index or current_floor_index == 0:
            self.change_direction()

        # get the next destination in that direction
        # passenger pickup locations in the same direction
        pickup_loc = [
            i.origin for floor in self._building.floor_order
            for _, i in self._building.floor[floor].queue
            if self.curr_floor.dir_to(i.origin) == self.direction]
        # passenger dropoff locations in the same direction
        dropoff_loc = [
            i.destination for i in self.passengers
            if self.curr_floor.dir_to(i.destination) == self.direction]

        if len(pickup_loc + dropoff_loc) > 0:
            return min(pickup_loc + dropoff_loc, key=lambda x: abs(self.curr_floor - x))
        elif recurse:
            if settings.VERBOSE:
                print("changing directions, recursing")

            self.change_direction()
            return self.get_next_dest(recurse=False)
        else:
            return None

    def load(self):
        """load all the passengers at current floor"""
        self._load_passengers()


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
        self.elevators.extend(
            [ControlledElevator(self, *args, **kwargs)for _ in range(num_elevators)])

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
        self.down_sector = None
        self.up_sector = None
        self.curr_floor = self._building.floor['SB']

    def load(self):
        """load_passengers into the elevator"""
        self._load_passengers()

    def get_next_dest(self):
        """Must be implemented by each algorithm subclass"""
        return self._controller.get_next_dest(self)

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

    #return the closest destination in the current direction
    def get_next_dest(self, elevator, ch_dir=True):
        # remove current floor from destination queue
        if elevator.curr_floor in elevator.destination_queue:
            elevator.destination_queue.remove(elevator.curr_floor)

        self.update_dests()

        # find the closest passenger destination in the same direction
        closest_pass_dest = min(
            [i.destination for i
             in elevator.passengers
             if elevator.curr_floor.dir_to(i.destination) == elevator.direction],
            key=lambda x: abs(x - elevator.curr_floor),
            default=None)

        # find the closest pickup in the pickup queue
        closest_caller_dest = min(
            [i for i
             in elevator.destination_queue
             if elevator.curr_floor.dir_to(i) == elevator.direction],
            key=lambda x: abs(x - elevator.curr_floor),
            default=None)

        # get the closest destination (or None if neither destination exists)
        next_dest = min(
            [i for i in [closest_pass_dest, closest_caller_dest] if i is not None],
            key=lambda x: abs(elevator.curr_floor - x),
            default=None)

        # if neither destinatione exists, change direction and try again
        if next_dest is None and ch_dir:
            elevator.change_direction()

            # prevent an infinite recursion by passing ch_dir=False
            return self.get_next_dest(elevator, ch_dir=False)

        return next_dest

    def update_dests(self):
        """Update the destinations of all elevators based on calculated scores"""
        fos = [None for _ in range(len(self.elevators))] #figures of suitability for each elevator
        for arrival in self._building.get_all_arrivals():
            for idx, elevator in enumerate(self.elevators):
                # FS = 1 if elevator isn't moving towards the call
                if not elevator.direction == elevator.curr_floor.dir_to(arrival[1].origin):
                    fos[idx] = 1
                    continue

                # base fs score
                fos[idx] = (len(self._building.floor_order)
                            + 1 - abs(arrival[1].origin - elevator.curr_floor))

                # if the person is going in the opposite direction of the elevator, fs - 1
                if not elevator.direction == arrival[1].origin.dir_to(arrival[1].destination):
                    fos[idx] -= 1

            #find the greatest figure of suitability for this arrival
            max_idx = fos.index(max(fos))

            #add this floor to the destination queue of the best elevator
            if arrival[1].origin not in self.elevators[max_idx].destination_queue:
                self.elevators[max_idx].destination_queue.append(arrival[1].origin)

            # self._building.remove(arrival) #we're finished with this arrival

class FixedSectorsElevatorController(ElevatorController):
    """This controller implements the Fixed Sector algorithm

    The building is divided into as many sectors as there are elevators,
    and elevators will respond to calls within their sector.

    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        #NOTE: SECTORS MOVED TO BEING SET IN TEST/CALL FILE

    #return the closest destination in the current direction
    def get_next_dest(self, elevator, ch_dir=True):
        # remove current floor from destination queue
        if elevator.curr_floor in elevator.destination_queue:
            elevator.destination_queue.remove(elevator.curr_floor)

        elevator.destination_queue = []

        self.update_dests()

        # find the closest passenger destination in the same direction
        closest_pass_dest = min(
            [i.destination for i
             in elevator.passengers
             if elevator.curr_floor.dir_to(i.destination) == elevator.direction],
            key=lambda x: abs(x - elevator.curr_floor),
            default=None)

        # find the closest pickup in the pickup queue
        closest_caller_dest = min(
            [i for i
             in elevator.destination_queue
             if elevator.curr_floor.dir_to(i) == elevator.direction],
            key=lambda x: abs(x - elevator.curr_floor),
            default=None)

        # get the closest destination (or None if neither destination exists)
        next_dest = min(
            [i for i in [closest_pass_dest, closest_caller_dest] if i is not None],
            key=lambda x: abs(elevator.curr_floor - x),
            default=None)

        # if neither destinatione exists, change direction and try again
        if next_dest is None and ch_dir:
            elevator.change_direction()

            # prevent an infinite recursion by passing ch_dir=False
            return self.get_next_dest(elevator, ch_dir=False)

        return next_dest

    def update_dests(self):
        """Update the destinations of all elevators based on calculated scores"""
        fos = [None for _ in range(len(self.elevators))] #figures of suitability for each elevator

        for arrival in self._building.get_all_arrivals():
            for idx, elevator in enumerate(self.elevators):
                # FS = 1 if elevator isn't moving towards the call
                if not elevator.direction == elevator.curr_floor.dir_to(arrival[1].origin):
                    fos[idx] = 1
                    continue

                # base fs score
                fos[idx] = (len(self._building.floor_order)
                            + 1 - abs(arrival[1].origin - elevator.curr_floor))

                # if the person is going in the opposite direction of the elevator, fs - 1
                if not elevator.direction == arrival[1].origin.dir_to(arrival[1].destination):
                    fos[idx] -= 1

                # weight the suitability according to how far away it is from the sector
                arr_floor = arrival[1].origin
                if arr_floor.dir_to(arrival[1].destination) == "up":
                    if arr_floor in elevator.up_sector:
                        denom = 0
                    else:
                        denom = min(
                            abs(arr_floor-min(elevator.up_sector)),
                            abs(arr_floor-max(elevator.up_sector)))
                else:
                    if arr_floor in elevator.down_sector:
                        denom = 0
                    else:
                        denom = min(
                            abs(arr_floor-min(elevator.down_sector)),
                            abs(arr_floor-max(elevator.down_sector)))

                fos[idx] /= (1+denom)

            #find the greatest figure of suitability for this arrival
            max_idx = fos.index(max(fos))

            #add this floor to the destination queue of the best elevator
            self.elevators[max_idx].destination_queue.append(arrival[1].origin)

    def set_sector(self, elevator_num, up_sector, down_sector):
        """set the sectors of the elevators

        Args:
            elevator_num: which elevator to set the sectors of
            up_sector: end points of floors included in the sector ex: ['B', '5']
            down_sector: end points of floors included in the sector ex: ['B', '5']
        """
        self.elevators[elevator_num].up_sector = [
            self._building.floor[self._building.floor_order[i]]
            for i in range(
                self._building.floor_order.index(up_sector[0]),
                self._building.floor_order.index(up_sector[1]))]
        self.elevators[elevator_num].down_sector = [
            self._building.floor[self._building.floor_order[i]]
            for i in range(
                self._building.floor_order.index(down_sector[0]),
                self._building.floor_order.index(down_sector[1]))]


class FixedSectorsTimePriorityElevatorController(ElevatorController):
    """This controller implements the Fixed Sector algorithm
    with TIME priority

    The building is divided into as many sectors as there are elevators,
    and elevators will respond to calls within their sector.

    Additionally, priority for a floor increases as "time" increases

    """
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        #NOTE: SECTORS MOVED TO BEING SET IN TEST/CALL FILE

    #return the closest destination in the current direction
    def get_next_dest(self, elevator, ch_dir=True):
        # remove current floor from destination queue
        if elevator.curr_floor in elevator.destination_queue:
            elevator.destination_queue.remove(elevator.curr_floor)

        elevator.destination_queue = []

        self.update_dests()

        # find the closest passenger destination in the same direction
        closest_pass_dest = min(
            [i.destination for i
             in elevator.passengers
             if elevator.curr_floor.dir_to(i.destination) == elevator.direction],
            key=lambda x: abs(x - elevator.curr_floor),
            default=None)

        # find the closest pickup in the pickup queue
        closest_caller_dest = min(
            [i for i
             in elevator.destination_queue
             if elevator.curr_floor.dir_to(i) == elevator.direction],
            key=lambda x: abs(x - elevator.curr_floor),
            default=None)

        # get the closest destination (or None if neither destination exists)
        next_dest = min(
            [i for i in [closest_pass_dest, closest_caller_dest] if i is not None],
            key=lambda x: abs(elevator.curr_floor - x),
            default=None)

        # if neither destinatione exists, change direction and try again
        if next_dest is None and ch_dir:
            elevator.change_direction()

            # prevent an infinite recursion by passing ch_dir=False
            return self.get_next_dest(elevator, ch_dir=False)

        return next_dest

    def update_dests(self):
        """Update the destinations of all elevators based on calculated scores"""
        fos = [None for _ in range(len(self.elevators))] #figures of suitability for each elevator
        for arrival in self._building.get_all_arrivals():
            for idx, elevator in enumerate(self.elevators):
                # FS = 1 if elevator isn't moving towards the call
                if not elevator.direction == elevator.curr_floor.dir_to(arrival[1].origin):
                    fos[idx] = 1
                    continue

                # base fs score
                fos[idx] = (len(self._building.floor_order)
                            + 1 - abs(arrival[1].origin - elevator.curr_floor))

                # if the person is going in the opposite direction of the elevator, fs - 1
                if not elevator.direction == arrival[1].origin.dir_to(arrival[1].destination):
                    fos[idx] -= 1

                # weight the suitability according to how far away it is from the sector
                arr_floor = arrival[1].origin
                if arr_floor.dir_to(arrival[1].destination) == "up":
                    if arr_floor in elevator.up_sector:
                        denom = 0
                    else:
                        denom = min(
                            abs(arr_floor-min(elevator.up_sector)),
                            abs(arr_floor-max(elevator.up_sector)))
                else:
                    if arr_floor in elevator.down_sector:
                        denom = 0
                    else:
                        denom = min(
                            abs(arr_floor-min(elevator.down_sector)),
                            abs(arr_floor-max(elevator.down_sector)))
                fos[idx] /= (1+denom)

                #Add weighting based on time
                diff = settings.CURR_TIME - arrival[0]
                if diff > settings.MAX_WAIT:
                    diff = diff/settings.MAX_WAIT
                    fos[idx] = fos[idx] * diff * diff

            #find the greatest figure of suitability for this arrival
            max_idx = fos.index(max(fos))

            #add this floor to the destination queue of the best elevator
            self.elevators[max_idx].destination_queue.append(arrival[1].origin)

    def set_sector(self, elevator_num, up_sector, down_sector):
        """set the sectors of the elevators

        Args:
            elevator_num: which elevator to set the sectors of
            up_sector: end points of floors included in the sector ex: ['B', '5']
            down_sector: end points of floors included in the sector ex: ['B', '5']
        """
        self.elevators[elevator_num].up_sector = [
            self._building.floor[self._building.floor_order[i]]
            for i in range(
                self._building.floor_order.index(up_sector[0]),
                self._building.floor_order.index(up_sector[1]))]
        self.elevators[elevator_num].down_sector = [
            self._building.floor[self._building.floor_order[i]]
            for i in range(
                self._building.floor_order.index(down_sector[0]),
                self._building.floor_order.index(down_sector[1]))]
