from typing import Tuple
from simulator.gis.spatial_index import GISPrecomputation
import numpy as np

def snap_crime_to_location(
    crime_category: str, 
    base_lat: float, 
    base_lng: float, 
    gis_index: GISPrecomputation, 
    rng: np.random.Generator
) -> Tuple[float, float, str]:
    """
    Given a crime category, snap the coordinate to an appropriate location type.
    """
    location_desc = "Street"
    
    # Simple logic to snap to POIs or roads
    if crime_category == "Robbery" or crime_category == "Theft":
        # 30% chance to snap near an ATM or Bank
        if rng.random() < 0.3:
            atm = gis_index.atms.get_nearest(base_lat, base_lng, max_radius_deg=0.1)
            if atm:
                # Add small jitter so it's not EXACTLY on the ATM
                jitter_lat = rng.uniform(-0.0001, 0.0001)
                jitter_lng = rng.uniform(-0.0001, 0.0001)
                return atm.latitude + jitter_lat, atm.longitude + jitter_lng, f"Near {atm.name}"
                
    elif crime_category == "Assault":
        if rng.random() < 0.2:
            hospital = gis_index.hospitals.get_nearest(base_lat, base_lng, max_radius_deg=0.1)
            if hospital:
                return hospital.latitude, hospital.longitude, f"Near {hospital.name}"

    # Default: jitter around the base location
    return base_lat + rng.uniform(-0.001, 0.001), base_lng + rng.uniform(-0.001, 0.001), location_desc
