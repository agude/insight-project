from math import sin, cos, sqrt, atan2, radians

def delta_r(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0

    lat1r = radians(lat1)
    lon1r = radians(lon1)
    lat2r = radians(lat2)
    lon2r = radians(lon2)

    dlon = lon2r - lon1r
    dlat = lat2r - lat1r

    a = sin(dlat / 2)**2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance
