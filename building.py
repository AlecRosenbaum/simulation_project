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

    def remove(self, i):
        """remove instance i from queue (person comparators have been implemented)"""
        self.queue.remove(i)

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
