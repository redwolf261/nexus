from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any

from simulator.config.constants import (
    MO_ENTRY_METHODS, MO_TIME_SLOTS, MO_TARGET_TYPES,
    MO_ESCAPE_VEHICLES, MO_WEAPONS, MO_STOLEN_PROPERTY
)

@dataclass
class MoFingerprint:
    """Per-crime MO fingerprint used for similarity analysis."""
    crime_event_id: str
    criminal_id: Optional[str]
    entry_method: str
    time_slot: str
    target_type: str
    escape_vehicle: str
    weapon: str
    stolen_property: str
    num_offenders: int
    operates_at_night: bool
    is_solo: bool
    uses_vehicle_escape: bool
    is_violent: bool

    def to_vector_dict(self) -> dict:
        """Return a numeric encoding suitable for ML clustering."""
        return {'entry_method': MO_ENTRY_METHODS.index(self.entry_method) if self.entry_method in MO_ENTRY_METHODS else 0, 'time_slot': MO_TIME_SLOTS.index(self.time_slot) if self.time_slot in MO_TIME_SLOTS else 0, 'target_type': MO_TARGET_TYPES.index(self.target_type) if self.target_type in MO_TARGET_TYPES else 0, 'escape_vehicle': MO_ESCAPE_VEHICLES.index(self.escape_vehicle) if self.escape_vehicle in MO_ESCAPE_VEHICLES else 0, 'weapon': MO_WEAPONS.index(self.weapon) if self.weapon in MO_WEAPONS else 0, 'stolen_property': MO_STOLEN_PROPERTY.index(self.stolen_property) if self.stolen_property in MO_STOLEN_PROPERTY else 0, 'num_offenders': self.num_offenders, 'operates_at_night': int(self.operates_at_night), 'is_solo': int(self.is_solo), 'uses_vehicle_escape': int(self.uses_vehicle_escape), 'is_violent': int(self.is_violent)}

@dataclass
class CrimeEvent:
    """Raw crime event — the fundamental unit of simulation output."""
    event_id: str
    crime_type: str
    crime_category: str
    ipc_section: str
    severity: int
    occurred_date: date
    occurred_time: time
    crime_duration_minutes: int
    latitude: float
    longitude: float
    location_accuracy_meters: float
    district_id: str
    district_name: str
    station_id: str
    primary_criminal_id: Optional[str]
    accomplice_criminal_ids: List[str]
    victim_citizen_ids: List[str]
    witness_citizen_ids: List[str]
    vehicle_ids_involved: List[str]
    phone_ids_involved: List[str]
    modus_operandi: MoFingerprint
    estimated_loss_inr: float
    day_context: str
    is_gang_crime: bool
    campaign_id: Optional[str] = None
    nearest_poi_id: Optional[str] = None
    gang_id: Optional[str] = None
    festival_context: Optional[str] = None
    fir_registered: bool = False
    fir_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Victim:
    victim_id: str
    fir_id: str
    name_en: str
    gender: str
    age: int
    phone: str
    address: str
    injury_type: str
    property_lost: str
    loss_amount_inr: float
    citizen_id: Optional[str]

@dataclass
class Accused:
    accused_id: str
    fir_id: str
    criminal_id: Optional[str]
    name_en: str
    name_kn: str
    age: Optional[int]
    gender: Optional[str]
    address: Optional[str]
    is_known: bool
    is_arrested: bool
    role: str

@dataclass
class FIR:
    fir_id: str
    event_id: str
    fir_number: str
    station_id: str
    district_id: str
    district_name: str
    occurred_date: date
    reported_date: date
    crime_type: str
    crime_category: str
    ipc_sections: List[str]
    severity: int
    status: str
    description_en: str
    description_kn: str
    latitude: float
    longitude: float
    complainant_name: str
    complainant_phone: str
    complainant_address: str
    estimated_loss_inr: float
    num_accused: int
    num_victims: int
    num_witnesses: int
    is_gang_crime: bool
    season: str
    accomplice_criminal_ids: List[str]
    vehicle_ids: List[str]
    phone_ids: List[str]
    campaign_id: Optional[str] = None
    nearest_poi_id: Optional[str] = None
    investigating_officer_id: Optional[str] = None
    sho_officer_id: Optional[str] = None
    gang_id: Optional[str] = None
    festival_context: Optional[str] = None
    primary_criminal_id: Optional[str] = None
    victims: List[Victim] = field(default_factory=list)
    accused_list: List[Accused] = field(default_factory=list)

@dataclass
class CrimeCampaign:
    campaign_id: str
    gang_id: str
    crime_category: str
    start_date: date
    end_date: Optional[date]
    num_crimes_planned: int
    num_crimes_committed: int
    status: str # active, completed, interrupted
    target_district_id: str
