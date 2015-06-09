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
            """CREATE TABLE IF NOT EXISTS photos
            (
                photo_id BIGINT PRIMARY KEY NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                date_taken DATETIME,
                views INT NOT NULL,
                lat DOUBLE NOT NULL,
                lon DOUBLE NOT NULL,
                city_id INT NOT NULL
            )
            """
            )
