from credentials import DB_INFO
from scipy import optimize
from sklearn.cluster import MeanShift
import helpers
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pymysql as mdb
from pymysql.err import ProgrammingError


def get_tag_status(tag, city_id):
    # Connect to the database
    DB_NAME = 'flickr_data'
    con = mdb.connect(
            DB_INFO['host'],
            DB_INFO['user'],
            DB_INFO['password'],
            DB_NAME,
            autocommit=True,
            )

    # If the tag is in the results table already, do nothing
    with con:
        cur = con.cursor()
        SELECT = """SELECT count(*)
        AS tag_count
        FROM tags t, results r
        WHERE t.tag = '{tag}'
        AND r.tag_id = t.tag_id
        AND r.city_id = {city}""".format(
                tag=tag,
                city=city_id
                )
        cur.execute(SELECT)
        rows = cur.fetchall()
        entries = rows[0][0]


    cur.close()
    con.close()

    return bool(entries)


def get_similar_good_photo_locations(tag, city_id, tag_graph, distance_cutoff=5, minimum_photos=20, best_percentage=0.2):
    nearby_tags = nx.single_source_dijkstra_path_length(tag_graph, tag, cutoff=5)
    tags = nearby_tags.keys()
    views_and_coords = sorted(helpers.get_photos_from_tags(tags, city_id))
    saved_coords = []

    # Save the top 20, or 10% of photos, whichever is larger
    for views, photo_id, url, coord in reversed(views_and_coords):
        saved_coords.append(coord)
        if len(saved_coords) >= 20 \
        and float(len(saved_coords)) / len(views_and_coords) > 0.1:
            break

    return saved_coords


def make_normalized_kde(photo_kde, all_kde, base_map):
    def normalized_kde(coord):
        value = -np.true_divide(photo_kde(coord), all_kde(coord))
        try:
            adjustment = abs(value) * 5 * (not bool(base_map.is_land(coord[0], coord[1])))
        except TypeError:
            adjustment = np.array([(5 * (not bool(base_map.is_land(x, y)))) for (x, y) in zip(coord[0], coord[1])])

        return value + adjustment

    return normalized_kde


def hand_coded_seed_points(base_map):
    lat_lons = [
            (37.78561, -122.40774), # Downtown SF
            (37.76824, -122.48156), # Golden Gate Park
            (37.79850, -122.46748), # Persidio
            (37.83308, -122.48945), # Marin Headlands
            (37.86073, -122.42954), # Angel Island
            (37.82641, -122.42251), # Alcatraz
            (37.82444, -122.37174), # Treasure Island
            (37.80396, -122.25865), # Lake Merit
            (37.87175, -122.26123), # UC Berkeley
            ]
    x, y = zip(*[base_map(lon, lat) for (lat, lon) in lat_lons])

    return x, y


def write_result(tag, coord, city_id):
    DB_NAME = 'flickr_data'
    con = mdb.connect(
            DB_INFO['host'],
            DB_INFO['user'],
            DB_INFO['password'],
            DB_NAME,
            autocommit=True,
            )

    # Get tag ID
    with con:
        cur = con.cursor()
        SELECT = "SELECT tag_id FROM tags WHERE tag = '{tag}'".format(
                tag=tag
                )
        cur.execute(SELECT)
        rows = cur.fetchall()
        tag_id = rows[0][0]

    cur.close()

    # If the tag is in the results table already, do nothing
    with con:
        if coord.lat is not None and coord.lon is not None:
            cur = con.cursor()
            INSERT = """INSERT INTO results
            (tag_id, city_id, photo_id, lat, lon)
            VALUES
            ({tag_id},{city_id},{lat},{lon});
            """.format(
                    tag_id=tag_id,
                    city_id=city_id,
                    lat=coord.lat,
                    lon=coord.lon,
                    )
        else:
            INSERT = """INSERT INTO results
            (tag_id, city_id, photo_id, lat, lon)
            VALUES
            ({tag_id},{city_id},NULL,NULL);
            """.format(
                    tag_id=tag_id,
                    city_id=city_id,
                    lat=coord.lat,
                    lon=coord.lon,
                    )

        try:
            cur.execute(INSERT)
        except ProgrammingError:
            print "FAILED TO INSERT"
            print INSERT
            return

    cur.close()
    con.close()


def get_fit_starts(photo_locations):
    X_for_cluster = np.array(
            [np.array((coord.x, coord.y)) for coord in photo_locations]
            )
    # Clustering fails for small samples, but since they are small, just brute
    # force
    if len(X_for_cluster) > 2:
        cluster = MeanShift()
        cluster.fit(X_for_cluster)
        cluster_x, cluster_y = zip(*cluster.cluster_centers_)
    else:
        cluster_x, cluster_y = zip(*X_for_cluster)

    return cluster_x, cluster_y


