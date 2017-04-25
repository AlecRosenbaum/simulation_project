"""handles logging to local databases"""

import sqlite3
import os
import errno

class Logger:
    """a base class for loggers"""

    CREATE_TABLE_STMT = ""
    SELECT_ALL_STMT = ""
    INSERT_STMT = ""

    def __init__(self, db_path, remove_old=False):
        self.db_path = db_path

        # remove old database
        if remove_old:
            try:
                os.remove(self.db_path)
            except OSError as err:
                if err.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                    raise # re-raise exception if a different error occurred

        # create new database, or connect to existing
        if not os.path.isfile(self.db_path):
            # create directory tree
            dirs = os.path.dirname(self.db_path)
            if not os.path.exists(dirs):
                os.makedirs(dirs)

            # create database
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute(self.__class__.CREATE_TABLE_STMT)
            self.conn.commit()
        else:
            self.conn = sqlite3.connect(self.db_path)

    def write_log(self, obj, day, time):
        """write states to log database"""
        raise NotImplementedError()

    def get_all(self):
        """return all rows"""
        cur = self.conn.cursor()
        cur.execute(self.__class__.SELECT_ALL_STMT)
        return cur.fetchall()

    def delete_database(self):
        """delete database entirely"""
        try:
            os.remove(self.db_path)
        except OSError as err:
            if err.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                raise # re-raise exception if a different error occurred


class PersonLogger(Logger):
    """logs states of people"""

    CREATE_TABLE_STMT = """
                            CREATE TABLE PERSON_LOGS (
                               PERSON_ID INT,
                               EVENT_DAY INT,
                               EVENT_TIME INT,
                               STATE TEXT,
                               ELEVATOR_ID INT,
                               ELEVATOR_STATE TEXT
                            )"""

    INSERT_STMT = """
                    INSERT INTO PERSON_LOGS (
                        PERSON_ID,
                        EVENT_DAY,
                        EVENT_TIME,
                        STATE,
                        ELEVATOR_ID,
                        ELEVATOR_STATE)
                    VALUES ({}, {}, {}, '{}', {}, '{}')"""

    SELECT_ALL_STMT = """
                        SELECT
                            PERSON_ID,
                            EVENT_DAY,
                            EVENT_TIME,
                            STATE,
                            ELEVATOR_ID,
                            ELEVATOR_STATE
                        FROM
                            PERSON_LOGS"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write_log(self, person, day, time):
        """write states to log database"""
        if person.curr_elevator:
            stmt = self.__class__.INSERT_STMT.format(
                person.id,
                day,
                time,
                person.state,
                person.curr_elevator.id,
                person.curr_elevator.state)
        else:
            stmt = self.__class__.INSERT_STMT.format(
                person.id,
                day,
                time,
                person.state,
                -1,
                "None")
        self.conn.execute(stmt)
        # Note: usually it would make sense to commit changes here, but it is much faster
        #       if the commit is done after all simulation is finished
