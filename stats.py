"""runs statistics on simulation data"""

import os
import sqlite3

import numpy as np
import matplotlib.pyplot as plt

import settings

BASIC_ORDERED_STMT = """
    SELECT EVENT_DAY, PERSON_ID, EVENT_TIME, STATE, ELEVATOR_ID, ORIGIN, DEST
    FROM 'PERSON_LOGS' 
    ORDER BY EVENT_DAY, PERSON_ID, EVENT_TIME 
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

    # fetch basic data (used for multiple things)
    person_cur.execute(BASIC_ORDERED_STMT)
    basic_data = np.array(person_cur.fetchall())

    idle_rows = np.where(basic_data[:, 3] == "States.IDLE")[0]
    idle_vals = basic_data[idle_rows, 2].astype(dtype=np.float32)
    service_vals = basic_data[idle_rows - 1, 2].astype(dtype=np.float32)
    queued_vals = basic_data[idle_rows - 2, 2].astype(dtype=np.float32)

    # determine average time in system
    avg_tis = np.mean(np.subtract(idle_vals, queued_vals))
    print("average time in system (seconds):", avg_tis, file=stats_file)


    # time in system vs floors traveled
    tis_vs_floors = np.zeros((idle_vals.shape[0], 2), dtype=np.float32)
    tis_vs_floors[:, 1] = idle_vals - queued_vals
    dest = basic_data[idle_rows, 6].astype(dtype=np.int32)
    origin = basic_data[idle_rows, 5].astype(dtype=np.int32)
    tis_vs_floors[:, 0] = np.absolute(dest - origin)

    # find the average for each floor delta
    tis_vs_floors = tis_vs_floors[tis_vs_floors[:, 0].argsort()]
    floor_diff_data = np.split(
        tis_vs_floors,
        np.where(np.diff(tis_vs_floors[:, 0]))[0]+1)

    x = []
    y = []
    for i in floor_diff_data:
        x.append(i[0, 0])
        y.append(np.mean(i[:, 1]))

    plt.clf()
    plt.plot(x, y, color='r', linestyle='-')
    plt.savefig(os.path.join(stats_dir, ".".join(["tis_vs_travel_distance", "png"])))


    # avg time in system vs. arrival time (arrival == queued time)
    tis_vs_time = np.zeros((idle_vals.shape[0], 2), dtype=np.float32)
    tis_vs_time[:, 0] = basic_data[idle_rows - 2, 2].astype(dtype=np.float32)
    tis_vs_time[:, 1] = service_vals - queued_vals

    x = tis_vs_time[:, 0]
    y = tis_vs_time[:, 1]
    plt.clf()
    plt.scatter(x, y, s=2, lw=0)
    plt.savefig(os.path.join(stats_dir, ".".join(["wait_time_vs_tod", "png"])))


if __name__ == '__main__':
    run_stats()
