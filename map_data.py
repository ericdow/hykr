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
            resolution):
        '''Get the url for the image of a specific area, without API key'''
        raise NotImplementedError('You need to define get_satellite_image_url()!')

    def get_image_metadata(self, lat_min, long_min, lat_max, long_max, 
            resolution):
        '''Get the image metadata for a specific map request'''
        raise NotImplementedError('You need to define get_image_metadata()!')

    def get_api_key(self):
        '''Get the API key for this map service'''
        return self.api_key

class BingMapData(MapData):
    '''Map data from Bing Maps'''
    def __init__(self):
        self.base_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/'
        self.api_key = os.getenv('BING_MAPS_API_KEY')

    def get_satellite_image_url(self, lat_min, long_min, lat_max, long_max, 
            resolution):
        # get the url for the specified area
        imagerySet = 'Aerial'
        url = self.base_url + imagerySet + '?ma=' + str(lat_min) + ',' + \
                str(long_min) + ',' + str(lat_max) + ',' + str(long_max) + \
                '&fmt=png&key='
        
        return url
    
    def get_image_metadata(self, lat_min, long_min, lat_max, long_max, 
            resolution):
        # get the image metadata
        url = self.get_satellite_image_url(lat_min, long_min, lat_max, long_max,
                resolution) + self.get_api_key();
        url += '&mmd=1'

        contents = urllib.request.urlopen(url).read()
        contents = json.loads(contents)
        
        bbox = contents['resourceSets'][0]['resources'][0]['bbox']
        imageHeight = contents['resourceSets'][0]['resources'][0]['imageHeight']
        imageWidth = contents['resourceSets'][0]['resources'][0]['imageWidth']

        return (bbox, imageHeight, imageWidth)
    
    def get_water_image_url(self, lat_min, long_min, lat_max, long_max, 
            resolution):
        # get the url for the specified area
        imagerySet = 'Road'
        url = self.base_url + imagerySet + '?ma=' + str(lat_min) + ',' + \
                str(long_min) + ',' + str(lat_max) + ',' + str(long_max) + \
                '&fmt=png'

        # add a style string to make the water blue and remove all labels
        url += '&st=me|lv:0_ar|v:0_trs|v:0_ad|bv:0_wt|fc:0000ff_pt|v:0'
        url += '&key='

        return url

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
