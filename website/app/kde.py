from distance import delta_r
from my_sql_readers import lat_lon
import numpy as np
from scipy import stats

def calculate_all_kde(CITY_ID, db_connection):
    # FIXME
    SF_LAT = 37.7361172
    SF_LON = -122.423565
    # Get the coordinates of all photos in the city
    out_coords = lat_lon(CITY_ID, db_connection)
    lats = []
    lons = []
    for lat, lon in out_coords:
        if delta_r(lat, lon, SF_LAT, SF_LON) < 25: # in km
            lats.append(lat)
            lons.append(lon)

    # Get the coordinates
    lats = np.array(lats)
    lons = np.array(lons)

    print "Lon", lons[0], "Lat", lats[0]

    # Make a grid to sample on
    values = np.vstack([lons, lats])
    kde = stats.gaussian_kde(values, bw_method=0.2)
    return kde


def calculate_specific_kde(coords):
    # FIXME
    SF_LAT = 37.7361172
    SF_LON = -122.423565

    lats = []
    lons = []
    for lon, lat in coords:
        if delta_r(lat, lon, SF_LAT, SF_LON) < 25: # in km
            lats.append(lat)
            lons.append(lon)

    # Get the coordinates
    lats = np.array(lats)
    lons = np.array(lons)

    print "Lon", lons[0], "Lat", lats[0]

    # Make a grid to sample on
    values = np.vstack([lons, lats])

    
    kde = stats.gaussian_kde(values, bw_method=0.2)
    return kde
