"""
NEXUS Simulator — Points of Interest (POI) Generator
Generates realistic POIs (ATMs, Banks, Temples, Liquor Stores) near stations.
"""
from __future__ import annotations
import numpy as np
from typing import List

from simulator.geography.karnataka import Station
from simulator.schemas.geography import PointOfInterest

POI_TYPES = ["ATM", "Bank", "Temple", "School", "Liquor Store", "Metro Station", "Market", "Jewellery Shop"]

def generate_pois(stations: List[Station], rng: np.random.Generator) -> List[PointOfInterest]:
    pois: List[PointOfInterest] = []
    poi_counter = 0

    for station in stations:
        # Generate 2 to 10 POIs per station
        num_pois = int(rng.integers(2, 11))
        for _ in range(num_pois):
            ptype = rng.choice(POI_TYPES)
            lat = round(station.latitude + rng.uniform(-0.03, 0.03), 5)
            lng = round(station.longitude + rng.uniform(-0.03, 0.03), 5)
            
            name = f"{ptype} - {station.name} Area"
            
            pois.append(PointOfInterest(
                poi_id=f"POI-{poi_counter:06d}",
                name=name,
                poi_type=ptype,
                latitude=lat,
                longitude=lng,
                station_id=station.station_id,
                district_id=station.district_id,
                address=f"Near {station.name}, {station.district_name}"
            ))
            poi_counter += 1
            
    return pois
