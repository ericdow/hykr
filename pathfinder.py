from PIL import Image
from io import BytesIO
import math, requests
import numpy as np
from scipy import interpolate
from enum import IntEnum
from map_data import *
from priority_queue import *

class PathFinderResult(IntEnum):
    '''Enum for result of pathfinding'''
    OK = 1
    INVALID_START = 2
    INVALID_END = 3
    NO_VALID_PATH = 4

class NodeTimePair():
    """Wraps a node and its corresponding travel time in the priority queue"""
    
    def __init__(self, node, time):
        """Creates a NodeTimePair to be used as a key in the priority queue"""
        self.node = node
        self.time = time
        
    def __lt__(self, other):
        # :nodoc: Delegate comparison to time.
        return (self.time < other.time or 
                (self.time == other.time and 
                 id(self.node) < id(other.node)))
    
    def __le__(self, other):
        # :nodoc: Delegate comparison to time.
        return (self.time < other.time or
                (self.time == other.time and 
                 id(self.node) <= id(other.node)))
                
    def __gt__(self, other):
        # :nodoc: Delegate comparison to time.
        return (self.time > other.time or
                (self.time == other.time and 
                 id(self.node) > id(other.node)))
    
    def __ge__(self, other):
        # :nodoc: Delegate comparison to time.
        return (self.time > other.time or
                (self.time == other.time and 
                 id(self.node) >= id(other.node)))

class PathFinder:
    '''Base class for path finding objects'''
    def __init__(self):
        pass

    def get_optimal_path(self, lat_start, long_start, lat_end, long_end, 
            lat_long_bbox, lat_dist, long_dist, nx, ny, elev2d, 
            map_server : MapData):
        '''Determine the optimal path between two points'''
        raise NotImplementedError('You need to define get_optimal_path!')

    @staticmethod
    def walking_time(h_from, h_to, dx):
        '''Compute the time (in seconds) to walk between two points using Tobler's 
        hiking function
        https://en.wikipedia.org/wiki/Tobler%27s_hiking_function
        '''
        if np.isinf(h_from) or np.isinf(h_to):
            return np.inf
        dh_dx = (float(h_from) - float(h_to)) / dx
        speed = 6.0 * math.exp(-3.5 * math.fabs(dh_dx + 0.05)) / 3.6
        if speed == 0.0:
            return np.inf
        else:
            return dx / speed

    def get_land_grid(self, lat_long_bbox, nx, ny, map_server : MapData):
        '''Determine which grid points are on land and which are under water''' 
        # get the image used to determine the locations of water
        res = (5*nx,5*ny) 
        url = map_server.get_water_image_url(lat_long_bbox, res) + \
                map_server.get_api_key()
        img = Image.open(requests.get(url, stream=True).raw).convert('RGB')
        bbox, yres, xres = map_server.get_image_metadata(lat_long_bbox, res)

        # determine which pixels are covered by water
        img_rgb = np.array(img)
        water_rgb = map_server.get_water_rgb()
        rgb_tol = 25000 # average difference of ~90 in each channel
        land_pixels = np.sum((img_rgb - water_rgb)**2, axis=2) > rgb_tol
        land_pixels = np.transpose(land_pixels)

        # determine which graph nodes are covered by water
        lat_min, long_min, lat_max, long_max = lat_long_bbox
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

    def compute_neighbor_times(self, is_land, elev, lat_dist, long_dist):
        '''Compute the travel time between each grid point and its 8 neighbors''' 
        nx = is_land.shape[0]
        ny = is_land.shape[1]

        # interpolate elevations on movement grid
        nx_elev = elev.shape[0]
        ny_elev = elev.shape[1]
        x = np.linspace(0,1,nx_elev)
        y = np.linspace(0,1,ny_elev)
        interp = interpolate.RectBivariateSpline(x, y, elev)
        elev_interp = interp(np.linspace(0,1,nx), np.linspace(0,1,ny))

        # set height in water grid points to infinity
        elev_interp = np.where(is_land, elev_interp, np.inf)

        # ordering is (N, NE, E, SE, S, SW, W, NW)
        #              0  1   2  3   4  5   6  7
        neighbor_times = np.full((nx,ny,8), np.inf)
        dx = long_dist / nx
        dy = lat_dist / ny
        dxy = math.sqrt(dx**2 + dy**2)
        # N
        neighbor_times[:,:-1,0] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i,j+1], dy) for j in range(0,ny-1)] for i in range(0,nx)])
        # NE
        neighbor_times[:-1,:-1,1] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i+1,j+1], dxy) for j in range(0,ny-1)] for i in range(0,nx-1)])
        # E
        neighbor_times[:-1,:,2] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i+1,j], dx) for j in range(0,ny)] for i in range(0,nx-1)])
        # SE
        neighbor_times[:-1,1:,3] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i+1,j-1], dxy) for j in range(1,ny)] for i in range(0,nx-1)])
        # S
        neighbor_times[:,1:,4] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i,j-1], dy) for j in range(1,ny)] for i in range(0,nx)])
        # SW
        neighbor_times[1:,1:,5] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i-1,j-1], dxy) for j in range(1,ny)] for i in range(1,nx)])
        # W
        neighbor_times[1:,:,6] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i-1,j], dx) for j in range(0,ny)] for i in range(1,nx)])
        # NW
        neighbor_times[1:,:-1,7] = np.array([[self.walking_time(elev_interp[i,j], 
            elev_interp[i-1,j+1], dxy) for j in range(0,ny-1)] for i in range(1,nx)])

        return neighbor_times

    def check_start_end_validity(self, lat_start, long_start, lat_end, long_end, 
            lat_long_bbox, is_land):
        '''Check if start and end points are valid, i.e. not in water'''
        lat_min, long_min, lat_max, long_max = lat_long_bbox
        nx = is_land.shape[0]
        ny = is_land.shape[1]
        si = int(round(nx * (long_start-long_min) / (long_max-long_min)))
        sj = ny - int(round(ny * (lat_start-lat_min) / (lat_max-lat_min))) - 1
        ei = int(round(nx * (long_end-long_min) / (long_max-long_min)))
        ej = ny - int(round(ny * (lat_end-lat_min) / (lat_max-lat_min))) - 1

        if not is_land[si,sj]:
            return si, sj, ei, ej, PathFinderResult.INVALID_START
        if not is_land[ei,ej]:
            return si, sj, ei, ej, PathFinderResult.INVALID_END
        else:
            return si, sj, ei, ej, PathFinderResult.OK

