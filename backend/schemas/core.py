from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional
from datetime import date


# ── Base response schemas (backward compatible) ───────────────────────────────

class PersonBase(BaseModel):
    citizen_id: str
    name_en: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone_primary: Optional[str] = None
    occupation: Optional[str] = None
    district_name: Optional[str] = None
    is_migrant: Optional[bool] = None

class PersonResponse(PersonBase):
    model_config = ConfigDict(from_attributes=True)

class FIRBase(BaseModel):
    fir_id: str
    fir_number: Optional[str] = None
    station_id: Optional[str] = None
    district_id: Optional[str] = None
    district_name: Optional[str] = None
    occurred_date: Optional[date] = None
    crime_type: Optional[str] = None
    crime_category: Optional[str] = None
    severity: Optional[int] = None
    status: Optional[str] = None
    description_en: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_gang_crime: Optional[bool] = None
    campaign_id: Optional[str] = None
    estimated_loss_inr: Optional[float] = None

class FIRResponse(FIRBase):
    model_config = ConfigDict(from_attributes=True)


# ── Investigation Drawer detail schemas ───────────────────────────────────────

class AccusedSummary(BaseModel):
    accused_id: str
    name_en: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    role: Optional[str] = None
    is_arrested: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class VictimSummary(BaseModel):
    victim_id: str
    name_en: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    injury_type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class InvLogSummary(BaseModel):
    log_id: str
    event_type: Optional[str] = None
    timestamp: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class VehicleSummary(BaseModel):
    vehicle_id: str
    license_plate: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    is_stolen: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class PhoneSummary(BaseModel):
    phone_id: str
    phone_number: Optional[str] = None
    provider: Optional[str] = None
    is_burner: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class FIRDetailResponse(BaseModel):
    fir: FIRResponse
    accused: List[AccusedSummary] = []
    victims: List[VictimSummary] = []
    evidence_count: int = 0
    investigation_logs: List[InvLogSummary] = []
    linked_vehicles: List[VehicleSummary] = []
    linked_phones: List[PhoneSummary] = []


class CriminalSummary(BaseModel):
    criminal_id: str
    name_en: Optional[str] = None
    risk_level: Optional[str] = None
    expertise: Optional[str] = None
    total_crimes_committed: Optional[int] = None
    is_currently_active: Optional[bool] = None
    gang_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class GangSummary(BaseModel):
    gang_id: str
    name: Optional[str] = None
    specialization: Optional[str] = None
    threat_level: Optional[str] = None
    num_members: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class PersonDetailResponse(BaseModel):
    person: PersonResponse
    criminal: Optional[CriminalSummary] = None
    linked_firs: List[FIRResponse] = []
    vehicles: List[VehicleSummary] = []
    phones: List[PhoneSummary] = []
    gang: Optional[GangSummary] = None

class VehicleDetailResponse(BaseModel):
    vehicle: VehicleSummary
    owner: Optional[PersonResponse] = None
    linked_firs: List[FIRResponse] = []

class ArrestSummary(BaseModel):
    arrest_id: str
    arrest_date: Optional[date] = None
    arrest_location: Optional[str] = None
    bail_granted: Optional[bool] = None
    is_convicted: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class CriminalDetailResponse(BaseModel):
    criminal: CriminalSummary
    gang: Optional[GangSummary] = None
    linked_firs: List[FIRResponse] = []
    associates: List[CriminalSummary] = []
    arrests: List[ArrestSummary] = []
