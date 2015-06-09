from credentials import DB_INFO
import pymysql as mdb

DB_NAME = 'flickr_data'
con = mdb.connect(
        DB_INFO['host'],
        DB_INFO['user'],
        DB_INFO['password'],
        DB_NAME
        )

with con:
    cur = con.cursor()
    # Make the table
    cur.execute(
            """CREATE TABLE IF NOT EXISTS photo_tags
            (
                photo_id BIGINT NOT NULL,
                tag_id INT NOT NULL
            )
            """
            )
