from math import sin, cos, sqrt, atan2, radians
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy import stats, optimize
from math import sin, cos, sqrt, atan2, radians
import pymysql as mdb
from credentials import DB_INFO

DB_NAME = 'flickr_data'
con = mdb.connect(
        DB_INFO['host'],
        DB_INFO['user'],
        DB_INFO['password'],
        DB_NAME,
        autocommit=True,
        )

con_read = mdb.connect(
        DB_INFO['host'],
        DB_INFO['readonly_user'],
        DB_INFO['password'],
        DB_NAME,
        autocommit=True,
        )

class Coordinate:

    def __init__(self, lat, lon):
        self.lon = lon
        self.lat = lat
        self.coord = (lat, lon)

    def set_xy(self, basemap):
        self.x, self.y = basemap(self.lon, self.lat)
        self.xy = (self.x, self.y)

    def distance_to(self, other):
        """ Returns the distance between two coordinate objects in km. """
        # Radius of earth in km
        R = 6373.0

        lat1r = radians(self.lat)
        lon1r = radians(self.lon)
        lat2r = radians(other.lat)
        lon2r = radians(other.lon)

        dlon = lon2r - lon1r
        dlat = lat2r - lat1r

        a = sin(dlat / 2)**2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance

    def __str__(self):
        return self.coord.__str__()

    def __repr__(self):
        return self.coord.__repr__()


def city_coordinate(city_id, con=con):
    with con:
        cur = con.cursor()
        SELECT = """SELECT lat, lon
                    FROM cities
                    WHERE city_id = {city_id}""".format(
                city_id=city_id
                )
        cur.execute(SELECT)
        rows = cur.fetchall()
        cur.close()

        (lat, lon) = rows[0]
        return Coordinate(lat, lon)


def get_map(city_id, box_size = 0.6, con=con):
    # Get the coordinates from the database
    coord = city_coordinate(city_id, con)

    # Get the corners of the map box
    offset = box_size / 2.
    ll_lon = coord.lon - offset
    ll_lat = coord.lat - offset
    ur_lon = coord.lon + offset
    ur_lat = coord.lat + offset

    # Set up the map object
    my_map = Basemap(
            projection='merc',
            lat_0=coord.lat,
            lon_0=coord.lon,
            #resolution = 'f',
            resolution = 'h',
            area_thresh = 0.1,
            llcrnrlon=ll_lon,
            llcrnrlat=ll_lat,
            urcrnrlon=ur_lon,
            urcrnrlat=ur_lat,
            )

    return my_map


def get_all_photos(city_id, radius=15, con=con):
    # Coordinates of the city to measure radius from
    city_center = city_coordinate(city_id, con)

    with con:
        cur = con.cursor()
        SELECT = """SELECT lat, lon
                    FROM photos
                    WHERE city_id = {city_id}""".format(
                city_id=city_id
                )
        cur.execute(SELECT)

        # Select photos within some distance of the city
        coords = []
        for lat, lon in cur:
            coord = Coordinate(lat, lon)
            if city_center.distance_to(coord) <= radius:
                coords.append(coord)
        cur.close()

        return np.array(coords)

def get_related_tags(tag, con=con_read):
    with con:
        cur = con.cursor()
        SELECT = """SELECT daughter.tag
        FROM tag_graph tg
        LEFT JOIN tags parent ON tg.tag_id = parent.tag_id
        LEFT JOIN tags daughter ON tg.related_tag = daughter.tag_id
        WHERE parent.tag = %s
        AND tg.distance <= 5;
        """
        cur.execute(SELECT, tag)
        rows = cur.fetchall()
        return [tag for (tag,) in rows]


def get_photos_from_tags(tags, city_id, radius=15, con=con_read):
    """ Returns a list of (views, lat, lon) tuples that contain one of a list
    of tags. """
    # Coordinates of the city to measure radius from
    city_center = city_coordinate(city_id, con)

    with con:
        cur = con.cursor()
        str_tags = [tag for tag in tags]
        TAGS = "('" + "','".join(str_tags) + "')"
        SELECT = """SELECT p.photo_id, p.views, p.lat, p.lon
        FROM photo_tags pt, photos p, tags t
        WHERE p.city_id = {city_id}
        AND pt.photo_id = p.photo_id
        AND pt.tag_id = t.tag_id
        AND t.tag in {tags}
        """.format(
                tags=TAGS,
                city_id=city_id
                )
        cur.execute(SELECT)
        output = []

        # Select photos within some distance of the city
        seen_ids = []
        for photo_id, views, lat, lon in cur:
            # Remove redundant photos
            if photo_id in seen_ids:
                continue
            seen_ids.append(photo_id)
            # Set up a tuple of coordinates and views
            coord = Coordinate(lat, lon)
            if city_center.distance_to(coord) <= radius:
                output.append((views, coord))
        cur.close()

        return output


def get_xy_kde(photo_coords):
    # Get x,y coordinates
    X, Y = zip(*((coord.x, coord.y) for coord in photo_coords))

    # Make a grid to sample on
    values = np.vstack([X, Y])
    return stats.gaussian_kde(values, bw_method=0.2)


def get_tags_to_run_on(city_id, graph_tags):
    with con:
        cur = con.cursor()

        # Get all tags
        SELECT = """SELECT tag
                FROM tags t"""
        cur.execute(SELECT)
        rows = cur.fetchall()
        all_tags = set([tag for tag, in rows if tag in graph_tags])

        # Get the tags we have already filled
        SELECT = """SELECT t.tag
                FROM tags t
                INNER JOIN results r ON t.tag_id = r.tag_id
                WHERE r.city_id = {city_id}""".format(
                        city_id=city_id,
                        )
        cur.execute(SELECT)
        rows = cur.fetchall()
        done_tags = set([tag for tag, in rows])

        # Tags to consider
        tags_to_consider = all_tags - done_tags

        # Find the most popular tags
        count_tag = []
        for tag in tags_to_consider:
            SELECT = """SELECT COUNT(pt.photo_id)
                    FROM photo_tags pt
                    INNER JOIN tags t ON pt.tag_id = t.tag_id
                    INNER JOIN photos p on pt.photo_id = p.photo_id
                    WHERE p.city_id = {city_id}
                    AND t.tag = '{tag}'""".format(
                            city_id=city_id,
                            tag=tag,
                            )
            cur.execute(SELECT)
            rows = cur.fetchall()
            count = rows[0][0]
            count_tag.append((count, tag))

        cur.close()

        # Sort the tags from most to least common
        tags_to_run_on = [tag for _, tag in reversed(sorted(count_tag))]

        return tags_to_run_on


def get_results_from_tag(tag, con=con_read):
    with con:
        cur = con.cursor()

        # Get all tags
        SELECT = """SELECT r.lat, r.lon, r.photo_id
        FROM results r
        LEFT JOIN tags t ON t.tag_id = r.tag_id
        WHERE t.tag = %s;
        """
        cur.execute(SELECT, tag)
        rows = cur.fetchall()
        cur.close()
        lat, lon, pid = rows[0]
        coord = Coordinate(lat, lon)

        return coord
