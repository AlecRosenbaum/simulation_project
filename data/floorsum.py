"run a quick check on csv file to see distribution of class on floors"

import csv
import sqlite3


FILE_NAME = "class_enrollment_list.csv"

CREATE_STMT = "CREATE TABLE t (Room, Enrollment);"

def main():
    """main"""

    #open file
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute(CREATE_STMT)
    with open('class_enrollment_list.csv', 'r') as fin: # `with` statement available in 2.5+
    # csv.DictReader uses first line in file for column headings by default
        dict_read = csv.DictReader(fin) # comma is default delimiter
        to_db = [(i['Room'], i['Enrollment Total']) for i in dict_read]
    cur.executemany("INSERT INTO t (Room, Enrollment) VALUES (?, ?);", to_db)
    con.commit()

    select_chunks = ["WITH Temp AS (",
                     " SELECT Enrollment, CASE ",
                     " WHEN ROOM LIKE '%SB%' THEN 'SB'",
                     " WHEN Room LIKE '00B%' THEN 'B'",
                     " WHEN Room LIKE '00G%' THEN 'G'",
                     " WHEN Room LIKE '%1__' THEN '1'",
                     " WHEN Room LIKE '%2__' THEN '2'",
                     " WHEN Room LIKE '%3__' THEN '3'",
                     " WHEN Room LIKE '%4__' THEN '4'",
                     " WHEN Room LIKE '%5__' THEN '5'",
                     " WHEN Room LIKE '%6__' THEN '6'",
                     " WHEN Room LIKE '%7__' THEN '7'",
                     " WHEN Room LIKE '%8__' THEN '8'",
                     " WHEN Room LIKE '%9__' THEN '9'",
                     " WHEN Room LIKE '%10__' THEN '10'",
                     " WHEN Room LIKE '%11__' THEN '11'",
                     " WHEN Room LIKE '%12__' THEN '12'",
                     " ELSE NULL",
                     " END AS Floor FROM t)",
                     "SELECT Floor, SUM(Enrollment) as Total_Per_Floor",
                     " FROM Temp",
                     " GROUP BY Floor"]
    select_stmt = ''.join(select_chunks)
    cur.execute(select_stmt)
    rows = cur.fetchall()

    for row in rows:
        print(row)

    con.close()

if __name__ == '__main__':
    main()
