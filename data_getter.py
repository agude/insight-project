#!/usr/bin/env python
# -*- coding: utf-8 -*-

from secret import API_SECRET
import flickrapi as api
from lxml import etree
import csv
import datetime
from time import sleep
import sys

def date_range(start_date, end_date):
    delta = datetime.timedelta(days=1)
    while start_date < end_date:
        yield start_date.strftime("%Y-%m-%d"), (start_date + delta).strftime("%Y-%m-%d")
        start_date += delta

def uni_to_ascii(string):
    return unicode(string).encode('ascii', 'ignore')

def get_size(element):
    h0 = element.get("o_height")
    h1 = element.get("height_o")
    w0 = element.get("o_width")
    w1 = element.get("width_o")

    if h0:
        h = int(h0)
    elif h1:
        h = int(h1)
    else:
        h = "\N"

    if w0:
        w = int(w0)
    elif w1:
        w = int(w1)
    else:
        w = "\N"

    return [h, w]

def tuplize_element(element):
    output = []
    key_type = (
            ("id", str),
            ("owner", uni_to_ascii),
            ("secret", str),
            #("server", int),
            #("farm", int),
            ("title", uni_to_ascii),
            #("ispublic", bool),
            #("isfriend", bool),
            #("isfamily", bool),
            ("license", int),
            ("dateupload", str),
            ("datetaken", str),
            #("datetakengranularity", int),
            #("datetakenunknown", int),
            ("ownername", uni_to_ascii),
            ("views", int),
            ("tags", uni_to_ascii), # Split on space
            ("machine_tags", uni_to_ascii), # Split on space
            #("originalsecret", str),
            #("originalformat", str),
            ("latitude", float),
            ("longitude", float),
            ("accuracy", int),
            ("context", int),
            ("place_id", str),
            ("woeid", str),
            #("geo_is_family", bool),
            #("geo_is_friend", bool),
            #("geo_is_contact", bool),
            #("geo_is_public", bool),
            ("media", str),
            ("media_status", str),
            ("url_o", str),
            ("url_n", str),
            )
    for key, converter in key_type:
        try:
            output.append(converter(element.get(key)))
        except:
            print "Failed: ", key
            output.append("\N")

    return output

# Set up the downloader
API_KEY = u"c8c6aa2b82851c9991fe44ec5228e644"

# All of the data to be returned
extras_to_get = "description,license,date_upload,date_taken,owner_name,original_format,geo,tags,machine_tags,o_dims,views,media,url_o,url_n"

# San Francisco
city = {"lat": 37.7361172, "lon": -122.423565, "name": "sf"}

# Seattle
#city = {"lat": 47.614848, "lon": -122.3359058, "name": "seattle2"}

# Geneva
#city = {"lat": 46.2050295, "lon": 6.1440885, "name": "geneva"}

# New York
#city = {"lat": 40.7033127, "lon": -73.979681, "name": "new_york2"}

# London
#city = {"lat": 51.5286417, "lon": -0.1015987, "name": "london"}

# London
#city = {"lat": 41.8337329, "lon": -87.7321555, "name": "chicago"}


# Make an output file
output_name = "./data/ALL_{name}.csv".format(name=city["name"])

with open(output_name, "wb") as output_csv:
    csv_writer = csv.writer(output_csv)

    # Loop over days
    for min_date, max_date in date_range(datetime.date(2014, 5, 31), datetime.date(2015, 5, 31)):
        success = False
        print "{min} to {max}:".format(
                min=min_date,
                max=max_date
                ),
        while not success:
            sleep(2)
            try:
                flickr = api.FlickrAPI(API_KEY, API_SECRET)
                # Create a generator over pictures from a flickr search
                walker = flickr.walk(
                        min_taken_date=min_date,
                        max_taken_date=max_date,
                        privacy_filter=1, # Public
                        per_page=500,
                        has_geo=True,
                        safe_search=1, # Safe
                        content_type=1, # Photos only
                        media=u"photos",
                        extras=extras_to_get,
                        lat = city["lat"],
                        lon = city["lon"],
                        radius = 20, # km
                        )
                data = []
                # Write data
                for element in walker:
                    row = (tuplize_element(element) + get_size(element))
                    data.append(row)
            except:
                sys.stderr.write("Failed, trying again.\n")
            else:
                success = True
                counter = 0
                for row in data:
                    csv_writer.writerow(row)
                    counter += 1
                print " {n} photos grabbed".format(n=counter)
