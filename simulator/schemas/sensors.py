from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CellTower:
    tower_id: str
    latitude: float
    longitude: float
    district_id: str
    station_id: str
    provider: str

@dataclass
class CCTVCamera:
    camera_id: str
    latitude: float
    longitude: float
    district_id: str
    station_id: str
    camera_type: str # PUBLIC, PRIVATE, TRAFFIC
    resolution: str # 720p, 1080p, 4K

@dataclass
class ANPRCamera:
    anpr_id: str
    latitude: float
    longitude: float
    district_id: str
    station_id: str

@dataclass
class CellTowerPing:
    ping_id: str
    phone_id: str
    tower_id: str
    timestamp: datetime
    signal_strength: int # -120 to -40 dBm

@dataclass
class VehicleGPS:
    gps_id: str
    vehicle_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    speed_kmh: float

@dataclass
class CCTVLog:
    log_id: str
    camera_id: str
    timestamp: datetime
    vehicle_id: str # The true vehicle captured
    person_id: str # The true person captured
    confidence: float # Recognition confidence

@dataclass
class ANPRLog:
    log_id: str
    anpr_id: str
    vehicle_id: str # true vehicle
    plate_read: str # Might have noise/errors
    timestamp: datetime
    speed_kmh: float
