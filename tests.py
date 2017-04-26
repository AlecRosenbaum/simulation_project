"""handles all testing for the simulation models"""
import os

import settings
from person import ArrivalGenerator
from building import Building
import elevators
import logger

import stats as sim_stats

def testScanElevator():
    """main"""

    # create loggers
    person_logger = logger.PersonLogger(
        os.path.join(settings.LOG_DIR, settings.PERSON_LOG_FNAME), remove_old=True)
    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=person_logger)

    # load saved arrivals or generate new arrivals
    save_path = os.path.join(settings.ARRIVALS_DIR, "test_arrivals.csv")
    if not os.path.exists(save_path):
        arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV)
        arr_gen.save(save_path)
    else:
        arr_gen.load(save_path)

    # add first 100 floor arrival to FEQ
    cnt = 0
    for time, person in arr_gen.arrival_times:
        cnt += 1
        if cnt > 100:
            break
        settings.FEQ.put_nowait((time, person, person.States.QUEUED))

    # create an elevator
    settings.ELEVATORS.append(elevators.ScanElevator(None, building))

    while not settings.FEQ.empty():
        curr_time, obj, state = settings.FEQ.get_nowait()
        settings.CURR_TIME = curr_time
        obj.update_state(state)

    # commit changes to person_logger
    person_logger.conn.commit()

    sim_stats.main()


if __name__ == '__main__':
    testScanElevator()
