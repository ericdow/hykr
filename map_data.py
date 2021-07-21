import urllib.request, requests, json

class MapData:
    '''Base class for map data objects, which are responsible for 
    retreiving map data'''
    def __init__(self):
        self.base_url = None

    def is_healthy(self):
        '''Check if the data server is healthy and return a bool'''
        raise NotImplementedError('You need to define is_healthy()!')
    
    def get_image(self, lat_min, long_min, lat_max, long_max, resolution):
        '''Get an image of a specific area'''
        raise NotImplementedError('You need to define get_image()!')

class BingMapData(MapData):
    '''Map data from Bing Maps'''
    def __init__(self):
        self.base_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/'
        with open('bing_maps_api_key', 'r') as file:
            self.api_key = file.read()

    def get_image(self, lat_min, long_min, lat_max, long_max, resolution):
        imagerySet = 'Aerial'
        url = self.base_url + imagerySet + '?mapArea=' + str(lat_min) + ',' + \
                str(long_min) + ',' + str(lat_max) + ',' + str(long_max) + \
                '&format=jpeg&mapSize=' + str(resolution) + ',' + \
                str(resolution) + '&key=' + self.api_key
        print(url)
