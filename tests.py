"""handles all testing for the simulation models"""
import os
from timeit import default_timer as timer

import settings
from person import ArrivalGenerator
from building import Building
import elevators
import logger

import stats as sim_stats

BASE_DIR = "experiments"

def test_scan_elevator(limit=None):
    """method that tests the scan elevator"""

    result_dir = "scan"

    # create directory if not existing
    dirs = os.path.join(BASE_DIR, result_dir)
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    # create loggers
    person_logger_path = os.path.join(dirs, settings.LOG_DIR, settings.PERSON_LOG_FNAME)
    person_logger = logger.PersonLogger(person_logger_path, remove_old=True)
    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=person_logger)

    days = ["M", "Tu", "W", "Th", "F"]

    for day in days:
        # load saved arrivals or generate new arrivals
        arr_gen.arrival_times = []
        save_path = os.path.join(settings.ARRIVALS_DIR, "{}_arrivals.csv".format(day))
        if not os.path.exists(save_path):
            arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV, days=[day])
            arr_gen.save(save_path)
        else:
            arr_gen.load(save_path)

        # add first 100 floor arrivals to FEQ
        cnt = 0
        for time, person in arr_gen.arrival_times:
            cnt += 1
            if limit is not None and cnt > limit:
                break
            settings.FEQ.put_nowait((time, person, person.States.QUEUED))

        # create 6 elevators
        settings.ELEVATORS = []
        for _ in range(6):
            settings.ELEVATORS.append(elevators.ScanElevator(None, building))

        while not settings.FEQ.empty():
            curr_time, obj, state = settings.FEQ.get_nowait()
            settings.CURR_TIME = curr_time
            obj.update_state(state)

        # commit changes to person_logger
        person_logger.conn.commit()
        print("Done with", day)

    sim_stats.run_stats(person_log_path=person_logger_path, stats_dir=os.path.join(dirs, "stats"))
    print("done simulating", result_dir)


def test_look_elevator(limit=None):
    """method that tests the look elevator"""

    result_dir = "look"

    # create directory if not existing
    dirs = os.path.join(BASE_DIR, result_dir)
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    # create loggers
    person_logger_path = os.path.join(dirs, settings.LOG_DIR, settings.PERSON_LOG_FNAME)
    person_logger = logger.PersonLogger(person_logger_path, remove_old=True)
    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=person_logger)

    days = ["M", "Tu", "W", "Th", "F"]

    for day in days:
        # load saved arrivals or generate new arrivals
        arr_gen.arrival_times = []
        save_path = os.path.join(settings.ARRIVALS_DIR, "{}_arrivals.csv".format(day))
        if not os.path.exists(save_path):
            arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV, days=[day])
            arr_gen.save(save_path)
        else:
            arr_gen.load(save_path)

        # add first 100 floor arrivals to FEQ
        cnt = 0
        for time, person in arr_gen.arrival_times:
            cnt += 1
            if limit is not None and cnt > limit:
                break
            settings.FEQ.put_nowait((time, person, person.States.QUEUED))

        # create 6 elevators
        settings.ELEVATORS = []
        for _ in range(6):
            settings.ELEVATORS.append(elevators.LookElevator(None, building))

        while not settings.FEQ.empty():
            curr_time, obj, state = settings.FEQ.get_nowait()
            settings.CURR_TIME = curr_time
            obj.update_state(state)

        # commit changes to person_logger
        person_logger.conn.commit()
        print("Done with", day)

    sim_stats.run_stats(person_log_path=person_logger_path, stats_dir=os.path.join(dirs, "stats"))
    print("done simulating", result_dir)

def test_nearest_elevator(limit=None):
    """method that tests nearest car first elevator"""

    result_dir = "nearest"

    # create directory if not existing
    dirs = os.path.join(BASE_DIR, result_dir)
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    # create loggers
    person_logger_path = os.path.join(dirs, settings.LOG_DIR, settings.PERSON_LOG_FNAME)
    person_logger = logger.PersonLogger(person_logger_path, remove_old=True)
    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=person_logger)

    days = ["M", "Tu", "W", "Th", "F"]

    for day in days:
        # load saved arrivals or generate new arrivals
        arr_gen.arrival_times = []
        save_path = os.path.join(settings.ARRIVALS_DIR, "{}_arrivals.csv".format(day))
        if not os.path.exists(save_path):
            arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV, days=[day])
            arr_gen.save(save_path)
        else:
            arr_gen.load(save_path)

        # add first 100 floor arrivals to FEQ
        cnt = 0
        for time, person in arr_gen.arrival_times:
            cnt += 1
            if limit is not None and cnt > limit:
                break
            settings.FEQ.put_nowait((time, person, person.States.QUEUED))

        # create 6 elevators
        settings.ELEVATORS = []
        controller = elevators.NearestCarElevatorController(building)
        controller.spawn_elevators(6, person_logger, building)
        settings.ELEVATORS.extend(controller.elevators)

        while not settings.FEQ.empty():
            curr_time, obj, state = settings.FEQ.get_nowait()
            settings.CURR_TIME = curr_time
            obj.update_state(state)

        # commit changes to person_logger
        person_logger.conn.commit()
        print("Done with", day)

    sim_stats.run_stats(person_log_path=person_logger_path, stats_dir=os.path.join(dirs, "stats"))
    print("done simulating", result_dir)

