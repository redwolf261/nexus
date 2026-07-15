"""
NEXUS Simulator — Coordinate Sampler
Provides spatially-biased coordinate sampling within Karnataka.
Crime locations cluster around populated areas rather than being uniform random.
"""
from __future__ import annotations
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

from simulator.geography.karnataka import DISTRICT_BOUNDS, Station


KARNATAKA_BBOX = {
    "lat_min": 11.5,
    "lat_max": 18.5,
    "lng_min": 74.0,
    "lng_max": 78.6,
}


@dataclass
class Coordinate:
    latitude: float
    longitude: float
    accuracy_meters: float = 10.0   # GPS accuracy simulation
    district_id: Optional[str] = None

    def to_wkt(self) -> str:
        return f"POINT({self.longitude} {self.latitude})"

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy_meters": self.accuracy_meters,
            "wkt": self.to_wkt(),
        }


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in kilometers between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class CoordinateSampler:
    """
    Samples coordinates biased toward populated stations.
    Supports:
      - Random coordinate within a district
      - Coordinate near a specific station (Gaussian spread)
      - Coordinate within operating radius of a criminal's home station
    """

    def __init__(self, stations: List[Station], rng: random.Random) -> None:
        self.stations = stations
        self.rng = rng
        # Build a weighted list of stations based on population served
        self._weights = [s.population_served for s in stations]
        self._total_weight = sum(self._weights)

    def sample_near_station(
        self,
        station: Station,
        radius_km: float = 10.0,
        noise_pct: float = 0.0,
    ) -> Coordinate:
        """
        Sample a point within radius_km of a station center.
        Uses polar Gaussian to maintain spatial realism.
        """
        # Gaussian distance within radius
        distance = abs(self.rng.gauss(0, radius_km / 3))
        distance = min(distance, radius_km)
        angle = self.rng.uniform(0, 2 * math.pi)

        # Convert km offset to degrees (approx)
        delta_lat = (distance * math.cos(angle)) / 111.0
        delta_lng = (distance * math.sin(angle)) / (111.0 * math.cos(math.radians(station.latitude)))

        lat = round(station.latitude + delta_lat, 6)
        lng = round(station.longitude + delta_lng, 6)

        # Clamp to Karnataka
        lat = max(KARNATAKA_BBOX["lat_min"], min(KARNATAKA_BBOX["lat_max"], lat))
        lng = max(KARNATAKA_BBOX["lng_min"], min(KARNATAKA_BBOX["lng_max"], lng))

        # GPS noise injection
        accuracy = 10.0
        if noise_pct > 0 and self.rng.random() < noise_pct:
            lat += self.rng.uniform(-0.005, 0.005)
            lng += self.rng.uniform(-0.005, 0.005)
            accuracy = self.rng.uniform(50, 500)

        return Coordinate(latitude=lat, longitude=lng, accuracy_meters=accuracy, district_id=station.district_id)

    def sample_population_weighted(self, noise_pct: float = 0.0) -> Tuple[Coordinate, Station]:
        """
        Sample a station proportional to its population, then sample a coordinate near it.
        """
        r = self.rng.uniform(0, self._total_weight)
        cumulative = 0.0
        chosen = self.stations[-1]
        for station, weight in zip(self.stations, self._weights):
            cumulative += weight
            if r <= cumulative:
                chosen = station
                break
        coord = self.sample_near_station(chosen, radius_km=5.0, noise_pct=noise_pct)
        return coord, chosen

    def sample_within_district(self, district_id: str) -> Coordinate:
        """Sample a coordinate within the real bounding box of a district."""
        bounds = DISTRICT_BOUNDS.get(district_id, KARNATAKA_BBOX)
        lat = self.rng.uniform(bounds["lat_min"], bounds["lat_max"])
        lng = self.rng.uniform(bounds["lng_min"], bounds["lng_max"])
        return Coordinate(latitude=round(lat, 6), longitude=round(lng, 6), district_id=district_id)

    def sample_within_radius(
        self, center_lat: float, center_lng: float, radius_km: float
    ) -> Coordinate:
        """Sample within radius_km of a given center point."""
        distance = self.rng.uniform(0, radius_km)
        angle = self.rng.uniform(0, 2 * math.pi)
        delta_lat = (distance * math.cos(angle)) / 111.0
        delta_lng = (distance * math.sin(angle)) / (111.0 * math.cos(math.radians(center_lat)))
        lat = round(center_lat + delta_lat, 6)
        lng = round(center_lng + delta_lng, 6)
        lat = max(KARNATAKA_BBOX["lat_min"], min(KARNATAKA_BBOX["lat_max"], lat))
        lng = max(KARNATAKA_BBOX["lng_min"], min(KARNATAKA_BBOX["lng_max"], lng))
        return Coordinate(latitude=lat, longitude=lng)

    def get_stations_within_radius(
        self, center_lat: float, center_lng: float, radius_km: float
    ) -> List[Station]:
        """Return all stations within radius_km of a center point."""
        return [
            s for s in self.stations
            if _haversine_distance(center_lat, center_lng, s.latitude, s.longitude) <= radius_km
        ]
