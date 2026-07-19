from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any

@dataclass
class Coordinate:
    latitude: float
    longitude: float
    accuracy_meters: float = 10.0
    state: str = "Karnataka"
    district_id: Optional[str] = None
    district: Optional[str] = None
    subdivision: Optional[str] = None
    taluk: Optional[str] = None
    hobli: Optional[str] = None
    village: Optional[str] = None
    ward: Optional[str] = None
    police_circle: Optional[str] = None
    police_station: Optional[str] = None
    beat: Optional[str] = None
    pincode: Optional[str] = None

    def to_wkt(self) -> str:
        return f'POINT({self.longitude} {self.latitude})'

    def to_dict(self) -> dict:
        return {
            'latitude': self.latitude, 
            'longitude': self.longitude, 
            'accuracy_meters': self.accuracy_meters,
            'state': self.state,
            'district_id': self.district_id,
            'district': self.district,
            'subdivision': self.subdivision,
            'taluk': self.taluk,
            'hobli': self.hobli,
            'village': self.village,
            'ward': self.ward,
            'police_circle': self.police_circle,
            'police_station': self.police_station,
            'beat': self.beat,
            'pincode': self.pincode,
            'wkt': self.to_wkt()
        }

@dataclass
class Station:
    station_id: str
    name: str
    district_id: str
    district_name: str
    taluk: str
    station_type: str
    jurisdiction_area_km2: float
    population_served: int
    officer_quota: int
    latitude: float
    longitude: float
    established_year: int
    is_cyber_cell: bool
    is_traffic_cell: bool
    phone: str
    address: str

@dataclass
class District:
    district_id: str
    name: str
    headquarters: str
    district_type: str
    population_density: str
    num_stations: int
    stations: List[Station] = field(default_factory=list)
    taluks: List[str] = field(default_factory=list)

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
    is_high_risk: bool

@dataclass
class PointOfInterest:
    poi_id: str
    name: str
    poi_type: str # ATM, School, Temple, Bank, Liquor Store, Metro, etc.
    latitude: float
    longitude: float
    station_id: str
    district_id: str
    address: str
    category: str = "Unspecified"
    geometry: Optional[str] = None
    risk_factor: float = 0.5
    opening_hours: str = "24/7"
    footfall_score: int = 50