def find_the_minimum(photo_locations, normalized_kde, cluster_points, base_map):
    # Find the range of values to use for bounds
    X = np.array([coord.x for coord in photo_locations])
    Y = np.array([coord.y for coord in photo_locations])
    xmin = X.min()
    ymin = Y.min()
    xmax = X.max()
    ymax = Y.max()

    # We brute force by searching from our cluster points
    minimum = (float("inf"), (0, 0))
    bounds = ((xmin, xmax), (ymin, ymax))
    for x, y in zip(cluster_points[0], cluster_points[1]):
        results = optimize.minimize(
                normalized_kde,
                (x, y),
                bounds = bounds,
                )
        if results['fun'] < minimum[0]:
            x_peak, y_peak = results['x'][0], results['x'][1]
            minimum = (results['fun'], (x_peak, y_peak))

    x_peak, y_peak = minimum[1]
    lon_peak, lat_peak = base_map(x_peak, y_peak, inverse=True)
    best_coord = helpers.Coordinate(lat_peak, lon_peak)
    best_coord.x = x_peak
    best_coord.y = y_peak

    return best_coord


def make_heat_map(photo_locations, normalized_kde):
    # Find the range of values to use for bounds
    X = np.array([coord.x for coord in photo_locations])
    Y = np.array([coord.y for coord in photo_locations])
    xmin = X.min()
    ymin = Y.min()
    xmax = X.max()
    ymax = Y.max()

    # Make the grid to sample on
    X_POS, Y_POS = np.mgrid[xmin:xmax:25j, ymin:ymax:25j]
    positions = np.vstack([X_POS.ravel(), Y_POS.ravel()])
    Z = np.reshape(normalized_kde(positions).T, X_POS.shape)

    return Z

def save_plot(base_map, tag, photo_locations, best_coord, cluster_points=None, heat_map=None):

    # Find the range of values to use for bounds
    for coord in photo_locations:
        coord.set_xy(base_map)
    best_coord.set_xy(base_map)
    X = np.array([coord.x for coord in photo_locations])
    Y = np.array([coord.y for coord in photo_locations])
    xmin = X.min()
    ymin = Y.min()
    xmax = X.max()
    ymax = Y.max()

    # Make the figure
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # Draw the map
    base_map.drawcoastlines()
    #base_map.fillcontinents(color='grey')
    #base_map.drawmapboundary()

    # Draw the heat map
    if heat_map is not None:
        ax.imshow(
                np.rot90(heat_map),
                cmap=plt.get_cmap("OrRd_r"),
                extent=[xmin, xmax, ymin, ymax],
                vmax=abs(heat_map).max(),
                vmin=-abs(heat_map).max(),
                )

    # Plot the data
    ax.plot(X, Y, 'k.', markersize=3)

    # Plot the seed clusters
    if cluster_points is not None:
        ax.plot(cluster_points[0], cluster_points[1], 'g^', markersize=3)

    ax.plot(best_coord.x, best_coord.y, 'bo', markersize=5)

    # These values are from the all map for SF
    xs = (9280.2130129241632, 64886.100965711179)
    ys = (11277.447582875378, 73062.806598237716)
    ax.set_xlim(xs)
    ax.set_ylim(ys)

    output_name = "fit_plots/{tag}.png".format(tag=tag)
    plt.savefig(output_name, bbox_inches='tight')
    plt.close('all')


def find_best_location(tag, city_id, tag_graph, base_map, all_kde):
    from time import time as t
    start = t()
    # Check if we already have a result
    result_exists = get_tag_status(tag, city_id)
    if result_exists:
        print "\tSkipping", tag
        return

    # Get the nearby tags, and then the lats and lons from them
    ok_photo_locations = get_similar_good_photo_locations(tag, city_id, tag_graph)
    if len(ok_photo_locations) <= 0:
        null_coord = helpers.Coordinate(None, None)
        write_result(tag, null_coord, city_id)
        return
    if len(ok_photo_locations) == 1:
        good_photo_locations = ok_photo_locations
    else:
        good_photo_locations = []
        for coord in ok_photo_locations:
            coord.set_xy(base_map)
            # Prune items in the ocean or bay
            if base_map.is_land(coord.x, coord.y):
                good_photo_locations.append(coord)

    # Set up a KDE of the good photos
    if len(good_photo_locations) <= 0:
        null_coord = helpers.Coordinate(None, None)
        write_result(tag, null_coord, city_id)
        return
    # If only one matching photo, that is the best location
    elif len(good_photo_locations) == 1:
        write_result(tag, good_photo_locations[0], city_id)
        save_plot(base_map, tag, good_photo_locations, good_photo_locations[0])
        return
    else: 
        photo_kde = helpers.get_xy_kde(good_photo_locations)
        normalized_kde = make_normalized_kde(photo_kde, all_kde, base_map)

    #print "Done getting photos in", t() - start, "seconds"
    #start = t()

    # Cluster the points to seed minimiation
    #cluster_points = get_fit_starts(good_photo_locations)
    cluster_points = hand_coded_seed_points(base_map)

    #print "Done clustering in", t() - start, "seconds"
    #start = t()

    # Find the minimum of normalized KDE starting from the cluster locations
    best_coord = find_the_minimum(good_photo_locations, normalized_kde, cluster_points)

    #print "Done fitting in", t() - start, "seconds"
    #start = t()

    # Writing to the database
    write_result(tag, best_coord, city_id)

    # Plot the results
    heat_map = make_heat_map(good_photo_locations, normalized_kde)
    save_plot(base_map, tag, good_photo_locations, best_coord, cluster_points, heat_map)

    #print "Done with plotting in", t() - start, "seconds"
    #start = t()
