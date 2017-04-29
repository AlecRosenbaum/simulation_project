"""Building and floor objects"""

# imports
# from queue import PriorityQueue

import settings


class Building:
    """models the building"""

    def __init__(self, floors):
        self.floor_order = floors
        self.floor = {}
        for i in floors:
            self.floor[i] = Floor(self, i)
        self.all_arrivals = [] #(time, person, floor)

    def push(self, time, person, floor):
        """add to the queue"""
        self.all_arrivals.append((time, person, floor))
        self.all_arrivals.sort(key=lambda x: x[0])

    def peak(self):
        """get first entry"""
        return self.all_arrivals[0]

    def remove(self, person):
        """remove the head of the list"""
        self.all_arrivals.remove(person)

    def get_all_arrivals(self):
        """returns a list of all arrivals on all floors"""
        ret = []
        for i in self.floor.values():
            ret.extend(i.queue)
        return ret

class Floor:
    """models each floor of a building

    Note: because elevators will pull those waiting into the elevator in different ways (maybe
          according to different algorithms), the floor queue is just a sorted list, not a real
          queue datatype.
    """

    def __init__(self, building, name):
        """constructor"""
        self.building = building
        self.name = name
        self.queue = [] #(time, person)

    def push(self, person, time):
        """add to the queue"""
        self.queue.append((time, person))
        self.queue.sort(key=lambda x: x[0])
        self.building.push(time, person, self)

    def remove(self, person):
        """remove instance i from queue (person comparators have been implemented)"""
        for idx, i in enumerate(self.queue):
            if person == i[1]:
                self.queue.pop(idx)
                return

    def up(self, num=None):
        """return first <num> queued objects going up

        Args:
            num: number of queued "person" instances to return

        Ret:
            yields each person object in queue going up
        """
        cnt = 0
        for i in self.queue:
            if num is not None and cnt >= num:
                break

            if i[1].origin < i[1].destination:
                yield i[1]
                cnt += 1

    def down(self, num=None):
        """return first <num> queued objects going down

        Args:
            num: number of queued "person" instances to return

        Ret:
            yields each person object in queue going up
        """
        cnt = 0
        for i in self.queue:
            if num is not None and cnt >= num:
                break

            if i[1].origin > i[1].destination:
                yield i[1]
                cnt += 1

    def dir_to(self, cmp):
        """returns the direction of cmp floor from self

        Returns:
            "up" for up
            "down" for down
            "same" if they're the same floor
        """

        if self < cmp:
            return "up"
        elif self > cmp:
            return "down"
        elif self == cmp:
            return "same"
        else:
            raise ValueError("Inappropriate argument cmp = {}".format(cmp))

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Floor({})".format(self.name)

    def __lt__(self, cmp):
        floor_order = self.building.floor_order
        return floor_order.index(self.name) < floor_order.index(cmp.name)

    def __gt__(self, cmp):
        floor_order = self.building.floor_order
        return floor_order.index(self.name) > floor_order.index(cmp.name)

    def __eq__(self, cmp):
        return self.name == cmp.name


    def __sub__(self, cmp):
        floor_order = self.building.floor_order
        return floor_order.index(self.name) - floor_order.index(cmp.name)
