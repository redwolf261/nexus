"""
NEXUS Simulator — Landmark & Location Generator
Populates each station jurisdiction with typed POIs:
banks, ATMs, markets, temples, schools, hospitals, bus stands, residential clusters.
"""
from __future__ import annotations
import random
import uuid
from dataclasses import dataclass
from typing import List

from simulator.geography.karnataka import Station


LOCATION_TYPES = [
    "bank", "atm", "market", "temple", "church", "mosque", "school",
    "college", "hospital", "bus_stand", "railway_station", "petrol_pump",
    "hotel", "mall", "theatre", "park", "playground", "residential_area",
    "industrial_area", "warehouse", "jewellery_shop", "pawn_shop"
]

# How many of each type per 100k population
LOCATION_DENSITY: dict = {
    "bank":              0.8,
    "atm":               3.0,
    "market":            2.0,
    "temple":            8.0,
    "church":            1.5,
    "mosque":            1.0,
    "school":            4.0,
    "college":           0.8,
    "hospital":          1.0,
    "bus_stand":         0.5,
    "railway_station":   0.2,
    "petrol_pump":       1.5,
    "hotel":             1.2,
    "mall":              0.3,
    "theatre":           0.4,
    "park":              1.0,
    "playground":        1.5,
    "residential_area":  10.0,
    "industrial_area":   0.4,
    "warehouse":         0.6,
    "jewellery_shop":    0.5,
    "pawn_shop":         0.3,
}

LOCATION_NAME_PREFIXES: dict = {
    "bank": ["State Bank of India", "Canara Bank", "Union Bank", "HDFC Bank",
             "ICICI Bank", "Axis Bank", "Bank of Baroda", "Karnataka Bank",
             "Vijaya Bank", "Corporation Bank", "Indian Bank"],
    "market": ["Rythu", "KR", "City", "Old", "New", "Central", "Gandhi",
                "Nehru", "Mahatma", "Indira", "District", "Taluk"],
    "temple": ["Sri Venkateswara", "Sri Rama", "Sri Hanuman", "Sri Lakshmi",
                "Sri Ganesha", "Sri Basaveshwara", "Sri Shiva", "Sri Anjaneya"],
    "school": ["Government Higher Primary", "Zilla Panchayat High", "Kendriya Vidyalaya",
                "Government High School", "Private High School", "Convent"],
    "hospital": ["District Government", "Taluk Government", "PHC", "CHC",
                  "Private Nursing Home", "Specialist Clinic"],
}


@dataclass
class Location:
    location_id: str
    name: str
    location_type: str
    station_id: str
    district_id: str
    district_name: str
    taluk: str
    latitude: float
    longitude: float
    address: str
    is_high_risk: bool          # ATMs, banks, jewellery shops = True


def generate_locations(
    stations: List[Station],
    rng: random.Random,
    max_locations_per_station: int = 30,
) -> List[Location]:
    """
    Generate POI locations for all stations.
    Location density is proportional to population served.
    """
    all_locations: List[Location] = []
    loc_idx = 0

    for station in stations:
        pop_lakhs = station.population_served / 100_000
        station_locations: List[Location] = []

        for loc_type, density in LOCATION_DENSITY.items():
            count = max(1, int(pop_lakhs * density))
            count = min(count, max_locations_per_station // len(LOCATION_TYPES) + 2)

            for _ in range(count):
                # Jitter coordinates around station center
                lat = station.latitude  + rng.uniform(-0.05, 0.05)
                lng = station.longitude + rng.uniform(-0.05, 0.05)

                # Build name
                prefixes = LOCATION_NAME_PREFIXES.get(loc_type, [])
                if prefixes:
                    name = f"{rng.choice(prefixes)} {loc_type.replace('_', ' ').title()} - {station.taluk}"
                else:
                    name = f"{station.taluk} {loc_type.replace('_', ' ').title()} {loc_idx}"

                high_risk = loc_type in {"atm", "bank", "jewellery_shop", "pawn_shop", "market"}

                location = Location(
                    location_id=f"LOC-{loc_idx:08d}",
                    name=name,
                    location_type=loc_type,
                    station_id=station.station_id,
                    district_id=station.district_id,
                    district_name=station.district_name,
                    taluk=station.taluk,
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    address=f"Near {name}, {station.taluk}, {station.district_name}",
                    is_high_risk=high_risk,
                )
                station_locations.append(location)
                loc_idx += 1

        all_locations.extend(station_locations)

    return all_locations
