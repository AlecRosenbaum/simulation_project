"""runs statistics on simulation data"""

import os
import sqlite3

import numpy as np
import matplotlib.pyplot as plt

import settings

AVG_TIME_IN_SYS_STMT = """
SELECT 
    AVG(A.EVENT_TIME - (SELECT EVENT_TIME FROM PERSON_LOGS B WHERE A.PERSON_ID = B.PERSON_ID AND B.STATE == "States.QUEUED")) AS AVG_WAIT_TIME
FROM PERSON_LOGS A
WHERE A.STATE = "States.IDLE"
"""

TIME_IN_SYS_VS_FLOORS_TRAVELED_STMT = """
SELECT 
    Abs(DEST-ORIGIN) AS FLOORS_TRAVELED,
    AVG(A.EVENT_TIME - (SELECT EVENT_TIME FROM PERSON_LOGS B WHERE A.PERSON_ID = B.PERSON_ID AND B.STATE == "States.QUEUED")) AS AVG_TIME_IN_SYS
FROM PERSON_LOGS A
WHERE A.STATE = "States.IDLE"
GROUP BY FLOORS_TRAVELED
"""

# TOD = time of day
WAIT_TIME_VS_TOD_STMT = """
SELECT 
    EVENT_TIME,
    (SELECT EVENT_TIME FROM PERSON_LOGS B WHERE A.PERSON_ID = B.PERSON_ID AND B.STATE == "States.IDLE" LIMIT 1) - A.EVENT_TIME AS WAIT_TIME
FROM PERSON_LOGS A
WHERE A.STATE = "States.QUEUED"
"""


STATS_DIR = "stats"
STATS_FILE_NAME = "stats.txt"
PERSON_LOG_PATH = os.path.join(settings.LOG_DIR, settings.PERSON_LOG_FNAME)
ELEVATOR_LOG_PATH = os.path.join(settings.LOG_DIR, settings.ELEVATOR_LOG_FNAME)
FLOOR_LOG_PATH = os.path.join(settings.LOG_DIR, settings.FLOOR_LOG_FNAME)

def run_stats(person_log_path=PERSON_LOG_PATH, elevator_log_path=ELEVATOR_LOG_PATH,
              floor_log_path=FLOOR_LOG_PATH, stats_dir=STATS_DIR):
    """run stats for files"""

     # create statistics file
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)
    stats_file = open(os.path.join(stats_dir, STATS_FILE_NAME), 'w')

    # open person event database
    if os.path.isfile(person_log_path):
        person_conn = sqlite3.connect(person_log_path)
        person_cur = person_conn.cursor()
    else:
        raise LookupError("Person Log database doesn't exist")

    # determine average time in system
    person_cur.execute(AVG_TIME_IN_SYS_STMT)
    avg_time_in_system = person_cur.fetchall()[0][0]
    print("average wait time (seconds):", avg_time_in_system, file=stats_file)

    # time in system vs floors traveled
    person_cur.execute(TIME_IN_SYS_VS_FLOORS_TRAVELED_STMT)
    avg_time_in_system_data = person_cur.fetchall()

    x, y = zip(*avg_time_in_system_data)
    plt.clf()
    plt.plot(x, y, color='r', linestyle='-')
    plt.savefig(os.path.join(stats_dir, ".".join(["tis_vs_travel_distance", "png"])))

    # avg wait time vs. arrival time
    person_cur.execute(WAIT_TIME_VS_TOD_STMT)
    wait_time_vs_tod = person_cur.fetchall()

    x, y = zip(*wait_time_vs_tod)
    plt.clf()
    plt.scatter(x, y, s=2, lw=0)
    plt.savefig(os.path.join(stats_dir, ".".join(["wait_time_vs_tod", "png"])))


if __name__ == '__main__':
    run_stats()
