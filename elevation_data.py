import urllib.request, requests, json, time, math

class ElevationData:
    '''Base class for elevation data objects, which are responsible for 
    retreiving elevation data'''
    def __init__(self):
        self.base_url = None

    def is_healthy(self):
        '''Check if the data server is healthy and return a bool'''
        raise NotImplementedError('You need to define is_healthy()!')

    def get_elevations(self, lat_start, long_start, lat_end, long_end, nx, ny, 
            d_mult):
        '''Get the elevation at a given latitudes and longitudes'''
        raise NotImplementedError('You need to define get_elevation()!')

    def get_lat_long_dist(self, lat_start, long_start, lat_end, long_end, nx, 
            ny, d_mult):
        # form a bounding box of points to evaluate the elevations at
        lat_mid = 0.5*(lat_start + lat_end)
        lat_dist = math.fabs(lat_end - lat_start)*111045.0
        long_mid = 0.5*(long_start + long_end)
        Re = 6.371e6 # Earth radius in meters
        r_at_lat = math.cos(math.radians(math.fabs(lat_mid)))*Re # radius at lat_mid
        long_dist = r_at_lat*math.radians(math.fabs(long_end-long_start))
        
        d = math.sqrt(lat_dist**2 + long_dist**2)
        lat_min = lat_mid - 0.5*d_mult*d/Re*180.0/math.pi
        lat_max = lat_mid + 0.5*d_mult*d/Re*180.0/math.pi
        dlat = (lat_max - lat_min) / ny
        lat_dist = math.fabs(lat_max - lat_min)*111045.0
        
        long_min = long_mid - 0.5*d_mult*d/r_at_lat*180.0/math.pi
        long_max = long_mid + 0.5*d_mult*d/r_at_lat*180.0/math.pi
        dlong = (long_max - long_min) / nx
        long_dist = r_at_lat*math.radians(math.fabs(long_max-long_min))

        return (lat_dist, long_dist, lat_min, long_min, lat_max, long_max)

    def get_lat_long_grid(self, lat_start, long_start, lat_end, long_end, nx, 
            ny, d_mult):
        lat_min, long_min, lat_max, long_max = self.get_lat_long_dist(lat_start, 
                long_start, lat_end, long_end, nx, ny, d_mult)[2:]
        
        dlat = (lat_max - lat_min) / ny
        dlong = (long_max - long_min) / nx
        
        lat_long_list = []
        for i in range(nx):
            long = long_min + i*dlong
            for j in range(ny):
                lat = lat_min + j*dlat
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
    
    def get_elevations(self, lat_start, long_start, lat_end, long_end, nx, ny, 
            d_mult):
        lat_long_list = self.get_lat_long_grid(lat_start, long_start, lat_end,
                long_end, nx, ny, d_mult)
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

    def get_elevations(self, lat_start, long_start, lat_end, long_end, nx, ny, 
            d_mult):
        lat_long_list = self.get_lat_long_grid(lat_start, long_start, lat_end,
                long_end, nx, ny, d_mult)
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

class BingMapData(ElevationData):
    '''Elevation data from Bing Maps'''
    def __init__(self):
        self.base_url = 'http://dev.virtualearth.net/REST/v1/Elevation/'
        with open('bing_maps_api_key', 'r') as file:
            self.api_key = file.read()

    def get_elevations(self, lat_start, long_start, lat_end, long_end, nx, ny, 
            d_mult):
        # build a list of points to query
        lat_long_list = self.get_lat_long_grid(lat_start, long_start, lat_end,
                long_end, nx, ny, d_mult)
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
    bmd = BingMapData()
    print(bmd.get_elevations(50, 50, 60, 60, 32, 32, 1.2))

    '''
    otd = OpenTopoData()
    print(otd.is_healthy())
    print(otd.get_elevations([(-43.5,172.5), (27.6,1.98)]))

    epqs = EPQSData()
    print(epqs.get_elevations([(36.1,-115.3)]))
    '''
