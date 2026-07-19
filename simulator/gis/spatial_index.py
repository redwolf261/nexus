from typing import List, Tuple, Any, Callable
import math

class SpatialGrid:
    """
    A simple grid-based spatial index to avoid O(N*M) distance calculations.
    Splits the map into a grid of roughly fixed size (e.g. 10km x 10km).
    """
    def __init__(self, cell_size_deg: float = 0.1):
        self.cell_size = cell_size_deg
        self.grid = {}

    def _get_cell(self, lat: float, lng: float) -> Tuple[int, int]:
        return (int(lat / self.cell_size), int(lng / self.cell_size))

    def insert(self, lat: float, lng: float, item: Any):
        cell = self._get_cell(lat, lng)
        if cell not in self.grid:
            self.grid[cell] = []
        self.grid[cell].append((lat, lng, item))

    def get_nearest(self, lat: float, lng: float, max_radius_deg: float = 0.5) -> Any:
        """Find the nearest item within the search radius."""
        center_cell = self._get_cell(lat, lng)
        search_range = int(math.ceil(max_radius_deg / self.cell_size))
        
        nearest_item = None
        min_dist = float('inf')

        # Check the center cell and neighboring cells
        for dlat in range(-search_range, search_range + 1):
            for dlng in range(-search_range, search_range + 1):
                cell = (center_cell[0] + dlat, center_cell[1] + dlng)
                if cell in self.grid:
                    for item_lat, item_lng, item in self.grid[cell]:
                        dist = (lat - item_lat)**2 + (lng - item_lng)**2
                        if dist < min_dist:
                            min_dist = dist
                            nearest_item = item
                            
        return nearest_item

class GISPrecomputation:
    """
    Precomputes nearest POIs and Stations for fast access during generation.
    """
    def __init__(self):
        self.stations = SpatialGrid()
        self.hospitals = SpatialGrid()
        self.atms = SpatialGrid()
        self.police_stations = SpatialGrid()
        
    def load_stations(self, stations_list):
        for s in stations_list:
            self.stations.insert(s.latitude, s.longitude, s)
            self.police_stations.insert(s.latitude, s.longitude, s)
            
    def load_pois(self, pois_list):
        for p in pois_list:
            if p.poi_type == "Hospital":
                self.hospitals.insert(p.latitude, p.longitude, p)
            elif p.poi_type == "ATM" or p.poi_type == "Bank":
                self.atms.insert(p.latitude, p.longitude, p)
                
    def get_nearest_station(self, lat, lng):
        return self.stations.get_nearest(lat, lng)
        
    def get_nearest_hospital(self, lat, lng):
        return self.hospitals.get_nearest(lat, lng)
