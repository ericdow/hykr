from flask import Flask, request, render_template, jsonify
import os, sys, math
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

    # form a bounding box of points to evaluate the elevations at
    nx = 30
    ny = 30
    lat_mid = 0.5*(lat_start + lat_end)
    lat_dist = math.fabs(lat_end - lat_start)*111045.0
    long_mid = 0.5*(long_start + long_end)
    Re = 6.371e6 # Earth radius in meters
    r_at_lat = math.cos(math.radians(math.fabs(lat_mid)))*Re # radius at lat_mid
    long_dist = r_at_lat*math.radians(math.fabs(long_end-long_start))
    
    d = math.sqrt(lat_dist**2 + long_dist**2)
    mult = 1.2 # multiplier for expanding bounding box
    
    lat_min = lat_mid - 0.5*mult*d/Re*180.0/math.pi
    lat_max = lat_mid + 0.5*mult*d/Re*180.0/math.pi
    dlat = (lat_max - lat_min) / ny
    lat_dist = math.fabs(lat_max - lat_min)*111045.0
    
    long_min = long_mid - 0.5*mult*d/r_at_lat*180.0/math.pi
    long_max = long_mid + 0.5*mult*d/r_at_lat*180.0/math.pi
    dlong = (long_max - long_min) / nx
    long_dist = r_at_lat*math.radians(math.fabs(long_max-long_min))
    
    lat_long_to_eval = []
    for i in range(nx):
        long = long_min + i*dlong
        for j in range(ny):
            lat = lat_min + j*dlat
            lat_long_to_eval.append((lat,long))

    # compute the elevation data
    if elev_source == 'open_topo_data':
        elev_server = OpenTopoData()
    elif elev_source == 'epqs':
        elev_server = EPQSData()
    elev = elev_server.get_elevations(lat_long_to_eval)

    return jsonify({"elev":elev, "nx":nx, "ny":ny, "lat_dist":lat_dist, 
        "long_dist":long_dist})

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # TODO: remove debug
    app.run("127.0.0.1", port=5000, debug=True)
