from flask import Flask, request, render_template, jsonify
import os, sys
from elevation_data import *

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

    # compute the elevation data
    nx = 32
    ny = 32
    d_mult = 1.2
    if elev_source == 'open_topo_data':
        elev_server = OpenTopoData()
    elif elev_source == 'epqs':
        elev_server = EPQSData()
    elif elev_source == 'bing_maps':
        elev_server = BingMapData()
    elev = elev_server.get_elevations(lat_start, long_start, lat_end, long_end, 
            nx, ny, d_mult)

    return jsonify({"elev":elev, "nx":nx, "ny":ny, "lat_dist":lat_dist, 
        "long_dist":long_dist})

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # TODO: remove debug
    app.run("127.0.0.1", port=5000, debug=True)
