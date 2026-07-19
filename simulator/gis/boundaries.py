from typing import Dict, Any
from simulator.geography.karnataka import DISTRICT_BOUNDS

def generate_district_boundaries() -> Dict[str, Any]:
    """
    Generate GeoJSON-compatible FeatureCollection for all district boundaries.
    Uses the approximate bounding boxes defined in karnataka.py.
    """
    features = []
    
    for district_id, bounds in DISTRICT_BOUNDS.items():
        # A simple rectangular polygon for the district
        poly = [
            [bounds["lng_min"], bounds["lat_min"]],
            [bounds["lng_max"], bounds["lat_min"]],
            [bounds["lng_max"], bounds["lat_max"]],
            [bounds["lng_min"], bounds["lat_max"]],
            [bounds["lng_min"], bounds["lat_min"]]
        ]
        
        feature = {
            "type": "Feature",
            "properties": {
                "district_id": district_id
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly]
            }
        }
        features.append(feature)
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_random_point_in_district(district_id: str, rng) -> tuple[float, float]:
    """
    Generate a random (lat, lng) strictly within a district's bounding box.
    """
    bounds = DISTRICT_BOUNDS.get(district_id, {"lat_min": 12.0, "lat_max": 18.0, "lng_min": 74.0, "lng_max": 78.5})
    lat = rng.uniform(bounds["lat_min"], bounds["lat_max"])
    lng = rng.uniform(bounds["lng_min"], bounds["lng_max"])
    return lat, lng
