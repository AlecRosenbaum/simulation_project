"""used in recording data (python 3)

usage: python recording_tool.py
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
