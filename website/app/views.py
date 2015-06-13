from flask import render_template, request
from app import app
import numpy as np
import pymysql as mdb
from a_Model import ModelIt
import cPickle as pickle
import networkx as nx
from os import getcwd
from settings import APP_ROOT, APP_STATIC
from kde import calculate_all_kde, calculate_specific_kde
from time import time as t
from my_sql_readers import coords_from_city_and_tags
from minimizer import best_position
import json

db = mdb.connect(user="readonly", host="localhost", db="flickr_data", charset='utf8')

CITY_ID = 1 # 1 is SF
SF_LAT = 37.7361172
SF_LON = -122.423565

GLOBAL = {"START_TIME": t()}

# Code to load objects
@app.before_first_request
def load_graph():
    GLOBAL['sf_tag_graph'] = pickle.load(open(APP_STATIC+"/pickles/sf_tag_graph.pickle", "rb"))

@app.before_first_request
def setup_all_kde():
    GLOBAL['all_photo_kde'] = calculate_all_kde(CITY_ID, db)

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
       title = 'Home',
       output = str("Loaded in: %i seconds" %(t() - GLOBAL['START_TIME'])),
       )

@app.route('/input')
def cities_input():
  return render_template("input.html")

@app.route('/output')
def cities_output():
    #pull 'ID' from input field and store it
    tag = request.args.get('ID')

    # Clean up the tag
    clean_tag = tag.strip().lower().replace(' ', '')

    # Try to get related tags
    try:
        simularity_distance_max = 5
        related_tags = nx.single_source_dijkstra_path_length(GLOBAL['sf_tag_graph'], tag, cutoff=simularity_distance_max)
    except KeyError:
        return render_template("index.html",
            title = 'ERROR',
            output = 'Your tag is missing!'
        )

    # Get coords
    coords = coords_from_city_and_tags(related_tags, CITY_ID, db)
    views, lats, lons = zip(*coords)
    views = np.array(views)
    lats = np.array(lats)
    lons = np.array(lons)

    median_views = np.median(views)
    std_views = np.std(views)

    # Filter for good photos
    lats = lats[views > median_views + std_views]
    lons = lons[views > median_views + std_views]
    coords = list(zip(lons, lats))

    # Get the new KDE for these tags
    tags_kde = calculate_specific_kde(coords)

    # Get the best position from the KDE
    best_lon, best_lat, start_lon, start_lat = best_position(tags_kde, GLOBAL['all_photo_kde'], coords)

    leaflet_coords = list(zip(lats, lons))
    return render_template("output.html",
            best_lon = best_lon,
            best_lat = best_lat,
            start_lon = start_lon,
            start_lat = start_lat,
            coords = json.dumps(list(leaflet_coords))
            )
