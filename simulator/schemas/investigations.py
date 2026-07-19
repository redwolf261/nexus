from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import List, Optional, Dict, Any

@dataclass
class ChainOfCustodyEntry:
    handler_id: str
    handler_type: str
    received_date: date
    action: str
    notes: str

@dataclass
class Evidence:
    evidence_id: str
    fir_id: str
    evidence_type: str
    description: str
    collection_date: date
    collection_officer_id: Optional[str]
    collection_location: str
    condition: str
    is_forensic: bool
    forensic_report_id: Optional[str]
    lab_name: Optional[str]
    lab_received_date: Optional[date]
    lab_result: Optional[str]
    is_recovered_property: bool
    estimated_value_inr: float
    chain_of_custody: List[ChainOfCustodyEntry] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

@dataclass
class ArrestRecord:
    arrest_id: str
    fir_id: str
    accused_id: str
    criminal_id: Optional[str]
    accused_name: str
    arresting_officer_id: Optional[str]
    arrest_date: date
    arrest_location: str
    district_id: str
    station_id: str
    arrest_type: str
    is_juvenile: bool
    remand_days: int
    bail_granted: bool
    bail_date: Optional[date]
    bail_amount_inr: float
    bail_court: Optional[str]
    is_convicted: bool
    conviction_date: Optional[date]
    sentence: Optional[str]

@dataclass
class Chargesheet:
    chargesheet_id: str
    fir_id: str
    filed_date: date
    filing_officer_id: Optional[str]
    court_name: str
    court_case_number: str
    ipc_sections: List[str]
    num_accused_charged: int
    accused_ids: List[str]
    status: str
    next_hearing_date: Optional[date]

@dataclass
class PatrolLog:
    log_id: str
    patrol_date: date
    station_id: str
    district_id: str
    district_name: str
    officer_id: str
    officer_rank: str
    vehicle_type: str
    vehicle_reg: str
    shift: str
    start_time: time
    end_time: time
    area_covered_km: float
    beat_area: str
    checkpost_count: int
    vehicles_checked: int
    persons_checked: int
    incidents_observed: int
    incident_notes: str
    patrol_type: str

@dataclass
class CCTVEvent:
    cctv_event_id: str
    camera_id: str
    camera_type: str
    camera_owner: str
    location_description: str
    latitude: float
    longitude: float
    district_id: str
    station_id: str
    event_timestamp: datetime
    vehicle_plate_captured: Optional[str]
    vehicle_type: Optional[str]
    vehicle_color: Optional[str]
    person_silhouette_class: str
    num_persons_captured: int
    linked_fir_id: Optional[str]
    is_primary_evidence: bool
    footage_available: bool
    footage_quality: str

@dataclass
class CallDetailRecord:
    cdr_id: str
    caller_phone_id: str
    receiver_phone_id: str
    timestamp: datetime
    duration_seconds: int
    cell_tower_lat: float
    cell_tower_lng: float
    call_type: str  # voice, sms, data

@dataclass
class InvestigationLog:
    log_id: str
    fir_id: str
    event_type: str # FIR_FILED, OFFICER_ASSIGNED, EVIDENCE_COLLECTED, SUSPECT_IDENTIFIED, ARREST, CHARGESHEET, CLOSED
    timestamp: datetime
    officer_id: Optional[str]
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None

@dataclass
class CourtCase:
    case_id: str
    chargesheet_id: str
    fir_id: str
    court_name: str
    judge_name: str
    filing_date: date
    verdict_date: Optional[date]
    verdict: str # PENDING, CONVICTION, ACQUITTAL
    sentence_type: Optional[str] # PRISON, FINE, BOTH
    sentence_months: int
    fine_amount_inr: float
