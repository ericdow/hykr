from PIL import Image
from io import BytesIO
import math, requests
import numpy as np
from map_data import *

class PathFinder:
    '''Base class for path finding objects'''
    def __init__(self):
        pass

    def get_optimal_path(self):
        '''Determine the optimal path between two points'''
        raise NotImplementedError('You need to define get_optimal_path!')

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
        res = (5*nx,5*ny) 
        url = map_server.get_water_image_url(lat_min, long_min, lat_max, 
                long_max, res) + map_server.get_api_key()
        img = Image.open(requests.get(url, stream=True).raw).convert('RGB')
        bbox, yres, xres = map_server.get_image_metadata(lat_min, long_min,
                lat_max, long_max, res)

        # determine which pixels are covered by water
        img_rgb = np.array(img)
        water_rgb = map_server.get_water_rgb()
        rgb_tol = 25000 # average difference of ~90 in each channel
        land_pixels = np.sum((img_rgb - water_rgb)**2, axis=2) < rgb_tol

        # determine which graph nodes are covered by water
        dlong = long_max - long_min
        dlat = lat_max - lat_min
        dlong_img = bbox[3] - bbox[1]
        dlat_img = bbox[2] - bbox[0]
        shift_x = int(xres*(long_min - bbox[1])/dlong_img)
        shift_y = int(yres*(lat_min - bbox[0])/dlat_img)
        width_x = xres*dlong/dlong_img/nx
        width_y = yres*dlat/dlat_img/ny
        start_x = int(shift_x + width_x/2)
        start_y = int(shift_y + width_y/2)
        ix = np.zeros(nx, dtype='int32')
        for i in range(nx):
            ix[i] = start_x + int(width_x*i)
        iy = np.zeros(ny, dtype='int32')
        for j in range(ny):
            iy[j] = start_y + int(width_y*j)
        is_land = land_pixels[np.ix_(ix,iy)]
        # Image.fromarray(is_land).save("land.png")

        return is_land

# class Dijkstra(Pathfinder):


