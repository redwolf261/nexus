import numpy as np
import networkx as nx
from typing import Dict, Any, List
from simulator.gis.boundaries import get_random_point_in_district

def generate_district_roads(district_id: str, rng: np.random.Generator, num_nodes: int = 50) -> nx.Graph:
    """
    Generate a synthetic but realistic road network for a district.
    Creates a planar-like graph by connecting nearest neighbors.
    """
    G = nx.Graph()
    G.graph["district_id"] = district_id
    
    # Generate nodes (intersections)
    nodes_data = []
    for i in range(num_nodes):
        lat, lng = get_random_point_in_district(district_id, rng)
        node_id = f"R-{district_id}-{i}"
        
        # Decide road type for node importance
        road_type = rng.choice(["highway", "arterial", "local"], p=[0.1, 0.3, 0.6])
        G.add_node(node_id, lat=lat, lng=lng, type=road_type)
        nodes_data.append((node_id, lat, lng))
        
    # Connect nodes to form a network
    # We will connect each node to its 2-4 nearest neighbors to ensure a connected graph with some cycles
    for i in range(num_nodes):
        u_id, u_lat, u_lng = nodes_data[i]
        
        # Calculate distances to all other nodes
        distances = []
        for j in range(num_nodes):
            if i != j:
                v_id, v_lat, v_lng = nodes_data[j]
                dist = np.sqrt((u_lat - v_lat)**2 + (u_lng - v_lng)**2)
                distances.append((dist, v_id))
                
        distances.sort()
        
        # Connect to 2 to 4 nearest neighbors
        num_connections = int(rng.integers(2, 5))
        for dist, v_id in distances[:num_connections]:
            if not G.has_edge(u_id, v_id):
                # Assign speed limit based on edge type
                u_type = G.nodes[u_id]["type"]
                v_type = G.nodes[v_id]["type"]
                
                if u_type == "highway" or v_type == "highway":
                    speed = 80.0
                elif u_type == "arterial" or v_type == "arterial":
                    speed = 50.0
                else:
                    speed = 30.0
                    
                # Store distance as edge weight (Euclidean approximation)
                G.add_edge(u_id, v_id, weight=dist, speed_kmh=speed)
                
    # Ensure graph is fully connected
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for k in range(len(components) - 1):
            comp1 = list(components[k])
            comp2 = list(components[k+1])
            u = rng.choice(comp1)
            v = rng.choice(comp2)
            u_lat, u_lng = G.nodes[u]["lat"], G.nodes[u]["lng"]
            v_lat, v_lng = G.nodes[v]["lat"], G.nodes[v]["lng"]
            dist = np.sqrt((u_lat - v_lat)**2 + (u_lng - v_lng)**2)
            G.add_edge(u, v, weight=dist, speed_kmh=50.0)
            
    return G

class RoadNetworkManager:
    def __init__(self, districts: List[str], rng: np.random.Generator):
        self.rng = rng
        self.networks = {}
        for d in districts:
            # 30 nodes per district is lightweight enough for fast generation
            self.networks[d] = generate_district_roads(d, rng, num_nodes=30)
            
    def export_geojson(self) -> Dict[str, Any]:
        features = []
        for d, G in self.networks.items():
            for u, v, data in G.edges(data=True):
                u_node = G.nodes[u]
                v_node = G.nodes[v]
                
                feature = {
                    "type": "Feature",
                    "properties": {
                        "district_id": d,
                        "speed_kmh": data["speed_kmh"]
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [u_node["lng"], u_node["lat"]],
                            [v_node["lng"], v_node["lat"]]
                        ]
                    }
                }
                features.append(feature)
                
        return {
            "type": "FeatureCollection",
            "features": features
        }
