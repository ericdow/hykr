from flask import Flask, request, render_template, jsonify, Response
import os, sys
import urllib.parse
from dotenv import load_dotenv
from elevation_data import *
from map_data import *

load_dotenv() # load variables stored in .env file 

app = Flask(__name__)

@app.route('/calculate_result')
def calculate_result():
    # grab the input parameters
    lat_start = float(request.args.get('lat_start'))
    long_start = float(request.args.get('long_start'))
    lat_end = float(request.args.get('lat_end'))
    long_end = float(request.args.get('long_end'))
    elev_source = request.args.get('elev_source')
    map_source = request.args.get('map_source')
    algo = request.args.get('algo')

    # get the elevation data
    nx = 100
    ny = 100
    buff_mult = 1.2
    if elev_source == 'open_topo_data':
        elev_server = OpenTopoData()
    elif elev_source == 'epqs':
        elev_server = EPQSData()
    elif elev_source == 'bing_maps':
        elev_server = BingElevData()
    lat_min, long_min, lat_max, long_max = \
            elev_server.get_square_bbox(lat_start, long_start, lat_end, 
                    long_end, buff_mult)
    lat_dist, long_dist = elev_server.get_lat_long_dist(lat_min, long_min, 
            lat_max, long_max)
    elev = elev_server.get_elevations(lat_min, long_min, lat_max, long_max,
            nx, ny)

    # get the image data
    if map_source == 'bing_maps':
        map_server = BingMapData()
    resolution = (0,0) # TODO
    sat_img_base_url = map_server.get_satellite_image_url(lat_min, long_min, 
            lat_max, long_max, resolution)
    bbox, yres, xres = map_server.get_image_metadata(lat_min, 
            long_min, lat_max, long_max, resolution)
    map_lat_dist, map_long_dist = elev_server.get_lat_long_dist(bbox[0], 
            bbox[1], bbox[2], bbox[3])
    tex_scale_x = long_dist / map_long_dist
    tex_scale_y = lat_dist / map_lat_dist
    lat_shift, long_shift = elev_server.get_lat_long_dist(bbox[0], bbox[1], 
            lat_min, long_min)
    tex_shift_x = lat_shift / map_lat_dist
    tex_shift_y = long_shift / map_long_dist

    # form the satellite image proxy url (used to hide API keys)
    sat_img_proxy_url = request.host_url + 'sat_img/' + map_source + \
            '/' + urllib.parse.quote(sat_img_base_url)

    # find the optimal path
    # TODO

    return jsonify({"elev":elev, "image_url":sat_img_proxy_url, "nx":nx, "ny":ny, 
        "lat_dist":lat_dist, "long_dist":long_dist, "tex_scale_x":tex_scale_x,
        "tex_scale_y":tex_scale_y, "tex_shift_x":tex_shift_x, 
        "tex_shift_y":tex_shift_y})

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/sat_img/<path:map_source_and_url>', methods=['GET'])
def sat_img_proxy(map_source_and_url):
    # split route into map_source and image url 
    [map_source, sat_img_base_url] = map_source_and_url.split('/',1)

    # determine which map server to use
    if (map_source == 'bing_maps'):
        map_server = BingMapData()
    sat_img_url = sat_img_base_url + map_server.get_api_key()
    if request.method=='GET':
        resp = requests.get(sat_img_url)
        response = Response(resp.content, resp.status_code)
    return response

if __name__ == "__main__":
    # TODO: remove debug
    app.run("127.0.0.1", port=5000, debug=True)
