from credentials import DB_INFO
import pymysql as mdb

DB_NAME = 'flickr_data'
con = mdb.connect(
        DB_INFO['host'],
        DB_INFO['user'],
        DB_INFO['password'],
        DB_NAME
        )

# The cities to add
cities = [
        {"lat": 37.7361172, "lon": -122.423565, "name": "San Francisco"},
        {"lat": 47.614848, "lon": -122.3359058, "name": "Seattle"},
        {"lat": 46.2050295, "lon": 6.1440885, "name": "Geneva"},
        {"lat": 40.7033127, "lon": -73.979681, "name": "New York"},
        {"lat": 51.5286417, "lon": -0.1015987, "name": "London"},
        {"lat": 41.8337329, "lon": -87.7321555, "name": "Chicago"},
        ]

with con:
    cur = con.cursor()
    # Make the table (delete it if it exists)
    cur.execute("DROP TABLE IF EXISTS cities")
    cur.execute(
            """CREATE TABLE IF NOT EXISTS cities
            (
                city_id INT PRIMARY KEY AUTO_INCREMENT,
                city_name VARCHAR(50) NOT NULL,
                city_lat DOUBLE NOT NULL,
                city_lon DOUBLE NOT NULL
            )"""
            )
    # Add cities
    for city in cities:
        print city
        INSERT = """INSERT INTO cities
        (city_name, city_lat, city_lon)
        VALUES
        ("{name}", {lat}, {lon})""".format(
                name=city["name"],
                lat=city["lat"],
                lon=city["lon"],
                )
        print INSERT
        cur.execute(INSERT)
