from credentials import DB_INFO
from scipy import optimize
from sklearn.cluster import MeanShift
import helpers
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pymysql as mdb


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

    for view, coord in reversed(views_and_coords):
        saved_coords.append(coord)
        if len(saved_coords) >= 20 \
        and float(len(saved_coords)) / len(views_and_coords) > 0.1:
            break

    #print "Best photos len:", len(saved_coords), saved_coords
    return saved_coords


def make_normalized_kde(photo_kde, all_kde, base_map):
    def normalized_kde(coord):
        value = -np.true_divide(photo_kde(coord), all_kde(coord))
        try:
            adjustment = abs(value) * (not bool(base_map.is_land(coord[0], coord[1])))
        except TypeError:
            adjustment = np.array([(not bool(base_map.is_land(x, y))) for (x, y) in zip(coord[0], coord[1])])

        return value + adjustment

    return normalized_kde


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
        cur = con.cursor()
        INSERT = """INSERT INTO results
        (tag_id, city_id, photo_id, lat, lon)
        VALUES
        ({tag_id}, {city_id}, {photo_id}, {lat}, {lon})
        """.format(
                tag_id=tag_id,
                city_id=city_id,
                photo_id = 0,
                lat = coord.lat,
                lon = coord.lon,
                )
        cur.execute(INSERT)

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


def find_best_location(tag, city_id, tag_graph, base_map, all_kde):
    from time import time as t
    start = t()
    # Check if we already have a result
    result_exists = get_tag_status(tag, city_id)
    if result_exists:
        print "\tSkipping", tag
        return

    # Get the nearby tags, and then the lats and lons from them
    good_photo_locations = get_similar_good_photo_locations(tag, city_id, tag_graph)
    for coord in good_photo_locations:
        coord.set_xy(base_map)

    # Set up a KDE of the good photos
    if len(good_photo_locations) > 1:
        photo_kde = helpers.get_xy_kde(good_photo_locations)
        normalized_kde = make_normalized_kde(photo_kde, all_kde, base_map)
    # If only one matching photo, that is the best location
    else:
        write_result(tag, good_photo_locations[0], city_id)
        save_plot(base_map, tag, good_photo_locations, good_photo_locations[0])

    #print "Done getting photos in", t() - start, "seconds"
    #start = t()

    # Cluster the points to seed minimiation
    cluster_points = get_fit_starts(good_photo_locations)

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
