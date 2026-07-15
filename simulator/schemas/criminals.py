from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any

@dataclass
class MoTemplate:
    """Structured Modus Operandi fingerprint for a criminal."""
    entry_method: str
    preferred_time_slot: str
    target_type: str
    escape_vehicle: str
    weapon: str
    stolen_property: str
    typical_num_offenders: int
    uses_accomplices: bool
    operates_at_night: bool

    def to_dict(self) -> dict:
        return {'entry_method': self.entry_method, 'preferred_time_slot': self.preferred_time_slot, 'target_type': self.target_type, 'escape_vehicle': self.escape_vehicle, 'weapon': self.weapon, 'stolen_property': self.stolen_property, 'typical_num_offenders': self.typical_num_offenders, 'uses_accomplices': self.uses_accomplices, 'operates_at_night': self.operates_at_night}

@dataclass
class CriminalProfile:
    criminal_id: str
    citizen_id: str
    name_en: str
    name_kn: str
    age: int
    gender: str
    district_id: str
    district_name: str
    station_id: str
    home_lat: float
    home_lng: float
    risk_level: str
    expertise: str
    preferred_crime_types: List[str]
    operating_radius_km: float
    modus_operandi: MoTemplate
    recidivism_probability: float
    career_stage: str
    is_gang_member: bool = False
    gang_id: Optional[str] = None
    is_gang_leader: bool = False
    vehicle_ids: List[str] = field(default_factory=list)
    phone_ids: List[str] = field(default_factory=list)
    known_associates: List[str] = field(default_factory=list)
    alias_names: List[str] = field(default_factory=list)
    total_crimes_committed: int = 0
    total_arrests: int = 0
    is_currently_active: bool = True
    is_currently_arrested: bool = False

@dataclass
class Gang:
    gang_id: str
    name: str
    specialization: str
    leader_criminal_id: str
    member_criminal_ids: List[str]
    territory_district_ids: List[str]
    territory_district_names: List[str]
    preferred_time_slot: str
    escape_vehicle_type: str
    communication_method: str
    num_members: int
    threat_level: str
    financial_links: List[str]
    is_interstate: bool
    total_crimes_attributed: int
    is_active: bool
    formation_year: int
    shared_vehicle_ids: List[str] = field(default_factory=list)