def test_sector_elevator(limit=None):
    """test for testing fixed sector algorithm"""

    result_dir = "FS0"

    # create directory if not existing
    dirs = os.path.join(BASE_DIR, result_dir)
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    # create loggers
    person_logger_path = os.path.join(dirs, settings.LOG_DIR, settings.PERSON_LOG_FNAME)
    person_logger = logger.PersonLogger(person_logger_path, remove_old=True)
    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=person_logger)

    days = ["M", "Tu", "W", "Th", "F"]

    for day in days:
        # load saved arrivals or generate new arrivals
        arr_gen.arrival_times = []
        save_path = os.path.join(settings.ARRIVALS_DIR, "{}_arrivals.csv".format(day))
        if not os.path.exists(save_path):
            arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV, days=[day])
            arr_gen.save(save_path)
        else:
            arr_gen.load(save_path)

        # add first 100 floor arrivals to FEQ
        cnt = 0
        for time, person in arr_gen.arrival_times:
            cnt += 1
            if limit is not None and cnt > limit:
                break
            settings.FEQ.put_nowait((time, person, person.States.QUEUED))

        # create 6 elevators
        settings.ELEVATORS = []
        controller = elevators.FixedSectorsElevatorController(building)
        controller.spawn_elevators(6, person_logger, building)
        #SET SECTORS
        controller.set_sector(0, ['G', '1'], ['1', '3'])
        controller.set_sector(1, ['G', '1'], ['1', '3'])
        controller.set_sector(2, ['G', '1'], ['1', '3'])
        controller.set_sector(3, ['G', '1'], ['10', '12'])
        controller.set_sector(4, ['SB', '11'], ['B', '12'])
        controller.set_sector(5, ['SB', 'B'], ['G', '1'])
        settings.ELEVATORS.extend(controller.elevators)

        while not settings.FEQ.empty():
            curr_time, obj, state = settings.FEQ.get_nowait()
            settings.CURR_TIME = curr_time
            obj.update_state(state)

        # commit changes to person_logger
        person_logger.conn.commit()
        print("Done with", day)

        settings.CURR_DAY += 1

    sim_stats.run_stats(person_log_path=person_logger_path, stats_dir=os.path.join(dirs, "stats"))
    print("done simulating", result_dir)

def test_sector_time_elevator(limit=None):
    """test for testing fixed sector algorithm"""
    result_dir = "FS4"

    # create directory if not existing
    dirs = os.path.join(BASE_DIR, result_dir)
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    # create loggers
    person_logger_path = os.path.join(dirs, settings.LOG_DIR, settings.PERSON_LOG_FNAME)
    person_logger = logger.PersonLogger(person_logger_path, remove_old=True)
    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=person_logger)

    days = ["M", "Tu", "W", "Th", "F"]

    for day in days:
        # load saved arrivals or generate new arrivals
        arr_gen.arrival_times = []
        save_path = os.path.join(settings.ARRIVALS_DIR, "{}_arrivals.csv".format(day))
        if not os.path.exists(save_path):
            arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV, days=[day])
            arr_gen.save(save_path)
        else:
            arr_gen.load(save_path)

        # add first 100 floor arrivals to FEQ
        cnt = 0
        for time, person in arr_gen.arrival_times:
            cnt += 1
            if limit is not None and cnt > limit:
                break
            settings.FEQ.put_nowait((time, person, person.States.QUEUED))

        # create 6 elevators
        settings.ELEVATORS = []
        controller = elevators.FixedSectorsTimePriorityElevatorController(building)
        controller.spawn_elevators(6, person_logger, building)
        #SET SECTORS
        controller.set_sector(0, ['G', '1'], ['1', '3'])
        controller.set_sector(1, ['G', '1'], ['1', '3'])
        controller.set_sector(2, ['G', '1'], ['1', '3'])
        controller.set_sector(3, ['G', '1'], ['10', '12'])
        controller.set_sector(4, ['SB', '11'], ['B', '12'])
        controller.set_sector(5, ['SB', 'B'], ['G', '1'])
        settings.ELEVATORS.extend(controller.elevators)

        while not settings.FEQ.empty():
            curr_time, obj, state = settings.FEQ.get_nowait()
            settings.CURR_TIME = curr_time
            obj.update_state(state)

        # commit changes to person_logger
        person_logger.conn.commit()
        print("Done with", day)

    sim_stats.run_stats(person_log_path=person_logger_path, stats_dir=os.path.join(dirs, "stats"))
    print("done simulating", result_dir)

if __name__ == '__main__':
    START = timer()

    test_scan_elevator()
    test_look_elevator()
    test_nearest_elevator()
    test_sector_elevator()
    test_sector_time_elevator()

    END = timer()
    print(END - START)
