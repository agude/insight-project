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
print files

# Get a set of current tags
with con:
   cur = con.cursor()
   cur.execute("SELECT tag FROM tags")
   rows = cur.fetchall()
   TAGS_LIST = [tag for tag, in rows]
   EXISTANT_TAGS = set(TAGS_LIST)

# Pull out the tags
with con:
    cur = con.cursor()
    for file in files:
        with open(file, "rb") as read_file:
            reader = csv.reader(read_file)
            for row in reader:
                tags = tags_from_csv_field(row[9])
                for tag in tags:
                    if tag not in EXISTANT_TAGS:
                        INSERT = """INSERT INTO tags
                        (tag)
                        VALUES
                        ("{tag}")""".format(
                                tag=tag
                                )
                        cur.execute(INSERT)
                        # Add to the set to prevent duplication
                        EXISTANT_TAGS.add(tag)
