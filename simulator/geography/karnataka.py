"""
NEXUS Simulator — Karnataka Geography Builder
Generates the district → taluk → station hierarchy.
Each station gets a jurisdiction polygon approximation, population density class,
officer quota, and resource profile.
"""
from __future__ import annotations
import numpy as np
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from simulator.config.constants import KARNATAKA_DISTRICTS, POLICE_RANKS
from simulator.schemas.geography import Station, District
from simulator.schemas.geography import Station, District
from simulator.schemas.geography import Station, District


# ─────────────────────────────────────────────────────────────────────────────
# APPROXIMATE STATION COUNTS PER DENSITY CLASS
# ─────────────────────────────────────────────────────────────────────────────
STATIONS_PER_DISTRICT = {
    "metro":       60,
    "urban":       30,
    "semi_urban":  18,
    "rural":       10,
}

# Officer quotas per station type
OFFICERS_PER_STATION = {
    "metro":       45,
    "urban":       25,
    "semi_urban":  15,
    "rural":       8,
}

# Karnataka taluk names sampled per district (representative)
DISTRICT_TALUKS: Dict[str, List[str]] = {
    "KA-BLR": ["Bengaluru North", "Bengaluru South", "Bengaluru East", "Bengaluru West", "Yelahanka", "Rajarajeshwari Nagar", "Mahadevapura"],
    "KA-BLR-R": ["Hosakote", "Devanahalli", "Doddaballapura", "Nelamangala"],
    "KA-MYS": ["Mysuru", "Nanjangud", "Hunsur", "Heggadadevankote", "Periyapatna", "T Narsipur", "Krishnarajanagar"],
    "KA-MGL": ["Mangaluru", "Bantwal", "Belthangady", "Puttur", "Sullia", "Kadaba"],
    "KA-HBL": ["Hubballi", "Dharwad", "Kalghatagi", "Navalgund", "Kundgol"],
    "KA-BLG": ["Belagavi", "Gokak", "Hukkeri", "Khanapur", "Chikkodi", "Raibag", "Ramdurg", "Savadatti"],
    "KA-KLP": ["Kalaburagi", "Afzalpur", "Chittapur", "Gulbarga", "Sedam", "Shorapur", "Yadgir"],
    "KA-DVG": ["Davanagere", "Harihar", "Channagiri", "Harapanahalli", "Jagalur"],
    "KA-SHV": ["Shivamogga", "Bhadravati", "Tirthahalli", "Soraba", "Sagar", "Hosanagara"],
    "KA-TKR": ["Tumakuru", "Tiptur", "Gubbi", "Sira", "Pavagada", "Madhugiri", "Chikkanayakanahalli"],
    "KA-RCR": ["Raichur", "Manvi", "Devadurga", "Lingasugur", "Sindhanur"],
    "KA-BDR": ["Bidar", "Basavakalyan", "Aurad", "Bhalki", "Humnabad"],
    "KA-VJP": ["Vijayapura", "Basavana Bagewadi", "Indi", "Muddebihal", "Sindagi"],
    "KA-BSD": ["Bagalkote", "Badami", "Bilagi", "Hungund", "Jamkhandi", "Mudhol"],
    "KA-HSN": ["Hassan", "Arsikere", "Belur", "Channarayapatna", "Holenarasipur", "Sakleshpur"],
    "KA-CKM": ["Chikkamagaluru", "Kadur", "Koppa", "Mudigere", "Sringeri", "Tarikere"],
    "KA-KDG": ["Madikeri", "Somwarpet", "Virajpete"],
    "KA-UDR": ["Udupi", "Kundapura", "Karkala", "Brahmavar"],
    "KA-MDY": ["Mandya", "Maddur", "Malavalli", "Nagamangala", "Pandavapura", "Shrirangapattana"],
    "KA-CHT": ["Chamarajanagara", "Gundlupete", "Hanur", "Yelandur"],
    "KA-KLR": ["Kolar", "Bangarpet", "Malur", "Mulbagal", "Srinivaspur"],
    "KA-CHB": ["Chikkaballapura", "Bagepalli", "Chintamani", "Gauribidanur", "Gudibande", "Sidlaghatta"],
    "KA-RMN": ["Ramanagara", "Channapatna", "Kanakapura", "Magadi"],
    "KA-GBG": ["Gadag", "Ron", "Shirhatti", "Mundargi", "Nargund"],
    "KA-HVR": ["Haveri", "Byadagi", "Hanagal", "Hirekerur", "Ranebennur", "Shiggaon"],
    "KA-KPT": ["Koppal", "Gangavathi", "Kushtagi", "Yelburga"],
    "KA-YDG": ["Yadgir", "Gurmatkal", "Shorapur"],
    "KA-VKT": ["Hosapete", "Hagaribommanahalli", "Hadagali", "Harapanahalli", "Hoovina Hadagali"],
    "KA-CTV": ["Chitradurga", "Challakere", "Hiriyur", "Holalkere", "Hosadurga", "Molakalmuru"],
    "KA-BLR2": ["Ballari", "Hagaribommanahalli", "Sandur", "Siruguppa"],
    "KA-RBG": ["Dharwad", "Hubballi", "Kalghatagi", "Navalgund"],
}






def _make_station(
    rng: np.random.Generator,
    station_idx: int,
    district: Dict,
    taluk: str,
    coord_bounds: Dict,
) -> Station:
    """Construct a single police station record."""
    dist_type = district["type"]

    station_type_weights = {
        "metro":       ["city"] * 5 + ["town"] * 3 + ["rural"] * 1,
        "urban":       ["city"] * 2 + ["town"] * 4 + ["rural"] * 2,
        "semi_urban":  ["town"] * 4 + ["rural"] * 4,
        "rural":       ["town"] * 2 + ["rural"] * 6,
    }
    stype = rng.choice(station_type_weights.get(dist_type, ["town"]))

    area_km2_map = {"city": rng.uniform(5, 30), "town": rng.uniform(30, 150), "rural": rng.uniform(150, 500)}
    pop_map      = {"city": int(rng.integers(50_000, 500_000 + 1)), "town": int(rng.integers(10_000, 80_000 + 1)), "rural": int(rng.integers(3_000, 20_000 + 1))}
    off_map      = {"city": int(rng.integers(30, 60 + 1)), "town": int(rng.integers(10, 30 + 1)), "rural": int(rng.integers(4, 12 + 1))}

    lat = rng.uniform(coord_bounds["lat_min"], coord_bounds["lat_max"])
    lng = rng.uniform(coord_bounds["lng_min"], coord_bounds["lng_max"])

    station_name = f"{taluk} {'Town' if stype == 'town' else 'Rural' if stype == 'rural' else ''} PS".strip()
    if station_idx > 0:
        station_name = f"{taluk} PS-{station_idx + 1}"

    station_id = f"STN-{district['id']}-{station_idx:04d}"

    return Station(
        station_id=station_id,
        name=station_name,
        district_id=district["id"],
        district_name=district["name"],
        taluk=taluk,
        station_type=stype,
        jurisdiction_area_km2=round(area_km2_map[stype], 2),
        population_served=pop_map[stype],
        officer_quota=off_map[stype],
        latitude=round(lat, 6),
        longitude=round(lng, 6),
        established_year=int(rng.integers(1950, 2015 + 1)),
        is_cyber_cell=rng.random() < 0.2,
        is_traffic_cell=rng.random() < 0.3,
        phone=f"080-{int(rng.integers(20000000, 29999999 + 1))}",
        address=f"Near {rng.choice(['Main Road', 'Bus Stand', 'Taluk Office', 'Court Complex'])}, {taluk}, {district['name']}",
    )


