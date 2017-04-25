"""runs statistics on simulation data"""

import os
import sqlite3

import settings

AVG_WAIT_TIME_STMT = """
SELECT 
    AVG(A.EVENT_TIME - (SELECT EVENT_TIME FROM PERSON_LOGS B WHERE A.PERSON_ID = B.PERSON_ID AND B.STATE == "States.QUEUED")) AS AVG_WAIT_TIME
FROM PERSON_LOGS A
WHERE A.STATE = "States.SERVICE"
"""


STATS_DIR = "stats"
STATS_FILE_NAME = "stats.txt"

def main():
    """main"""

     # create statistics file
    if not os.path.exists(STATS_DIR):
        os.makedirs(STATS_DIR)
    stats_file = open(os.path.join(STATS_DIR, STATS_FILE_NAME), 'w')

    # open person event database
    person_log_path = os.path.join(settings.LOG_DIR, settings.PERSON_LOG_FNAME)
    if os.path.isfile(person_log_path):
        person_conn = sqlite3.connect(person_log_path)
        person_cur = person_conn.cursor()
    else:
        raise LookupError("Person Log database doesn't exist")

    person_cur.execute(AVG_WAIT_TIME_STMT)
    avg_wait_time = person_cur.fetchall()[0][0]
    print("average wait time (seconds):", avg_wait_time, file=stats_file)

if __name__ == '__main__':
    main()
