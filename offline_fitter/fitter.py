#!/home/agude/bin/anaconda/bin/python

import cPickle as pk
import multiprocessing as mp
from best_position import find_best_location
import helpers
import numpy as np

# Hardcode the city
CITY_ID = 1
DISTANCE_CUT = 25

# Number of jobs to run at once
NJOBS = int(mp.cpu_count())

# Load the tag relation graph
tag_graph = pk.load(open("../pickles/sf_tag_graph.pickle", "rb"))
graph_tags = set(tag_graph.nodes())

# Find tags to run over
tags_to_run_on = helpers.get_tags_to_run_on(CITY_ID, graph_tags)

# Set up the map
base_map = helpers.get_map(CITY_ID)

# Set up the all photo KDE
photo_coords = helpers.get_all_photos(CITY_ID)
selected_photo_coords = []
for coord in photo_coords:
    coord.set_xy(base_map)
    # Prune items in the ocean or bay
    if base_map.is_land(coord.x, coord.y):
        selected_photo_coords.append(coord)

selected_photo_coords = np.array(selected_photo_coords)

all_kde = helpers.get_xy_kde(selected_photo_coords)

# Dummy function to pass multiple parameters through pool.map
def dummy(tag):
    print "Working on tag:", tag
    find_best_location(tag, CITY_ID, tag_graph, base_map, all_kde)
    print "Done with tag:", tag

for tag in tags_to_run_on:
    dummy(tag)
    import sys
    sys.exit()

# Set up the arguments to pass to the script
#tags = tags_to_run_on
#pool = mp.Pool(processes=NJOBS)
#pool.map(dummy, tags)

# Run jobs in parallel
#pool.close()  # No more tasks to add
#pool.join()  # Wait for jobs to finish
