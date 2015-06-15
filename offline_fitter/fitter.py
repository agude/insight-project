#!/home/agude/bin/anaconda/bin/python

import cPickle as pk
import multiprocessing as mp
from best_position import find_best_location
import helpers

# Hardcode the city
CITY_ID = 1
DISTANCE_CUT = 25

# Number of jobs to run at once
NJOBS = int(mp.cpu_count())

# Load the tag relation graph
tag_graph = pk.load(open("../pickles/sf_tag_graph.pickle", "rb"))

# Set up the map
base_map = helpers.get_map(CITY_ID)

# Set up the all photo KDE
photo_coords = helpers.get_all_photos(CITY_ID)
for coord in photo_coords:
    coord.set_xy(base_map)

all_kde = helpers.get_xy_kde(photo_coords)

# Dummy function to pass multiple parameters through pool.map
def dummy(tag):
    print "Working on tag:", tag
    find_best_location(tag, CITY_ID, tag_graph, base_map, all_kde)
    print "Done with tag:", tag

for tag in tag_graph.nodes():
    #dummy(tag)
    dummy("bryanday")
    import sys
    sys.exit()

# Set up the arguments to pass to the script
#tags = [tag for tag in tag_graph]
#pool = mp.Pool(processes=NJOBS)
#pool.map(dummy, tags)

# Run jobs in parallel
pool.close()  # No more tasks to add
pool.join()  # Wait for jobs to finish
