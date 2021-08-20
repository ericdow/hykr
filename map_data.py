import urllib.request, requests, json, os

class MapData:
    '''Base class for map data objects, which are responsible for 
    retreiving map data'''
    def __init__(self):
        self.base_url = None
        self.api_key = ''

    def is_healthy(self):
        '''Check if the data server is healthy and return a bool'''
        raise NotImplementedError('You need to define is_healthy()!')
    
    def get_satellite_image_url(self, lat_min, long_min, lat_max, long_max, 
            res):
        '''Get the url for the satellite image of an area, without API key'''
        raise NotImplementedError('You need to define get_satellite_image_url()!')

    def get_image_metadata(self, lat_min, long_min, lat_max, long_max, res):
        '''Get the image metadata for a specific map request'''
        raise NotImplementedError('You need to define get_image_metadata()!')
    
    def get_water_image_url(self, lat_min, long_min, lat_max, long_max, 
            res):
        '''Get the url for the water image of an area, without API key'''
        raise NotImplementedError('You need to define get_water_image_url()!')

    def get_water_rgb(self):
        '''Get the RGB tuple for the water color in a water image'''
        raise NotImplementedError('You need to define get_water_rgb()!')

    def get_api_key(self):
        '''Get the API key for this map service'''
        return self.api_key

class BingMapData(MapData):
    '''Map data from Bing Maps'''
    def __init__(self):
        self.base_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/'
        self.api_key = os.getenv('BING_MAPS_API_KEY')

    def get_satellite_image_url(self, lat_min, long_min, lat_max, long_max, 
            res):
        # get the url for the specified area
        imagerySet = 'Aerial'
        url = self.base_url + imagerySet + '?ma=' + str(lat_min) + ',' + \
                str(long_min) + ',' + str(lat_max) + ',' + str(long_max) + \
                '&ms=' + str(res[0]) + ',' + str(res[1]) + '&fmt=png&key='
        
        return url
    
    def get_image_metadata(self, lat_min, long_min, lat_max, long_max, 
            res):
        # get the image metadata
        url = self.get_satellite_image_url(lat_min, long_min, lat_max, long_max,
                res) + self.get_api_key();
        url += '&mmd=1'

        contents = urllib.request.urlopen(url).read()
        contents = json.loads(contents)
        
        bbox = contents['resourceSets'][0]['resources'][0]['bbox']
        imageHeight = contents['resourceSets'][0]['resources'][0]['imageHeight']
        imageWidth = contents['resourceSets'][0]['resources'][0]['imageWidth']

        return (bbox, imageHeight, imageWidth)
    
    def get_water_image_url(self, lat_min, long_min, lat_max, long_max, 
            res):
        # get the url for the specified area
        imagerySet = 'Road'
        url = self.base_url + imagerySet + '?ma=' + str(lat_min) + ',' + \
                str(long_min) + ',' + str(lat_max) + ',' + str(long_max) + \
                '&ms=' + str(res[0]) + ',' + str(res[1]) + '&fmt=png'

        # add a style string to make the water blue and remove all labels
        (r,g,b) = self.get_water_rgb()
        url += '&st=me|lv:0_ar|v:0_trs|v:0_ad|bv:0_wt|fc:' + \
                '{:02x}{:02x}{:02x}'.format(r, g, b) + '_pt|v:0'
        url += '&key='

        return url
    
    def get_water_rgb(self):
        return (0,0,255)

# class MapBoxData(MapData):
#     '''Map data from Bing Maps'''
#     def __init__(self):
#         self.base_url = 'https://api.mapbox.com/styles/v1/'
#         self.api_key = os.getenv('MAPBOX_API_KEY')
# 
#     def get_satellite_image_url(self, lat_min, long_min, lat_max, long_max):
#         # TODO
#         style = 'ericdow/ckrxxbtca153t17qqoykewj1y/'
#         url = self.base_url + 'static/[' + str(long_min) + ',' str(lat_min) + \
#                 ',' + str(long_max) + ',' + str(lat_max)
#         static/[-122.4364,37.6341,-122.3494,37.68]/300x200?access_token=
# 
#         return (image_url, bbox, imageHeight, imageWidth)
