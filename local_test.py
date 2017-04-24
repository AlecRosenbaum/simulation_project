"""This is a file for local testing"""

import settings
from person import ArrivalGenerator
from building import Building
import elevators

def main():
    """main"""

    # create building
    building = Building([
        'SB', 'B', 'G', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',])

    # generate arrivals
    arr_gen = ArrivalGenerator(building=building, person_logger=None)
    arr_gen.gen_from_classes(file_path=settings.ARRIVALS_DATA_SET_CSV)

    # add first 100 floor arrival to FEQ
    cnt = 0
    for time, person in arr_gen.arrival_times:
        cnt += 1
        if cnt > 100:
            break
        settings.FEQ.put_nowait((time, person, person.States.QUEUED))
        # print("added person:", time, person, person.States.QUEUED)

    # create an elevator
    settings.ELEVATORS.append(elevators.BasicElevator(None, building))

    cnt = 0
    while not settings.FEQ.empty() and cnt < 100:
        curr_time, obj, state = settings.FEQ.get_nowait()
        settings.CURR_TIME = curr_time
        obj.update_state(state)
        cnt += 1


if __name__ == '__main__':
    main()
