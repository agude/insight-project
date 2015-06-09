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
files = argv[1:]

# Pull out the data from the CSV
with con:
    cur = con.cursor()
    for file in files:
        with open(file, "rb") as read_file:
            reader = csv.reader(read_file)
            i = 0
            for row in reader:
                i+=1
            # Pack the data
                photo_id = int(row[0])
                INSERT = "INSERT INTO photo_tags (photo_id,tag_id) VALUES " 
                values = []
                tags = tags_from_csv_field(row[9])
                for tag in tags:
                    SELECT = "SELECT tag_id FROM tags WHERE tag='{tag}'".format(tag=tag)
                    cur.execute(SELECT)
                    rows = cur.fetchall()
                    tag_id = rows[0][0]
                    values.append("({pid}, {tid})".format(pid=photo_id, tid=tag_id))

                # Insert into the table
                if values:
                    INSERT += ', '.join(values) + ";"
                    cur.execute(INSERT)
