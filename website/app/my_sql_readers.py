import pymysql as mdb

def lat_lon(city, con):
    """ Return a list of (lat,lon) tuples from a city_id. """
    with con:
        cur = con.cursor()
        SELECT = """SELECT lat, lon
        FROM photos
        WHERE city_id = {city}
        """.format(
                city=city
                )
        cur.execute(SELECT)
        return set([(lat, lon) for (lat, lon) in cur])


def coords_from_city_and_tags(tags, city, con):
    """ Returns a list of (views, lat, lon) tuples that contain one of a list of
    tags. """
    with con:
        cur = con.cursor()
        str_tags = [tag for tag in tags]
        TAGS = "('" + "','".join(str_tags) + "')"
        SELECT = """SELECT p.views, p.lat, p.lon
        FROM photo_tags pt, photos p, tags t
        WHERE p.city_id = {city_id}
        AND pt.photo_id = p.photo_id
        AND pt.tag_id = t.tag_id
        AND t.tag in {tags}
        """.format(
                tags=TAGS,
                city_id=city
                )
        cur.execute(SELECT)
        return set([(views, lat, lon) for (views, lat, lon) in cur])
