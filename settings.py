"""settings and global configurations"""
from queue import PriorityQueue

# configuration constants
DEFAULT_CAPACITY = 20

# log filename
PERSON_LOG_FNAME = "person.sqlite3"
ELEVATOR_LOG_FNAME = "elevator.sqlite3"

# arrivals directory
ARRIVALS_DIR = "arrivals"
VERBOSE = True

# global future event queue
#   structure of items
#       (time_of_event, object, new_state, [args])
FEQ = PriorityQueue()
CURR_DAY = 0 # current day
ELEVATORS = []
