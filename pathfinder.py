from PIL import Image
import math, requests
import numpy as np
from map_data import *

class PathFinder:
    '''Base class for path finding objects'''
    def __init__(self):
        pass

    @staticmethod
    def get_walking_time(h_from, h_to, dx):
        '''Compute the time (in seconds) to walk between two points using Tobler's 
        hiking function
        https://en.wikipedia.org/wiki/Tobler%27s_hiking_function
        '''
        dh_dx = (float(h_from) - float(h_to)) / dx
        speed = 6.0 * exp(-3.5 * math.fabs(dh_dx + 0.05)) / 3.6
        return dx / speed

    def create_movement_grid(self, lat_min, long_min, lat_max, long_max, nx, ny,
            map_server : MapData):
        '''Create an nx x ny grid of nodes that a hiker can move between, and 
        determine which nodes are reachable'''
        # get the image used to determine the locations of water
        res = (1000,1000) # TODO choose based on nx/ny 
        url = map_server.get_water_image_url(lat_min, long_min, lat_max, 
                long_max, res) + map_server.get_api_key()
        img = Image.open(requests.get(url, stream=True).raw)
        bbox, yres, xres = map_server.get_image_metadata(lat_min, long_min,
                lat_max, long_max, res)

        # determine which pixels are covered by water
        img_rgb = np.asarray(img, dtype='int32')
        water_rgb = map_server.get_water_rgb()
        rgb_tol = 25000; # average difference of ~90 in each channel
        land_pixels = np.sum((img_rgb - water_rgb)**2, axis=2) < rgb_tol

        # determine which graph nodes are covered by water
        dlong = long_max - long_min
        dlat = lat_max - lat_min
        dlong_img = bbox[3] - bbox[1]
        dlat_img = bbox[2] - bbox[0]
        shift_x = int(res[0]*(long_min - bbox[1])/dlong_img)
        shift_y = int(res[1]*(lat_min - bbox[0])/dlat_img)
        width_x = int(res[0]*dlong/dlong_img/nx)
        width_y = int(res[1]*dlat/dlat_img/ny)
        start_x = shift_x + width_x//2
        end_x = start_x + nx*width_x
        start_y = shift_y + width_y//2
        end_y = start_y + ny*width_y
        is_land = land_pixels[start_x:end_x:width_x,start_y:end_y:width_y]

        return is_land

