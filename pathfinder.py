import math

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
        dh_dx = (float(h_from) - float(h_to)) / dx;
        speed = 6.0 * exp(-3.5 * math.fabs(dh_dx + 0.05)) / 3.6
        return dx / speed;
        

