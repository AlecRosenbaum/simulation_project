"""Building and floor objects"""

class Building:
    """models the building"""

    def __init__(self, floors):
        self.floor = {}
        for i in floors:
            self.floor[i] = Floor(i)


class Floor:
    """models each floor of a building"""

    def __init__(self, name):
        self.name = name
    