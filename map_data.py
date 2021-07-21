import urllib.request, requests, json, base64

class MapData:
    '''Base class for map data objects, which are responsible for 
    retreiving map data'''
    def __init__(self):
        self.base_url = None

    def is_healthy(self):
        '''Check if the data server is healthy and return a bool'''
        raise NotImplementedError('You need to define is_healthy()!')
    
    def get_image_url(self, lat_min, long_min, lat_max, long_max, resolution):
        '''Get the url for the image of a specific area'''
        raise NotImplementedError('You need to define get_image_url()!')

class BingMapData(MapData):
    '''Map data from Bing Maps'''
    def __init__(self):
        self.base_url = 'http://dev.virtualearth.net/REST/v1/Imagery/Map/'
        with open('bing_maps_api_key', 'r') as file:
            self.api_key = file.read().strip()

    def get_image_url(self, lat_min, long_min, lat_max, long_max):
        imagerySet = 'Aerial'
        # get the image
        url = self.base_url + imagerySet + '?ma=' + str(lat_min) + ',' + \
                str(long_min) + ',' + str(lat_max) + ',' + str(long_max) + \
                '&fmt=jpeg&key=' + self.api_key
        image_url = url
        
        # get the image metadata
        url += '&mmd=1'
        contents = urllib.request.urlopen(url).read()
        contents = json.loads(contents)
        bbox = contents['resourceSets'][0]['resources'][0]['bbox']
        imageHeight = contents['resourceSets'][0]['resources'][0]['imageHeight']
        imageWidth = contents['resourceSets'][0]['resources'][0]['imageWidth']

        return (image_url, bbox, imageHeight, imageWidth)
