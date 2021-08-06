import urllib.request, requests, json, time, math

# TODO: handle latitude limits, e.g. -85 to +85 degrees

class ElevationData:
    '''Base class for elevation data objects, which are responsible for 
    retreiving elevation data'''
    Re = 6.371e6 # Earth radius in meters
    
    def __init__(self):
        self.base_url = None

    def is_healthy(self):
        '''Check if the data server is healthy and return a bool'''
        raise NotImplementedError('You need to define is_healthy()!')

    def get_elevations(self, lat_min, long_min, lat_max, long_max, nx, ny):
        '''Get the elevation at a given latitudes and longitudes'''
        raise NotImplementedError('You need to define get_elevation()!')

    @staticmethod
    def clip_long(long):
        '''Utility function to clip longitudes to range -180 to +180'''
        if long > 180.0:
            return long - 360.0
        elif long < -180.0:
            return long + 360.0
        else:
            return long

    def get_lat_long_dist(self, lat_start, long_start, lat_end, long_end):
        lat_dist = math.fabs(lat_end - lat_start)*111045.0

        # always use smallest longitude range
        dlong = math.fabs(long_end - long_start)
        if dlong > 180.0:
            dlong = 360.0 - dlong
        lat_mid = 0.5*(lat_start + lat_end)
        r_at_lat = math.cos(math.radians(math.fabs(lat_mid)))*self.Re # radius at lat_mid
        long_dist = r_at_lat*math.radians(dlong)

        return (lat_dist, long_dist)
    
    def get_square_bbox(self, lat_start, long_start, lat_end, long_end, 
            buff_mult):
        '''Form a bounding box around start/end points with some buffer'''
        lat_dist, long_dist = self.get_lat_long_dist(lat_start, long_start,
                 lat_end, long_end)
        d = math.sqrt(lat_dist**2 + long_dist**2)
        
        lat_mid = 0.5*(lat_start + lat_end)
        lat_min = lat_mid - 0.5*buff_mult*d/self.Re*180.0/math.pi
        lat_max = lat_mid + 0.5*buff_mult*d/self.Re*180.0/math.pi

        # always use smallest longitude range
        dlong = math.fabs(long_end - long_start)
        long0 = min(long_start, long_end)
        long1 = max(long_start, long_end)
        if dlong > 180.0:
            dlong = 360.0 - dlong
            long0, long1 = long1, long0            
        long_mid = self.clip_long(long0 + 0.5*dlong) 
        
        r_at_lat = math.cos(math.radians(math.fabs(lat_mid)))*self.Re # radius at lat_mid
        long_min = self.clip_long(long_mid - 0.5*buff_mult*d/r_at_lat*180.0/math.pi)
        long_max = self.clip_long(long_mid + 0.5*buff_mult*d/r_at_lat*180.0/math.pi)

        return (lat_min, long_min, lat_max, long_max)

    def get_lat_long_grid(self, lat_min, long_min, lat_max, long_max, nx, ny):
        dlat = (lat_max - lat_min) / ny
        dlong = math.fabs(long_max - long_min)
        if dlong > 180.0:
            dlong = 360.0 - dlong
        dlong /= nx
        
        lat_long_list = []
        for j in range(ny):
            for i in range(nx):
                long = self.clip_long(long_min + i*dlong)
                lat = lat_max - j*dlat
                lat_long_list.append((lat,long))

        return lat_long_list

class OpenTopoData(ElevationData):
    '''Elevation data from opentopodata.org'''
    def __init__(self):
        self.base_url = 'https://api.opentopodata.org/'

    def is_healthy(self):
        contents = urllib.request.urlopen(self.base_url+'health').read()
        contents = json.loads(contents)
        return contents['status'] == 'OK'
    
    def get_elevations(self, lat_min, long_min, lat_max, long_max, nx, ny):
        lat_long_list = self.get_lat_long_grid(lat_min, long_min, lat_max,
                long_max, nx, ny)
        # public API: 1000 calls/day, 100 locations/call, 1 call/sec
        # build the request by joining the locations
        elevations = []
        dataset = 'aster30m'
        url = self.base_url + '/v1/' + dataset + '?locations='
        for i,lat_long in enumerate(lat_long_list):
            url += str(lat_long[0]) + ',' + str(lat_long[1])
            url += '|'
           
            # make request if we've reached 100 locations
            if ((i+1) % 100 == 0) or (i == len(lat_long_list)-1):
                url = url[:-1]
                # request the data
                contents = urllib.request.urlopen(url).read()
                contents = json.loads(contents)

                # extract a list of elevations
                for result in contents['results']:
                    elevations.append(result['elevation'])
        
                url = self.base_url + '/v1/' + dataset + '?locations='

        return elevations

class EPQSData(ElevationData):
    '''Elevation data from nationalmap.gov/epqs'''
    def __init__(self):
        self.base_url = 'https://nationalmap.gov/epqs/'

    def get_elevations(self, lat_min, long_min, lat_max, long_max, nx, ny):
        lat_long_list = self.get_lat_long_grid(lat_min, long_min, lat_max,
                long_max, nx, ny)
        elevations = []
        for lat_long in lat_long_list:
            url = self.base_url + 'pqs.php?'
            url += 'x=' + str(lat_long[0]) + '&y=' + str(lat_long[1])
            url += '&output=json&units=Meters'
        
            # request the data
            contents = urllib.request.urlopen(url).read()
            contents = json.loads(contents)

            # extract a list of elevations
            elevations.append(float(contents 
                ['USGS_Elevation_Point_Query_Service']
                ['Elevation_Query']['Elevation']))

        return elevations

class BingElevData(ElevationData):
    '''Elevation data from Bing Maps'''
    def __init__(self):
        self.base_url = 'http://dev.virtualearth.net/REST/v1/Elevation/'
        with open('bing_maps_api_key', 'r') as file:
            self.api_key = file.read().strip()

    def get_elevations(self, lat_min, long_min, lat_max, long_max, nx, ny):
        lat_long_list = self.get_lat_long_grid(lat_min, long_min, lat_max,
                long_max, nx, ny)
        body = 'points='
        for lat_long in lat_long_list:
            body += str(lat_long[0]) + ',' + str(lat_long[1]) + ','
        body = body[:-1]

        # use POST to get large numbers of elevations
        url = self.base_url + 'List?key=' + self.api_key
        headers = {'Content-Length': str(len(body)), 
                'Content-Type': 'text/plain; charset=utf-8'}
        r = requests.post(url, data=body, headers=headers)
        contents = json.loads(r.content)
        
        return contents['resourceSets'][0]['resources'][0]['elevations']

if __name__ == "__main__":
    # TODO
    bmd = BingElevData()
    lat_dist, long_dist, lat_min, long_min, lat_max, long_max = \
        bmd.get_lat_long_dist(50, -175, 50, 175, 1.2)
    print(long_min, long_max)
    lat_dist, long_dist, lat_min, long_min, lat_max, long_max = \
        bmd.get_lat_long_dist(50, -5, 50, 5, 1.2)
    print(long_min, long_max)
    lat_dist, long_dist, lat_min, long_min, lat_max, long_max = \
        bmd.get_lat_long_dist(50, 155, 50, -85, 1.2)
    print(long_min, long_max)
    # print(bmd.get_elevations(50, 50, 60, 60, 32, 32, 1.2))

    '''
    otd = OpenTopoData()
    print(otd.is_healthy())
    print(otd.get_elevations([(-43.5,172.5), (27.6,1.98)]))

    epqs = EPQSData()
    print(epqs.get_elevations([(36.1,-115.3)]))
    '''
