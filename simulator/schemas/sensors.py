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
    radius: float = 5000.0
    operator: str = "Airtel"
    sector_count: int = 3
    coverage_polygon: str = ""

@dataclass
class CCTVCamera:
    camera_id: str
    latitude: float
    longitude: float
    district_id: str
    station_id: str
    camera_type: str # PUBLIC, PRIVATE, TRAFFIC
    resolution: str # 720p, 1080p, 4K
    coverage_radius: float = 50.0
    orientation: float = 0.0
    field_of_view: float = 90.0
    installation_height: float = 5.0
    day_night: bool = True
    operational_status: str = "ACTIVE"

@dataclass
class ANPRCamera:
    anpr_id: str
    latitude: float
    longitude: float
    district_id: str
    station_id: str
    direction: str = "NORTH"
    lanes: int = 2
    capture_probability: float = 0.95
    ocr_accuracy: float = 0.9

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
