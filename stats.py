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

QUEUE_LEN_STMT = """
WITH NUM_DAYS AS (
    SELECT MAX(EVENT_DAY) + 1 as NUM
    FROM PERSON_LOGS
)
SELECT 
    EVENT_TIME, 
    CASE 
        WHEN STATE == 'States.QUEUED' THEN 1.0/(SELECT NUM FROM NUM_DAYS LIMIT 1)
        WHEN STATE == 'States.SERVICE' THEN -1.0/(SELECT NUM FROM NUM_DAYS LIMIT 1)
    ELSE
        0
    END AS QUEUE_LEN_CHNG
FROM PERSON_LOGS
ORDER BY EVENT_TIME
"""


STATS_DIR = "stats"
STATS_FILE_NAME = "stats.txt"
PERSON_LOG_PATH = os.path.join(settings.LOG_DIR, settings.PERSON_LOG_FNAME)

def run_stats(person_log_path=PERSON_LOG_PATH, stats_dir=STATS_DIR):
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

    ## average wait time
    avg_wait_time = np.mean(np.subtract(service_vals, queued_vals))
    print("average wait time (seconds):", avg_wait_time, file=stats_file)

    avg_wait_time = np.std(np.subtract(service_vals, queued_vals))
    print("wait time standard deviation (seconds):", avg_wait_time, file=stats_file)

    ## determine average time in system
    avg_tis = np.mean(np.subtract(idle_vals, queued_vals))
    print("average time in system (seconds):", avg_tis, file=stats_file)

    ## time in system vs floors traveled
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
        x.append(int(i[0, 0]))
        y.append(np.mean(i[:, 1]))

    plt.clf()

    y_pos = np.arange(len(x))
    rects = plt.bar(y_pos, y, align='center', alpha=0.5)
    plt.xticks(y_pos, x)
    plt.ylabel("Time in System (seconds)")
    plt.xlabel("Floors Traveled")
    autolabel(rects, plt)
    plt.savefig(os.path.join(stats_dir, ".".join(["tis_vs_travel_distance", "png"])))


    ## avg wait time vs. arrival time (arrival == queued time)
    wait_time_vs_time = np.zeros((idle_vals.shape[0], 2), dtype=np.float32)
    wait_time_vs_time[:, 0] = basic_data[idle_rows - 2, 2].astype(dtype=np.float32)
    wait_time_vs_time[:, 1] = service_vals - queued_vals

    x = wait_time_vs_time[:, 0]
    y = wait_time_vs_time[:, 1]
    plt.clf()
    plt.scatter(x, y, s=2, lw=0)
    plt.ylabel("Wait Time (seconds)")
    plt.xlabel("Arrival Time (seconds since 12AM)")
    plt.savefig(os.path.join(stats_dir, ".".join(["wait_time_vs_tod", "png"])))

    ## avg time in system vs. arrival time (arrival == queued time)
    tis_vs_time = np.zeros((idle_vals.shape[0], 2), dtype=np.float32)
    tis_vs_time[:, 0] = basic_data[idle_rows - 2, 2].astype(dtype=np.float32)
    tis_vs_time[:, 1] = idle_vals - queued_vals

    x = tis_vs_time[:, 0]
    y = tis_vs_time[:, 1]
    plt.clf()
    plt.scatter(x, y, s=2, lw=0)
    plt.ylabel("Time in System (seconds)")
    plt.xlabel("Arrival Time (seconds since 12AM)")
    plt.savefig(os.path.join(stats_dir, ".".join(["tis_vs_tod", "png"])))

    ## time in system vs origin floor
    tis_vs_origin = np.zeros((idle_vals.shape[0], 2), dtype=np.float32)
    tis_vs_origin[:, 1] = idle_vals - queued_vals
    tis_vs_origin[:, 0] = origin = basic_data[idle_rows, 5].astype(dtype=np.int32)

    # find the average for each origin floor
    tis_vs_origin = tis_vs_origin[tis_vs_origin[:, 0].argsort()]
    floor_origin_data = np.split(
        tis_vs_origin,
        np.where(np.diff(tis_vs_origin[:, 0]))[0]+1)

    x = []
    y = []
    floor_names = ['SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    for i in floor_origin_data:
        x.append(floor_names[int(i[0, 0])])
        y.append(np.mean(i[:, 1]))

    plt.clf()

    y_pos = np.arange(len(x))
    rects = plt.bar(y_pos, y, align='center', alpha=0.5)
    plt.xticks(y_pos, x)
    plt.ylabel("Time in System (seconds)")
    plt.xlabel("Origin Floor")
    autolabel(rects, plt)
    plt.savefig(os.path.join(stats_dir, ".".join(["tis_vs_origin_floor", "png"])))

    ## average queue length throughout the day
    person_cur.execute(QUEUE_LEN_STMT)
    queue_len_data = person_cur.fetchall()

    x, y = zip(*queue_len_data)
    y = np.cumsum(np.array(y, dtype=np.float32))
    plt.clf()
    plt.plot(x, y, color='r', linestyle='-')
    plt.ylabel("Queue Length (all floors)")
    plt.xlabel("Arrival Time (seconds since 12AM)")
    plt.savefig(os.path.join(stats_dir, ".".join(["avg_queue_len", "png"])))

def autolabel(rects, plot):
    """
    Attach a text label above each bar displaying its height,
    also set the height of the plot
    """
    # format y axis
    plot.ylim([0, max([i.get_height() for i in rects])*1.2])

    # add labels
    for rect in rects:
        height = rect.get_height()
        plot.text(
            rect.get_x() + rect.get_width()/2.,
            1.025*height,
            '%d' % int(height),
            ha='center', va='bottom')

if __name__ == '__main__':
    run_stats()
