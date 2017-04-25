"""settings and global configurations"""
from queue import PriorityQueue
from os import path

# configuration constants
DEFAULT_CAPACITY = 5
G_ENTRY_PCT = .6
ELEVATOR_SPEED = 15 # 15 seconds per floor traveled

# log filename
LOG_DIR = "logs"
PERSON_LOG_FNAME = "person.sqlite3"
ELEVATOR_LOG_FNAME = "elevator.sqlite3"

# arrivals
ARRIVALS_DIR = "arrivals"
ARRIVALS_DATA_SET_CSV = path.join("data", "class_enrollment_list.csv")

# logging
VERBOSE = True

# global future event queue
#   structure of items
#       (time_of_event, object, new_state, [args])
FEQ = PriorityQueue()
CURR_DAY = 0 # current day
CURR_TIME = 0
ELEVATORS = []
BUILDING = None
