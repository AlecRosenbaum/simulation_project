"""handles person and arrival models"""

# imports
from enum import Enum, auto
import csv
import datetime

import numpy as np

# local imports
import settings


class Person:
    """models a person"""

    person_ctr = 0

    class States(Enum):
        """states implemented for stations"""
        IDLE = auto()
        QUEUED = auto()
        PRE_SERVICE = auto() # walking onto elevator
        SERVICE = auto() # elevator moving between floors
        POST_SERVICE = auto() # walking off of elevator

    def __init__(self, logger, origin, destination):
        """ Person Constructor

        Each person has a unique id (person_id), and keeps track of their own state changes. All
        state changes are logged in the person logger.

        Args:
            logger: instance of a logger
            origin: origin floor (instance of Floor object)
            destination: destination floor (instance of Floor object)
        """
        self.state = self.States.IDLE
        self.person_id = Person.person_ctr
        self.logger = logger
        self.curr_elevator = None
        self.origin = origin
        self.destination = destination

        Person.person_ctr += 1

    def update_state(self, state):
        """updates current state. if none specified, updates based on current state variables.

        Args:
            state: instance of self.States class
        """
        self.state = state

    def __str__(self):
        return "{} -> {}".format(self.origin.name)

class ArrivalGenerator:
    """models floor arrivals based on source data (can save/load data)"""

    def __init__(self, building, person_logger, file_path, days=['M']):
        """ArrivalGenerator Contstructor

        initializes reader, generates all arrivals and departures as person objects

        Note: each person only makes on journey

        Args:
            building: reference to building object arrivals are generated for
            file_path: path to class schedule file
            days: list of days being simulated (ex: ['M', 'Tu'] -> generate arrivals if class is
                  scheduled for monday or wednesday). Defaults to Monday.
        """
        # init instance variables
        self.arrival_times = []
        self._person_logger = person_logger
        self._building = building

        # read csv
        days = set(days)
        for i in ArrivalGenerator.parse_csv(file_path):
            # for each class, generate arrivals and departures

            # if class isn't scheduled for a day we care about, skip
            if len(days & set(i['days'])) == 0:
                continue

            # generate elevator arrivals from class
            self.arrival_times.extend(self.gen_arrival_times(
                i['floor'],
                i['start'],
                i['num_enrolled']))
            self.arrival_times.extend(self.gen_departure_times(
                i['floor'],
                i['end'],
                i['num_enrolled']))

    def gen_arrival_times(self, floor, time, num):
        """Generates <num> arrivals at a floor for a particular time.

        Note: arrivals are generated according to a different distribution from departures.

        Arrivals are generated according to a Chi-Square distribution where 50% of students have
        arrived by 3.35 before class starts. (Chi-Square, df=4)

        Args:
            floor: class's floor
            time: time class starts
            num: number of enrolled students

        Returns:
            list of people w/ their elevator arrival time (in seconds since midnight).
            ex:
                [ (<elevator arrival time>, Person), ... ]
        """
        ret = []
        for rand_time in np.random.chisquare(df=4, size=num):
            origin = self._building.floor['G']
            dest = self._building.floor[floor]
            elevator_arrival_time = time - rand_time
            ret.append((elevator_arrival_time, Person(self._person_logger, origin, dest)))

        return ret

    def gen_departure_times(self, floor, time, num):
        """Generates <num> departures at a floor for a particular time

        Note: departures are generated according to a different distribution from arrivals.

        Departures are generated according to a Chi-Square distribution where 50% of students have
        left by 27 seconds after class ends. (Chi-Square, df=1)

        Args:
            floor: class's floor
            time: time class ends
            num: number of enrolled students
        """
        ret = []
        for rand_time in np.random.chisquare(df=1, size=num):
            origin = self._building.floor[floor]
            dest = self._building.floor['G']
            elevator_arrival_time = time + rand_time
            ret.append((elevator_arrival_time, Person(self._person_logger, origin, dest)))

        return ret

    @staticmethod
    def parse_csv(filename):
        """a generator that reads entries from a csv

        Args:
            filename: name of file to read from

        Yield:
            yields a dictionary containing:
                days: days class is held
                floor: string representing the floor
                start start time (in seconds since midnight)
                end: end time (in seconds since midnight)
                num_enrolled: int represeting number of enrolled students enrolled
        """
        with open(filename, newline='') as arrival_file:
            reader = csv.DictReader(arrival_file)
            for row in reader:
                # parse csv
                days = row['Days'].strip().split(" ")
                floor = row['Room'][:3].lstrip("0") # remove leading zeros
                start = ArrivalGenerator.time_to_sec(row["Meeting Start Time"])
                end = ArrivalGenerator.time_to_sec(row["Meeting End Time"])
                num_enrolled = int(row['Enrollment Total'])

                yield {
                    'days': days,
                    'floor': floor,
                    'start': start,
                    'end': end,
                    'num_enrolled': num_enrolled,
                }

    @staticmethod
    def time_to_sec(time_str):
        """converts time to seconds since midnight

        Args:
            time: time string of format 'HH:MM AM'

        Ret:
            returns an int representing seconds since midnight
        """
        time = datetime.datetime.strptime(time_str, "%I:%M %p").time()
        return 3600 * time.hour + 60 * time.minute
