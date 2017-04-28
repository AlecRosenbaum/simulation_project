"""used in recording data (python 3)

usage: python recording_tool.py

It will ask for a file name. If the file exists, entries will be appended,
otherwise a new file will be made.

The csv will be have the data in the following format:
    person_#,time_of_entry_into_queue
"""

import os.path
import datetime

def main():
    """main"""
    fname = input("enter filename:")

    cnt = 0
    if os.path.isfile(fname):
        cnt = sum(1 for _ in open(fname))

    with open(fname, 'a') as fout:
        while True:
            input()
            out_str = ",".join([str(cnt), str(datetime.datetime.now())])
            print(out_str, end="")
            print(out_str, file=fout)
            cnt += 1


if __name__ == '__main__':
    main()
