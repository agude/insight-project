from credentials import DB_INFO
import pymysql as mdb
from sys import argv
from utils.tags import tags_from_csv_field
import csv

DB_NAME = 'flickr_data'
con = mdb.connect(
        DB_INFO['host'],
        DB_INFO['user'],
        DB_INFO['password'],
        DB_NAME
        )

# Get the CSV files to check for tags
city_id = int(argv[1])
files = argv[2:]
print files

# Get a set of current tags
with con:
   cur = con.cursor()
   cur.execute("SELECT photo_id FROM photos")
   rows = cur.fetchall()
   PID_LIST = [pid for pid, in rows]
   EXISTANT_PIDS = set(PID_LIST)

# Pull out the data from the CSV
with con:
    cur = con.cursor()
    for file in files:
        with open(file, "rb") as read_file:
            reader = csv.reader(read_file)
            for row in reader:
            # Pack the data
                data = {
                    "photo_id": int(row[0]),
                    "user_id": '"{string}"'.format(string=str(row[1])),
                    "date_taken": "'{date}'".format(date=str(row[6])),
                    "views": int(row[8]),
                    "lat": float(row[11]),
                    "lon": float(row[12]),
                    "city_id": city_id,
                }
                # Insert into the database
                if data['photo_id'] not in EXISTANT_PIDS:
                    INSERT = """INSERT INTO photos
                    (
                        photo_id,
                        user_id,
                        date_taken,
                        views,
                        lat,
                        lon,
                        city_id
                    )
                    VALUES
                    ({photo_id},{user_id},{date_taken},{views},{lat},{lon},{city_id})""".format(
                            photo_id=data['photo_id'],
                            user_id=data['user_id'],
                            date_taken=data['date_taken'],
                            views=data['views'],
                            lat=data['lat'],
                            lon=data['lon'],
                            city_id=data['city_id']
                            )
                    #print INSERT
                    cur.execute(INSERT)
                    EXISTANT_PIDS.add(data['photo_id'])
