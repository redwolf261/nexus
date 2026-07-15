from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any

@dataclass
class Citizen:
    citizen_id: str
    name_en: str
    name_kn: str
    first_name_en: str
    last_name_en: str
    gender: str
    dob: date
    age: int
    aadhaar: str
    dl_number: Optional[str]
    phone_primary: str
    phone_secondary: Optional[str]
    occupation: str
    socioeconomic_class: str
    religion: str
    caste: str
    education: str
    district_id: str
    district_name: str
    taluk: str
    station_id: str
    home_lat: float
    home_lng: float
    home_address: str
    bank_account: Optional[str]
    upi_id: Optional[str]
    is_migrant: bool

    @property
    def is_adult(self) -> bool:
        return self.age >= 18

    @property
    def has_vehicle_license(self) -> bool:
        return self.dl_number is not None

@dataclass
class Officer:
    officer_id: str
    badge_number: str
    name_en: str
    gender: str
    rank: str
    rank_level: int
    rank_abbr: str
    station_id: str
    district_id: str
    district_name: str
    phone: str
    doj: date
    tenure_years: int
    shift: str
    specialization: str
    is_investigating_officer: bool
    is_station_house_officer: bool

@dataclass
class Vehicle:
    vehicle_id: str
    owner_id: str
    license_plate: str
    make: str
    model: str
    color: str
    type: str  # car, motorcycle, truck, etc.
    registration_year: int
    is_stolen: bool = False

@dataclass
class Phone:
    phone_id: str
    owner_id: str
    phone_number: str
    provider: str
    type: str  # smartphone, feature_phone, satellite
    is_burner: bool = False

@dataclass
class SocialTie:
    source_id: str
    target_id: str
    relationship_type: str # FAMILY, FRIEND, NEIGHBOUR, BUSINESS, FORMER_CELLMATE, LOAN
    strength: float # 0.0 to 1.0
    start_year: int
