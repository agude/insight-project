from app import app
from flask import render_template, request
from settings import APP_ROOT, APP_STATIC
import helpers
import json

CITY_ID = 1 # 1 is SF

@app.route('/')
@app.route('/index')
def cities_input():
  return render_template("input.html")

@app.route('/output')
def cities_output():
    #pull 'ID' from input field and store it
    tag = request.args.get('ID')
    if tag is None:
        tag = 'goldengate'

    # Clean up the tag
    clean_tag = tag.strip().lower().replace(' ', '')

    # Get coords from results
    best_coord = helpers.get_results_from_tag(clean_tag)

    # Get all the photos
    photo_coords = helpers.get_photos_from_tags((clean_tag,), CITY_ID)
    leaflet_coords = []
    seen_photos = []
    for (views, photo_id, url, coord) in photo_coords:
        datum = {
                "lat": coord.lat,
                "lon": coord.lon,
                "url": url,
                "photo_id": photo_id,
                "views": views,
                }
        seen_photos.append(photo_id)
        leaflet_coords.append(datum)

    seen_photos = set(seen_photos)

    # Get related tags
    related_tags = helpers.get_related_tags(clean_tag)
    related_photo_coords = helpers.get_photos_from_tags(related_tags, CITY_ID)
    related_leaflet_coords = []
    for (views, photo_id, url, coord) in related_photo_coords:
        datum = {
                "lat": coord.lat,
                "lon": coord.lon,
                "url": url,
                "photo_id": photo_id,
                "views": views,
                }
        if photo_id not in seen_photos:
            related_leaflet_coords.append(datum)

    # Set the page title string
    title = tag.capitalize()
    print title

    # Render the page
    return render_template("output.html",
            title = title,
            best_lon = best_coord.lon,
            best_lat = best_coord.lat,
            related_coords = json.dumps(list(related_leaflet_coords)),
            tag_coords = json.dumps(list(leaflet_coords)),
            )