class Dijkstra(PathFinder):
    
    def get_optimal_path(self, lat_start, long_start, lat_end, long_end, 
            lat_long_bbox, lat_dist, long_dist, nx, ny, elev2d, 
            map_server : MapData):
        # find the valid grid points and compute the time between neighbors
        is_land = self.get_land_grid(lat_long_bbox, nx, ny, map_server)
        neighbor_times = self.compute_neighbor_times(is_land, elev2d, 
                lat_dist, long_dist)
       
        # check if start/end points are valid
        si, sj, ei, ej, valid = self.check_start_end_validity(lat_start, 
                long_start, lat_end, long_end, lat_long_bbox, is_land)
        if (valid == PathFinderResult.INVALID_START or 
                valid == PathFinderResult.INVALID_END):
            return valid, []

        # initialize the parents, keys, etc.
        pq = PriorityQueue()
        parents = np.empty((nx,ny), dtype=object) # initialized to None
        queue_keys = np.empty((nx,ny), dtype=object) # initialized to None

        # insert the start point into the priority queue
        queue_keys[si,sj] = NodeTimePair(np.array([si,sj]), 0.0)
        pq.insert(queue_keys[si,sj])

        delta_ij = np.array([[0,1], [1,1], [1,0], [1,-1], [0,-1], [-1,-1], [-1,0], [-1,1]])
        num_visited = 0
        found_end = False
        while len(pq) > 0:
            node_key = pq.extract_min()
            node, time = node_key.node, node_key.time
            i,j = node[0],node[1]
            num_visited = num_visited + 1
           
            # stop searching if you find the ending node 
            if (i,j) == (ei,ej):
                found_end = True
                break
            
            # relax nodes adjacent to this node
            for n in range(8):
                # skip nodes that aren't reachable
                if np.isinf(neighbor_times[i,j,n]):
                    continue
                neigh_ij = node + delta_ij[n]
                ni,nj = neigh_ij[0],neigh_ij[1]
                neigh_time = neighbor_times[i,j,n] + time
                if queue_keys[ni, nj] is None:
                    queue_keys[ni,nj] = NodeTimePair(np.array([ni,nj]), 
                        neigh_time)
                    pq.insert(queue_keys[ni,nj])
                    parents[ni,nj] = np.array([i,j])
                elif neigh_time < queue_keys[ni,nj].time:
                    queue_keys[ni,nj].time = neigh_time
                    pq.decrease_key(queue_keys[ni,nj])
                    parents[ni,nj] = np.array([i,j])
        
        # check if we reached the end node
        if not found_end:
            return PathFinderResult.NO_VALID_PATH, []

        # follow the parent pointers back to build the path
        path = [int(ej),int(ei)]
        i,j = ei,ej
        while (i,j) != (si,sj):
            parent = parents[i,j]
            i,j = parent[0], parent[1]
            path.append(int(j))
            path.append(int(i))
        path.reverse()
        return PathFinderResult.OK, path