# Real approximate bounding boxes per district
DISTRICT_BOUNDS: Dict[str, Dict] = {
    "KA-BLR":  {"lat_min": 12.8, "lat_max": 13.2, "lng_min": 77.4, "lng_max": 77.8},
    "KA-BLR-R":{"lat_min": 12.9, "lat_max": 13.5, "lng_min": 77.3, "lng_max": 77.7},
    "KA-MYS":  {"lat_min": 11.8, "lat_max": 12.5, "lng_min": 76.2, "lng_max": 77.1},
    "KA-MGL":  {"lat_min": 12.4, "lat_max": 13.0, "lng_min": 74.8, "lng_max": 75.5},
    "KA-HBL":  {"lat_min": 15.0, "lat_max": 15.6, "lng_min": 74.8, "lng_max": 75.5},
    "KA-BLG":  {"lat_min": 15.5, "lat_max": 16.4, "lng_min": 74.2, "lng_max": 75.2},
    "KA-KLP":  {"lat_min": 17.0, "lat_max": 17.7, "lng_min": 76.5, "lng_max": 77.5},
    "KA-DVG":  {"lat_min": 14.2, "lat_max": 14.8, "lng_min": 75.6, "lng_max": 76.3},
    "KA-SHV":  {"lat_min": 13.7, "lat_max": 14.4, "lng_min": 74.9, "lng_max": 75.8},
    "KA-TKR":  {"lat_min": 13.0, "lat_max": 14.0, "lng_min": 76.5, "lng_max": 77.3},
    "KA-RCR":  {"lat_min": 15.9, "lat_max": 16.5, "lng_min": 76.8, "lng_max": 77.6},
    "KA-BDR":  {"lat_min": 17.5, "lat_max": 18.3, "lng_min": 76.8, "lng_max": 77.7},
    "KA-VJP":  {"lat_min": 16.6, "lat_max": 17.3, "lng_min": 75.5, "lng_max": 76.5},
    "KA-BSD":  {"lat_min": 16.0, "lat_max": 16.8, "lng_min": 75.2, "lng_max": 76.0},
    "KA-HSN":  {"lat_min": 12.7, "lat_max": 13.3, "lng_min": 75.8, "lng_max": 76.6},
    "KA-CKM":  {"lat_min": 13.0, "lat_max": 13.5, "lng_min": 75.6, "lng_max": 76.1},
    "KA-KDG":  {"lat_min": 11.8, "lat_max": 12.7, "lng_min": 75.6, "lng_max": 76.3},
    "KA-UDR":  {"lat_min": 13.2, "lat_max": 13.8, "lng_min": 74.6, "lng_max": 75.2},
    "KA-MDY":  {"lat_min": 12.3, "lat_max": 12.9, "lng_min": 76.5, "lng_max": 77.0},
    "KA-CHT":  {"lat_min": 11.7, "lat_max": 12.3, "lng_min": 76.5, "lng_max": 77.5},
    "KA-KLR":  {"lat_min": 12.8, "lat_max": 13.3, "lng_min": 78.0, "lng_max": 78.5},
    "KA-CHB":  {"lat_min": 13.3, "lat_max": 13.9, "lng_min": 77.5, "lng_max": 78.2},
    "KA-RMN":  {"lat_min": 12.5, "lat_max": 13.0, "lng_min": 77.2, "lng_max": 77.7},
    "KA-GBG":  {"lat_min": 15.2, "lat_max": 15.7, "lng_min": 75.4, "lng_max": 76.0},
    "KA-HVR":  {"lat_min": 14.4, "lat_max": 15.0, "lng_min": 75.0, "lng_max": 75.6},
    "KA-KPT":  {"lat_min": 15.2, "lat_max": 15.8, "lng_min": 76.0, "lng_max": 76.6},
    "KA-YDG":  {"lat_min": 16.3, "lat_max": 16.9, "lng_min": 76.5, "lng_max": 77.2},
    "KA-VKT":  {"lat_min": 14.8, "lat_max": 15.6, "lng_min": 75.8, "lng_max": 76.5},
    "KA-CTV":  {"lat_min": 13.9, "lat_max": 14.9, "lng_min": 76.2, "lng_max": 77.1},
    "KA-BLR2": {"lat_min": 14.8, "lat_max": 15.6, "lng_min": 76.5, "lng_max": 77.2},
    "KA-RBG":  {"lat_min": 15.2, "lat_max": 15.6, "lng_min": 74.8, "lng_max": 75.4},
}


def build_geography(rng: np.random.Generator) -> tuple[List[District], List[Station]]:
    """
    Build the complete Karnataka district → station hierarchy.
    Returns (districts_list, stations_list).
    """
    all_districts: List[District] = []
    all_stations: List[Station] = []

    for dist_meta in KARNATAKA_DISTRICTS:
        dist_id = dist_meta["id"]
        taluks = DISTRICT_TALUKS.get(dist_id, [dist_meta["hq"]])
        num_stations = STATIONS_PER_DISTRICT.get(dist_meta["type"], 10)
        bounds = DISTRICT_BOUNDS.get(dist_id, {"lat_min": 12.0, "lat_max": 18.0, "lng_min": 74.0, "lng_max": 78.5})

        district = District(
            district_id=dist_id,
            name=dist_meta["name"],
            headquarters=dist_meta["hq"],
            district_type=dist_meta["type"],
            population_density=dist_meta["population_density"],
            num_stations=num_stations,
            taluks=taluks,
        )

        # Distribute stations across taluks
        station_counter = 0
        for i, taluk in enumerate(taluks):
            # Each taluk gets at least 1 station, remainder distributed
            stations_in_taluk = max(1, num_stations // len(taluks))
            if i == 0:
                stations_in_taluk += num_stations % len(taluks)

            for j in range(stations_in_taluk):
                stn = _make_station(rng, station_counter, dist_meta, taluk, bounds)
                district.stations.append(stn)
                all_stations.append(stn)
                station_counter += 1

        all_districts.append(district)

    return all_districts, all_stations