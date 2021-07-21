from flask import Flask, request, render_template, jsonify
import os, sys
from elevation_data import *
from map_data import *

app = Flask(__name__)

@app.route('/calculate_result')
def calculate_result():
    # grab the input parameters
    lat_start = float(request.args.get('lat_start'))
    long_start = float(request.args.get('long_start'))
    lat_end = float(request.args.get('lat_end'))
    long_end = float(request.args.get('long_end'))
    elev_source = request.args.get('elev_source')
    algo = request.args.get('algo')

    # get the elevation data
    nx = 100
    ny = 100
    d_mult = 1.2
    if elev_source == 'open_topo_data':
        elev_server = OpenTopoData()
    elif elev_source == 'epqs':
        elev_server = EPQSData()
    elif elev_source == 'bing_maps':
        elev_server = BingElevData()
    elev = elev_server.get_elevations(lat_start, long_start, lat_end, long_end, 
            nx, ny, d_mult)
    lat_dist, long_dist, lat_min, long_min, lat_max, long_max = \
            elev_server.get_lat_long_dist(lat_start, long_start, lat_end, 
                    long_end, d_mult)

    # get the image data
    map_server = BingMapData()
    image_url, bbox, yres, xres = map_server.get_image_url(lat_min, long_min, 
            lat_max, long_max)

    return jsonify({"elev":elev, "image_url":image_url, "nx":nx, "ny":ny, 
        "lat_dist":lat_dist, "long_dist":long_dist})

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # TODO: remove debug
    app.run("127.0.0.1", port=5000, debug=True)
