import networkx as nx
import numpy as np
from typing import List, Tuple, Dict
from simulator.gis.roads import RoadNetworkManager

class Router:
    def __init__(self, road_manager: RoadNetworkManager):
        self.road_manager = road_manager
        
    def _find_nearest_node(self, G: nx.Graph, lat: float, lng: float) -> str:
        """Find the nearest road intersection to a coordinate."""
        nearest = None
        min_dist = float('inf')
        for node, data in G.nodes(data=True):
            dist = (data['lat'] - lat)**2 + (data['lng'] - lng)**2
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest

    def get_route(self, district_id: str, start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> List[Tuple[float, float]]:
        """
        Calculate shortest path on road network between two coordinates.
        Returns a list of (lat, lng) points representing the polyline route.
        """
        G = self.road_manager.networks.get(district_id)
        if not G:
            return [(start_lat, start_lng), (end_lat, end_lng)]
            
        start_node = self._find_nearest_node(G, start_lat, start_lng)
        end_node = self._find_nearest_node(G, end_lat, end_lng)
        
        if not start_node or not end_node:
            return [(start_lat, start_lng), (end_lat, end_lng)]
            
        try:
            path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
            route = [(start_lat, start_lng)]
            for node in path:
                route.append((G.nodes[node]['lat'], G.nodes[node]['lng']))
            route.append((end_lat, end_lng))
            return route
        except nx.NetworkXNoPath:
            return [(start_lat, start_lng), (end_lat, end_lng)]