class BidirectionalDijkstra(PathFinder):
    
    def get_optimal_path(self, lat_start, long_start, lat_end, long_end, 
            lat_long_bbox, lat_dist, long_dist, nx, ny, elev2d, 
            map_server : MapData):
        # find the valid grid points and compute the time between neighbors
        is_land = self.get_land_grid(lat_long_bbox, nx, ny, map_server)
        neighbor_times = self.compute_neighbor_times(is_land, elev2d, 
                lat_dist, long_dist)
       
        # check if start/end points are valid
        valid = self.check_start_end_validity(lat_start, long_start, lat_end, 
            long_end, lat_long_bbox, is_land)
        if (valid == PathFinderResult.INVALID_START or 
                valid == PathFinderResult.INVALID_END):
            return valid, []
        
        '''Perform Dijkstra from start and end points
        Choose direction with fewer frontier nodes for expansion'''
        fwd_frontier = PriorityQueue()
        rev_frontier = PriorityQueue()

        # initialize the parents, keys, etc. in both forward and reverse directions
        parents = np.empty((nx,ny,2), dtype=object) # initialized to None
        queue_keys = np.empty((nx,ny,2), dtype=object) # initialized to None
        finalized = np.zeros((nx,ny,2), dtype=bool) # initialized to False

        # insert the start and end points into the priority queues
        queue_keys[si,sj,0] = NodeTimePair(np.array([si,sj]), 0.0)
        fwd_frontier.insert(queue_keys[si,sj,0])
        queue_keys[ei,ej,1] = NodeTimePair(np.array([ei,ej]), 0.0)
        rev_frontier.insert(queue_keys[ei,ej,1])

        '''
        for node in nodes:
            node.parent = None
            node.queue_key = None
            
        num_visited = 0
    
        # Run Dijkstra's algorithm.
        pq = PriorityQueue()
        # Use NodeTimePair as a key in the priority queue.
        source.queue_key = NodeTimePair(source, 0)
        pq.insert(source.queue_key)
        
        while len(pq) > 0:
            node_key = pq.extract_min()
            node, dist = node_key.node, node_key.distance
            num_visited = num_visited + 1
            if node is destination: break
            for next_node in node.adj: # Relax nodes adjacent to node.
                next_dist = weight(node, next_node) + dist
                if next_node.queue_key is None:
                    next_node.queue_key = NodeTimePair(next_node, next_dist)
                    pq.insert(next_node.queue_key)
                    next_node.parent = node
                elif next_dist < next_node.queue_key.distance:
                    next_node.queue_key.distance = next_dist
                    pq.decrease_key(next_node.queue_key)
                    next_node.parent = node
        
      FFinalized:
      FReachable: fwd_frontier
      FCost = min_times[0]

      node(G) fnext = FReachable.getMinKey();
      FReachable.remove(fnext);
      fnext.FFinalized = true;
      curMinFCost = fnext.FCost;
      if (curMinFCost + curMinRCost + minUnitCost >= minCost) {
        terminate = true;
      }

      double fdist = fnext.FCost;
      for(v: fnext.nbrs) (!v.FFinalized) {
        edge e = v.edge();
        if (fdist + e.Weight + curMinRCost <= minCost) {
          if (v.FCost > fdist + e.Weight) {
            v.FCost = fdist + e.Weight;
            FReachable[v] = v.FCost;
            v.Parent = fnext;
            v.ParentEdge = e;
            if (v.RCost != +INF) {
              double newCost = v.FCost + v.RCost;
              <minCost; mid> min= <newCost; v>;
            }
          }
        }
      }

        '''

        terminate = False
        min_times = [np.inf,np.inf]
        min_total_time = np.inf
        # ordering is (N, NE, E, SE, S, SW, W, NW)
        delta_ij = np.array([[0,1], [1,1], [1,0], [1,-1], [0,-1], [-1,-1], [-1,0], [-1,1]])
        while (not terminate) and len(fwd_frontier) > 0 and len(rev_frontier) > 0:
            # choose search direction 
            if len(fwd_frontier) < len(rev_frontier):
                frontier = fwd_frontier
                search_dir = 0
            else:
                frontier = rev_frontier
                search_dir = 1

            node_and_key = frontier.extract_min()
            node, time = node_and_key.node, node_and_key.time
            min_times[search_dir] = time

            # check if any nodes have been found by both searches
            if min_times[0] + min_times[1] >= min_total_time:
                terminate = True

            # relax nodes adjacent to this node
            for n in range(8):
                # skip nodes that aren't reachable
                if np.isinf(neighbor_times[node[0], node[1], n]):
                    continue

                # skip nodes that have been finalized
                # TODO

                i,j = node[0],node[1]
                neigh_ij = node + delta_ij[n] 
                neigh_time = neighbor_times[i,j,n]




