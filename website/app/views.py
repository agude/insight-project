from app import app
from flask import render_template, request
from settings import APP_ROOT, APP_STATIC
import helpers
import json

CITY_ID = 1 # 1 is SF
SF_LAT = 37.7361172
SF_LON = -122.423565

@app.route('/index')
def index():
    return render_template("index.html",
       title = 'Home',
       output = str("Loaded in: %i seconds" %(t() - GLOBAL['START_TIME'])),
       )

@app.route('/')
@app.route('/input')
def cities_input():
  return render_template("input.html")

@app.route('/output')
def cities_output():
    #pull 'ID' from input field and store it
    tag = request.args.get('ID')

    # Clean up the tag
    clean_tag = tag.strip().lower().replace(' ', '')

    # Get coords from results
    best_coord = helpers.get_results_from_tag(clean_tag)

    # Get all the photos
    photo_coords = helpers.get_photos_from_tags((clean_tag,), CITY_ID)
    leaflet_coords = [(coord.lat, coord.lon) for (views, coord) in photo_coords]

    # Render the page
    return render_template("output.html",
            best_lon = best_coord.lon,
            best_lat = best_coord.lat,
            coords = json.dumps(list(leaflet_coords))
            )
