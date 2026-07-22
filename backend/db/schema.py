"""
NEXUS PostgreSQL Schema — full data layer.

Defines every relational table for the platform. This is the single source of
truth for the Postgres side; `backend/models.py` re-exports Person/Vehicle/FIR
from here so the existing API/analytics import path keeps working unchanged.

Design notes:
  - Types are explicit (Date, Float, Integer, Boolean, Numeric). The loader
    coerces raw CSV strings to these types generically (see pg_loader._coerce).
  - HARD ForeignKeys are declared only on clean, reliable ID relationships
    (the geographic/ownership backbone and case children -> FIR). Optional or
    polymorphic investigative links (e.g. FIR.primary_criminal_id — a suspect
    may be unidentified; CDR phone-number refs; FENCE-* financial parties) are
    plain INDEXED columns ("soft references"), validated by the validation
    pipeline but not DB-enforced, because enforcing them would be semantically
    wrong (unidentified entities legitimately have no parent row).
  - The gangs<->criminals cycle uses soft (indexed, non-FK) references on both
    sides (criminals.gang_id, gangs.leader_criminal_id), validated not enforced.
  - CHECK constraints guard latitude/longitude ranges.
"""
from __future__ import annotations

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, Time, Text, Numeric,
    ForeignKey, CheckConstraint, Index, DateTime, Enum
)

from backend.database import Base

import enum
from sqlalchemy.sql import func

class CrimeType(str, enum.Enum):
    THEFT = "Theft"
    ASSAULT = "Assault"
    FRAUD = "Fraud"
    MURDER = "Murder"
    NARCOTICS = "Narcotics"
    CYBER = "Cyber"
    TRAFFIC = "Traffic"
    OTHER = "Other"

class Role(str, enum.Enum):
    Admin = "Admin"
    Analyst = "Analyst"
    Supervisor = "Supervisor"
    ReadOnly = "ReadOnly"

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(Role), default=Role.ReadOnly)
    created_at = Column(DateTime, default=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    user_id = Column(String, ForeignKey('users.id'), index=True)
    action = Column(String)
    target_id = Column(String)
    request_id = Column(String)
    ip_address = Column(String)
    status = Column(String)


def _latlng_checks(prefix_lat: str = "latitude", prefix_lng: str = "longitude"):
    return (
        CheckConstraint(f"{prefix_lat} IS NULL OR ({prefix_lat} BETWEEN -90 AND 90)",
                        name=None),
        CheckConstraint(f"{prefix_lng} IS NULL OR ({prefix_lng} BETWEEN -180 AND 180)",
                        name=None),
    )


# ── Geography & infrastructure ──────────────────────────────────────────────
class District(Base):
    __tablename__ = "districts"
    district_id = Column(String, primary_key=True)
    name = Column(String, index=True)
    headquarters = Column(String)
    district_type = Column(String)
    population_density = Column(String)
    num_stations = Column(Integer)
    taluks = Column(Text)  # pipe-delimited; kept as text (geographic reference list)


class Station(Base):
    __tablename__ = "stations"
    station_id = Column(String, primary_key=True)
    name = Column(String, index=True)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    district_name = Column(String)
    taluk = Column(String)
    station_type = Column(String)
    jurisdiction_area_km2 = Column(Float)
    population_served = Column(Integer)
    officer_quota = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    established_year = Column(Integer)
    is_cyber_cell = Column(Boolean)
    is_traffic_cell = Column(Boolean)
    phone = Column(String)
    address = Column(Text)
    __table_args__ = (*_latlng_checks(),)


class Officer(Base):
    __tablename__ = "officers"
    officer_id = Column(String, primary_key=True)
    badge_number = Column(String, unique=True, index=True)
    name_en = Column(String, index=True)
    gender = Column(String)
    rank = Column(String)
    rank_level = Column(Integer)
    rank_abbr = Column(String)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    district_name = Column(String)
    phone = Column(String)
    doj = Column(Date)
    tenure_years = Column(Integer)
    shift = Column(String)
    specialization = Column(String, index=True)
    is_investigating_officer = Column(Boolean)
    is_station_house_officer = Column(Boolean)

    # ── Phase 8.2: Capability & Workload Model ──────────────────────────────
    # All columns are nullable / defaulted so the dataset CSV loader (which
    # inserts only the original columns) remains backward-compatible.
    subdivision = Column(String, nullable=True, index=True)
    years_experience = Column(Integer, nullable=True)  # Distinct from tenure_years (may be seeded from it)
    maximum_capacity = Column(Integer, nullable=True, default=10)  # Max concurrent open cases
    availability_status = Column(
        Enum("ON_DUTY", "OFF_DUTY", "BREAK", "FIELD", "LEAVE", "TRAINING", "SUSPENDED",
             name="availabilitystatus"),
        nullable=True, default="ON_DUTY", index=True,
    )
    # Denormalized workload counters — cached for speed, DB is source of truth.
    # Reconciliation (ReconciliationService) keeps these correct; the assignment
    # engine must never depend on these being perfectly accurate.
    current_case_count = Column(Integer, nullable=True, default=0)
    current_task_count = Column(Integer, nullable=True, default=0)
    # Scheduled return-from-leave date (nullable); auto_expire_leave() uses this.
    leave_ends_on = Column(Date, nullable=True)
    capability_version = Column(Integer, nullable=True, default=1)  # Optimistic lock for capability edits



class POI(Base):
    __tablename__ = "pois"
    poi_id = Column(String, primary_key=True)
    name = Column(String)
    poi_type = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    address = Column(Text)
    category = Column(String)
    geometry = Column(Text)
    risk_factor = Column(Float)
    opening_hours = Column(String)
    footfall_score = Column(Float)
    __table_args__ = (*_latlng_checks(),)


class CCTVCamera(Base):
    __tablename__ = "cctv_cameras"
    camera_id = Column(String, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True)
    camera_type = Column(String)
    resolution = Column(String)
    coverage_radius = Column(Float)
    orientation = Column(Float)
    field_of_view = Column(Float)
    installation_height = Column(Float)
    day_night = Column(String)
    operational_status = Column(String)
    __table_args__ = (*_latlng_checks(),)


class ANPRCamera(Base):
    __tablename__ = "anpr_cameras"
    anpr_id = Column(String, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True)
    direction = Column(String)
    lanes = Column(Integer)
    capture_probability = Column(Float)
    ocr_accuracy = Column(Float)
    __table_args__ = (*_latlng_checks(),)


class CellTower(Base):
    __tablename__ = "cell_towers"
    tower_id = Column(String, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True)
    provider = Column(String)
    radius = Column(Float)
    operator = Column(String)
    sector_count = Column(Integer)
    coverage_polygon = Column(Text)
    __table_args__ = (*_latlng_checks(),)


# ── Population & assets ─────────────────────────────────────────────────────
class Person(Base):
    __tablename__ = "persons"
    # Existing columns (backward-compatible with API/analytics) --------------
    citizen_id = Column(String, primary_key=True, index=True)
    name_en = Column(String, index=True)
    gender = Column(String)
    age = Column(Integer)
    phone_primary = Column(String, index=True)
    occupation = Column(String)
    home_address = Column(Text)
    district_name = Column(String)
    is_migrant = Column(Boolean)
    # Extended columns -------------------------------------------------------
    name_kn = Column(String)
    first_name_en = Column(String)
    last_name_en = Column(String)
    dob = Column(Date)
    aadhaar = Column(String)
    dl_number = Column(String)
    phone_secondary = Column(String)
    socioeconomic_class = Column(String)
    religion = Column(String)
    caste = Column(String)
    education = Column(String)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    taluk = Column(String)
    station_id = Column(String, index=True)  # soft ref (station may be sparse)
    home_lat = Column(Float)
    home_lng = Column(Float)
    bank_account = Column(String)
    upi_id = Column(String)


class Vehicle(Base):
    __tablename__ = "vehicles"
    vehicle_id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("persons.citizen_id"), index=True)
    license_plate = Column(String, index=True)
    make = Column(String)
    model = Column(String)
    color = Column(String)
    is_stolen = Column(Boolean)
    # Extended
    type = Column(String)
    registration_year = Column(Integer)


class Phone(Base):
    __tablename__ = "phones"
    phone_id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("persons.citizen_id"), index=True)
    phone_number = Column(String, index=True)
    provider = Column(String)
    type = Column(String)
    is_burner = Column(Boolean)
    activation_date = Column(Date)  # Phone number activation/issuance date


# ── Criminal network (circular FK resolved via use_alter) ───────────────────
class Criminal(Base):
    __tablename__ = "criminals"
    criminal_id = Column(String, primary_key=True, index=True)
    citizen_id = Column(String, ForeignKey("persons.citizen_id"), index=True)
    name_en = Column(String, index=True)
    name_kn = Column(String)
    alias_names = Column(Text)
    age = Column(Integer)
    gender = Column(String)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    district_name = Column(String)
    station_id = Column(String, index=True)
    home_lat = Column(Float)
    home_lng = Column(Float)
    risk_level = Column(String, index=True)
    expertise = Column(String)
    preferred_crime_types = Column(Text)
    operating_radius_km = Column(Float)
    recidivism_probability = Column(Float)
    career_stage = Column(String)
    is_gang_member = Column(Boolean)
    # Soft reference (not a hard FK): criminals<->gangs form a cycle
    # (gang_id here, leader_criminal_id on gangs). Per-batch commits can't
    # satisfy a hard constraint in either load order, so integrity is
    # enforced by the validation pipeline instead. Indexed for join speed.
    gang_id = Column(String, index=True)
    is_gang_leader = Column(Boolean)
    known_associates = Column(Text)  # exploded into criminal_associates junction
    total_crimes_committed = Column(Integer)
    total_arrests = Column(Integer)
    is_currently_active = Column(Boolean)
    is_currently_arrested = Column(Boolean)
    mo_entry_method = Column(String)
    mo_time_slot = Column(String)
    mo_target_type = Column(String)
    mo_escape_vehicle = Column(String)
    mo_weapon = Column(String)
    mo_stolen_property = Column(String)
    mo_num_offenders = Column(Integer)
    mo_operates_at_night = Column(Boolean)


class Gang(Base):
    __tablename__ = "gangs"
    gang_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    specialization = Column(String)
    # Soft reference — see Criminal.gang_id note on the circular dependency.
    leader_criminal_id = Column(String, index=True)
    member_criminal_ids = Column(Text)  # exploded into gang_members junction
    territory_district_ids = Column(Text)
    territory_district_names = Column(Text)
    preferred_time_slot = Column(String)
    escape_vehicle_type = Column(String)
    communication_method = Column(String)
    num_members = Column(Integer)
    threat_level = Column(String, index=True)
    financial_links = Column(Text)
    is_interstate = Column(Boolean)
    total_crimes_attributed = Column(Integer)
    is_active = Column(Boolean)
    formation_year = Column(Integer)


class Campaign(Base):
    __tablename__ = "campaigns"
    campaign_id = Column(String, primary_key=True, index=True)
    gang_id = Column(String, ForeignKey("gangs.gang_id"), index=True)
    crime_category = Column(String, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    num_crimes_planned = Column(Integer)
    num_crimes_committed = Column(Integer)
    status = Column(String)
    target_district_id = Column(String, ForeignKey("districts.district_id"), index=True)


class Mastermind(Base):
    __tablename__ = "masterminds"
    mastermind_id = Column(String, primary_key=True, index=True)
    citizen_id = Column(String, index=True)  # soft ref (may be unidentified)
    name_en = Column(String)
    alias = Column(String)
    wealth_level = Column(String)
    controlled_gang_ids = Column(Text)
    front_business = Column(String)


# ── FIR (central fact) ──────────────────────────────────────────────────────
class FIR(Base):
    __tablename__ = "firs"
    # Existing columns (backward-compatible) ---------------------------------
    fir_id = Column(String, primary_key=True, index=True)
    fir_number = Column(String, index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), index=True)
    district_name = Column(String)
    occurred_date = Column(Date, index=True)
    occurred_time = Column(Time)  # Hour:minute:second precision (default 12:00:00 if unknown)
    occurred_datetime = Column(DateTime, index=True)  # Combined for chronological ordering
    crime_type = Column(String, index=True)
    crime_category = Column(String, index=True)
    status = Column(String, index=True)
    description_en = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    # Extended columns -------------------------------------------------------
    event_id = Column(String, index=True)
    district_id = Column(String, ForeignKey("districts.district_id"), index=True)
    reported_date = Column(Date)
    ipc_sections = Column(String)
    severity = Column(Integer, index=True)
    description_kn = Column(Text)
    complainant_name = Column(String)
    complainant_phone = Column(String)
    complainant_address = Column(Text)
    estimated_loss_inr = Column(Numeric)
    num_accused = Column(Integer)
    num_victims = Column(Integer)
    num_witnesses = Column(Integer)
    is_gang_crime = Column(Boolean, index=True)
    season = Column(String)
    # Soft references (optional / may point to unidentified entities) --------
    campaign_id = Column(String, index=True)
    nearest_poi_id = Column(String, index=True)
    investigating_officer_id = Column(String, index=True)
    sho_officer_id = Column(String, index=True)
    gang_id = Column(String, index=True)
    festival_context = Column(String)
    primary_criminal_id = Column(String, index=True)
    __table_args__ = (
        *_latlng_checks(),
        Index("ix_firs_filter_sort", "crime_category", "status", "occurred_date"),
        Index("ix_firs_occurred_date_district", "occurred_date", "district_id"),
    )


# ── Case children (hard FK -> firs) ─────────────────────────────────────────
class Victim(Base):
    __tablename__ = "victims"
    victim_id = Column(String, primary_key=True)
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    name_en = Column(String)
    gender = Column(String)
    age = Column(Integer)
    phone = Column(String)
    address = Column(Text)
    injury_type = Column(String)
    property_lost = Column(String)
    loss_amount_inr = Column(Numeric)
    citizen_id = Column(String, index=True)  # soft ref (victim may be non-registered)


class Accused(Base):
    __tablename__ = "accused"
    accused_id = Column(String, primary_key=True)
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    criminal_id = Column(String, index=True)  # soft ref (unknown accused -> NULL)
    name_en = Column(String)
    name_kn = Column(String)
    age = Column(Integer)
    gender = Column(String)
    address = Column(Text)
    is_known = Column(Boolean)
    is_arrested = Column(Boolean)
    role = Column(String)


class Evidence(Base):
    __tablename__ = "evidence"
    evidence_id = Column(String, primary_key=True)
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    evidence_type = Column(String, index=True)
    description = Column(Text)
    collection_date = Column(Date)
    collection_officer_id = Column(String, index=True)
    collection_location = Column(String)
    condition = Column(String)
    is_forensic = Column(Boolean)
    forensic_report_id = Column(String)
    lab_name = Column(String)
    lab_received_date = Column(Date)
    lab_result = Column(Text)
    is_recovered_property = Column(Boolean)
    estimated_value_inr = Column(Numeric)
    tags = Column(Text)


class InvestigationLog(Base):
    __tablename__ = "investigation_logs"
    log_id = Column(String, primary_key=True)
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    event_type = Column(String, index=True)
    timestamp = Column(String)  # ISO datetime text
    officer_id = Column(String, index=True)
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(String)
    __table_args__ = (*_latlng_checks(),)


class ModusOperandi(Base):
    __tablename__ = "modus_operandi"
    crime_event_id = Column(String, primary_key=True)
    criminal_id = Column(String, index=True)  # soft ref
    entry_method = Column(String)
    time_slot = Column(String)
    target_type = Column(String)
    escape_vehicle = Column(String)
    weapon = Column(String)
    stolen_property = Column(String)
    num_offenders = Column(Integer)
    operates_at_night = Column(Boolean)
    is_solo = Column(Boolean)
    uses_vehicle_escape = Column(Boolean)
    is_violent = Column(Boolean)


class Chargesheet(Base):
    __tablename__ = "chargesheets"
    chargesheet_id = Column(String, primary_key=True)
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    filed_date = Column(Date)
    filing_officer_id = Column(String, index=True)
    court_name = Column(String)
    court_case_number = Column(String)
    ipc_sections = Column(String)
    num_accused_charged = Column(Integer)
    accused_ids = Column(Text)
    status = Column(String)
    next_hearing_date = Column(Date)


class Arrest(Base):
    __tablename__ = "arrests"
    arrest_id = Column(String, primary_key=True)
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    accused_id = Column(String, index=True)  # soft ref
    criminal_id = Column(String, index=True)
    accused_name = Column(String)
    arresting_officer_id = Column(String, index=True)
    arrest_date = Column(Date)
    arrest_location = Column(String)
    district_id = Column(String, index=True)
    station_id = Column(String, index=True)
    arrest_type = Column(String)
    is_juvenile = Column(Boolean)
    remand_days = Column(Integer)
    bail_granted = Column(Boolean)
    bail_date = Column(Date)
    bail_amount_inr = Column(Numeric)
    bail_court = Column(String)
    is_convicted = Column(Boolean)
    conviction_date = Column(Date)
    sentence = Column(String)


class CourtCase(Base):
    __tablename__ = "court_cases"
    case_id = Column(String, primary_key=True)
    chargesheet_id = Column(String, index=True)  # soft ref
    fir_id = Column(String, ForeignKey("firs.fir_id"), index=True)
    court_name = Column(String)
    judge_name = Column(String)
    filing_date = Column(Date)
    verdict_date = Column(Date)
    verdict = Column(String)
    sentence_type = Column(String)
    sentence_months = Column(Integer)
    fine_amount_inr = Column(Numeric)


# ── Telemetry (Postgres-only; soft refs due to scheme mismatch/polymorphism) ─
class CCTVLog(Base):
    __tablename__ = "cctv_logs"
    log_id = Column(String, primary_key=True)
    camera_id = Column(String, index=True)
    timestamp = Column(String)
    vehicle_id = Column(String, index=True)
    person_id = Column(String, index=True)  # holds CRM- (criminal) ids
    confidence = Column(Float)


class CCTVEvent(Base):
    __tablename__ = "cctv_events"
    cctv_event_id = Column(String, primary_key=True)
    camera_id = Column(String, index=True)  # different scheme than cctv_cameras
    camera_type = Column(String)
    camera_owner = Column(String)
    location_description = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    district_id = Column(String, index=True)
    station_id = Column(String, index=True)
    event_timestamp = Column(String)
    vehicle_plate_captured = Column(String)
    vehicle_type = Column(String)
    vehicle_color = Column(String)
    person_silhouette_class = Column(String)
    num_persons_captured = Column(Integer)
    linked_fir_id = Column(String, index=True)
    is_primary_evidence = Column(Boolean)
    footage_available = Column(Boolean)
    footage_quality = Column(String)
    __table_args__ = (*_latlng_checks(),)


class ANPRLog(Base):
    __tablename__ = "anpr_logs"
    log_id = Column(String, primary_key=True)
    anpr_id = Column(String, index=True)
    vehicle_id = Column(String, index=True)
    plate_read = Column(String, index=True)
    timestamp = Column(String)
    speed_kmh = Column(Float)


class CDR(Base):
    __tablename__ = "cdrs"
    cdr_id = Column(String, primary_key=True)
    caller_phone_id = Column(String, index=True)   # raw phone number, not PHN- id
    receiver_phone_id = Column(String, index=True)
    timestamp = Column(String)
    duration_seconds = Column(Integer)
    cell_tower_lat = Column(Float)
    cell_tower_lng = Column(Float)
    call_type = Column(String)


class CellTowerPing(Base):
    __tablename__ = "cell_tower_pings"
    ping_id = Column(String, primary_key=True)
    phone_id = Column(String, index=True)
    tower_id = Column(String, index=True)
    timestamp = Column(String)
    signal_strength = Column(Float)


class VehicleGPS(Base):
    __tablename__ = "vehicle_gps"
    gps_id = Column(String, primary_key=True)
    vehicle_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(String)
    speed_kmh = Column(Float)
    __table_args__ = (*_latlng_checks(),)


class PatrolLog(Base):
    __tablename__ = "patrol_logs"
    log_id = Column(String, primary_key=True)
    patrol_date = Column(Date, index=True)
    station_id = Column(String, index=True)
    district_id = Column(String, index=True)
    district_name = Column(String)
    officer_id = Column(String, index=True)
    officer_rank = Column(String)
    vehicle_type = Column(String)
    vehicle_reg = Column(String)
    shift = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    area_covered_km = Column(Float)
    beat_area = Column(String)
    checkpost_count = Column(Integer)
    vehicles_checked = Column(Integer)
    persons_checked = Column(Integer)
    incidents_observed = Column(Integer)
    incident_notes = Column(Text)
    patrol_type = Column(String)


# ── Intelligence & misc (Postgres-only) ─────────────────────────────────────
class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    transaction_id = Column(String, primary_key=True)
    sender_id = Column(String, index=True)     # polymorphic: FENCE-*, CRM-*
    receiver_id = Column(String, index=True)
    amount_inr = Column(Numeric)
    timestamp = Column(String)
    transaction_type = Column(String)
    linked_campaign_id = Column(String, index=True)
    notes = Column(Text)


class IntelligenceTip(Base):
    __tablename__ = "intelligence_tips"
    tip_id = Column(String, primary_key=True)
    source_type = Column(String)
    timestamp = Column(String)
    district_id = Column(String, index=True)
    station_id = Column(String, index=True)
    target_criminal_id = Column(String, index=True)
    target_gang_id = Column(String, index=True)
    linked_campaign_id = Column(String, index=True)
    confidence_score = Column(Float)
    description = Column(Text)


class Informant(Base):
    __tablename__ = "informants"
    informant_id = Column(String, primary_key=True)
    citizen_id = Column(String, index=True)
    primary_station_id = Column(String, index=True)
    true_reliability_score = Column(Float)
    category = Column(String)
    status = Column(String)


class SocialTie(Base):
    __tablename__ = "social_network"
    tie_id = Column(Integer, primary_key=True, autoincrement=True)  # synthetic PK (no natural key)
    source_id = Column(String, index=True)   # polymorphic
    target_id = Column(String, index=True)
    relationship_type = Column(String)
    strength = Column(Float)
    start_year = Column(Integer)


class EntityResolution(Base):
    __tablename__ = "entity_resolution"
    er_id = Column(Integer, primary_key=True, autoincrement=True)  # synthetic PK
    canonical_id = Column(String, index=True)
    canonical_name = Column(String)
    alias_id = Column(String, index=True)
    alias_value = Column(String)
    alias_type = Column(String)
    confidence = Column(Float)
    source_module = Column(String)


# ── Junction tables (expanded from pipe-delimited list columns) ─────────────
class GangMember(Base):
    __tablename__ = "gang_members"
    gang_id = Column(String, ForeignKey("gangs.gang_id"), primary_key=True)
    criminal_id = Column(String, primary_key=True, index=True)


class CriminalAssociate(Base):
    __tablename__ = "criminal_associates"
    criminal_id = Column(String, ForeignKey("criminals.criminal_id"), primary_key=True)
    associate_id = Column(String, primary_key=True, index=True)


class FIRAccomplice(Base):
    __tablename__ = "fir_accomplices"
    fir_id = Column(String, ForeignKey("firs.fir_id"), primary_key=True)
    criminal_id = Column(String, primary_key=True, index=True)


class FIRVehicle(Base):
    __tablename__ = "fir_vehicles"
    fir_id = Column(String, ForeignKey("firs.fir_id"), primary_key=True)
    vehicle_id = Column(String, primary_key=True, index=True)


class FIRPhone(Base):
    __tablename__ = "fir_phones"
    fir_id = Column(String, ForeignKey("firs.fir_id"), primary_key=True)
    phone_id = Column(String, primary_key=True, index=True)


# ── Investigations ────────────────────────────────────────────────────────────
class Investigation(Base):
    __tablename__ = 'investigations'
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    created_by = Column(String)
    assigned_officer = Column(String)
    owner_id = Column(String, ForeignKey('users.id'))
    assigned_team = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1, nullable=False)
    last_sequence = Column(Integer, default=0, nullable=False)

class InvestigationEntity(Base):
    __tablename__ = 'investigation_entities'
    investigation_id = Column(String, ForeignKey('investigations.id'), primary_key=True)
    entity_type = Column(String, primary_key=True)
    entity_id = Column(String, primary_key=True)
    added_at = Column(DateTime, default=func.now())

class InvestigationNote(Base):
    __tablename__ = 'investigation_notes'
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey('investigations.id'))
    author = Column(String)
    markdown = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1, nullable=False)

class InvestigationActivity(Base):
    __tablename__ = 'investigation_activities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String, ForeignKey('investigations.id'))
    action = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=func.now())

from sqlalchemy import JSON
class EventRecord(Base):
    __tablename__ = 'events'
    event_id = Column(String, primary_key=True)
    event_type = Column(String, index=True)
    payload = Column(JSON)
    timestamp = Column(DateTime, default=func.now(), index=True)
    processed = Column(Boolean, default=False)
    case_id = Column(String, index=True, nullable=True)
    user_id = Column(String, nullable=True)
    sequence = Column(Integer, index=True, nullable=True)

class InvestigationCollaborator(Base):
    __tablename__ = 'investigation_collaborators'
    investigation_id = Column(String, ForeignKey('investigations.id'), primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    added_at = Column(DateTime, default=func.now())

class BackgroundJob(Base):
    __tablename__ = 'background_jobs'
    id = Column(String, primary_key=True)
    task_name = Column(String, index=True)
    payload = Column(JSON)
    state = Column(String, default="QUEUED", index=True)
    attempts = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# ── Phase 7: Analytical Intelligence ─────────────────────────────────────────
class GraphMetric(Base):
    """Stores pre-computed graph analytics scores per entity."""
    __tablename__ = 'graph_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, index=True)
    entity_type = Column(String, index=True)
    metric_name = Column(String, index=True)   # pagerank, betweenness, community_id, etc.
    score = Column(Float, nullable=True)
    community_id = Column(String, nullable=True, index=True)
    algorithm = Column(String)
    computed_at = Column(DateTime, default=func.now(), index=True)
    __table_args__ = (
        Index("ix_graph_metrics_entity_metric", "entity_id", "metric_name"),
    )

class IntelligenceEventLog(Base):
    """Audit trail of all intelligence shown to analysts."""
    __tablename__ = 'intelligence_event_logs'

    event_id = Column(String, primary_key=True, index=True)
    workspace_id = Column(String, index=True)  # Soft ref to investigations.id
    event_type = Column(String, index=True)  # SERIES_DETECTED, LINK_FOUND, ANOMALY, etc.
    entity_id = Column(String, index=True)
    confidence_score = Column(Float)
    explanation_json = Column(JSON)  # Full IntelligenceExplanation
    shown_at = Column(DateTime, default=func.now(), index=True)
    analyst_id = Column(String, nullable=True)


# ── Phase 8.1: Operational Task Engine ───────────────────────────────────────
import enum as py_enum

class TaskStatus(str, py_enum.Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class TaskCategory(str, py_enum.Enum):
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    INTERVIEW = "INTERVIEW"
    WARRANT = "WARRANT"
    EXTERNAL_COORDINATION = "EXTERNAL_COORDINATION"
    ANALYSIS = "ANALYSIS"
    FIELD_OPERATION = "FIELD_OPERATION"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class TaskPriority(str, py_enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SLAState(str, py_enum.Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    BREACHED = "BREACHED"


class DependencyType(str, py_enum.Enum):
    FINISH_TO_START = "FINISH_TO_START"  # Task B cannot start until Task A completes
    START_TO_START = "START_TO_START"    # Task B cannot start until Task A starts


class TaskTemplate(Base):
    """Template defining the task workflow for a case type."""
    __tablename__ = 'task_templates'

    id = Column(String, primary_key=True)
    name = Column(String, index=True)  # e.g., "Murder Investigation"
    case_type = Column(String, index=True)  # e.g., MURDER, ROBBERY, MISSING_PERSON
    description = Column(Text)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1)


class TemplateTask(Base):
    """Defines a single task within a template."""
    __tablename__ = 'template_tasks'

    id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey('task_templates.id'), index=True)
    order = Column(Integer)  # Execution order within template
    title = Column(String)
    description = Column(Text)
    category = Column(Enum(TaskCategory))
    priority = Column(Enum(TaskPriority))
    sla_hours = Column(Integer, nullable=True)  # Expected duration in hours
    is_recurring = Column(Boolean, default=False)
    recurrence_interval_hours = Column(Integer, nullable=True)  # Hours between recurrences
    created_at = Column(DateTime, default=func.now())


class TemplateTaskDependency(Base):
    """Defines dependencies between tasks within a template."""
    __tablename__ = 'template_task_dependencies'

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('template_tasks.id'), index=True)
    depends_on_task_id = Column(String, ForeignKey('template_tasks.id'), index=True)
    dependency_type = Column(Enum(DependencyType), default=DependencyType.FINISH_TO_START)
    created_at = Column(DateTime, default=func.now())


class InvestigationTask(Base):
    """Individual task instance within an investigation."""
    __tablename__ = 'investigation_tasks'

    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey('investigations.id', ondelete='CASCADE'), index=True)
    template_task_id = Column(String, index=True, nullable=True)  # Soft ref to TemplateTask
    parent_task_id = Column(String, ForeignKey('investigation_tasks.id', ondelete='CASCADE'), index=True, nullable=True)

    title = Column(String)
    description = Column(Text)
    category = Column(Enum(TaskCategory))
    priority = Column(Enum(TaskPriority))
    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED)

    assigned_officer_id = Column(String, index=True, nullable=True)  # Soft ref to users.id

    created_at = Column(DateTime, default=func.now(), index=True)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True, index=True)

    # SLA Tracking with pause support (Finding 8 fix)
    sla_hours = Column(Integer, nullable=True)
    sla_state = Column(Enum(SLAState), default=SLAState.NORMAL)
    sla_escalated = Column(Boolean, default=False)
    blocked_at = Column(DateTime, nullable=True)  # When task entered BLOCKED state
    total_blocked_seconds = Column(Integer, default=0)  # Accumulated block time

    is_recurring = Column(Boolean, default=False)
    recurrence_interval_hours = Column(Integer, nullable=True)
    next_recurrence_at = Column(DateTime, nullable=True)

    version = Column(Integer, default=1)

    __table_args__ = (
        Index("ix_investigation_tasks_status", "investigation_id", "status"),
        Index("ix_investigation_tasks_officer", "assigned_officer_id", "status"),
        Index("ix_investigation_tasks_due", "investigation_id", "due_at"),
    )


class TaskDependency(Base):
    """Defines dependencies between actual task instances."""
    __tablename__ = 'task_dependencies'

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('investigation_tasks.id'), index=True)
    depends_on_task_id = Column(String, ForeignKey('investigation_tasks.id'), index=True)
    dependency_type = Column(Enum(DependencyType), default=DependencyType.FINISH_TO_START)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_task_dependencies_task", "task_id", "depends_on_task_id"),
    )
    dismissed_at = Column(DateTime, nullable=True)

class EntityMergeProposal(Base):
    """Pending entity merge proposals awaiting investigator approval."""
    __tablename__ = 'entity_merge_proposals'
    proposal_id = Column(String, primary_key=True, index=True)
    primary_entity_id = Column(String, index=True)
    merge_entity_id = Column(String, index=True)
    entity_type = Column(String)  # PERSON, VEHICLE, etc.
    match_score = Column(Float)
    confidence_overall = Column(Float)
    explanation_json = Column(JSON)  # Full IntelligenceExplanation
    status = Column(String, default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    created_by = Column(String)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    approved_by = Column(String, nullable=True)
    approval_notes = Column(Text, nullable=True)

class CrimeSeries(Base):
    """Persisted crime series discovered by the CrimeSeriesEngine."""
    __tablename__ = 'crime_series'
    series_id = Column(String, primary_key=True)
    fir_ids = Column(JSON)                     # List of FIR IDs in series
    characteristics = Column(JSON)
    emerging_trend_score = Column(Float)
    confidence_overall = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ── Phase 8.2: Assignment & Workload Management ──────────────────────────────

class AvailabilityStatus(str, py_enum.Enum):
    """Officer duty availability. Governs whether new work may be assigned."""
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"
    BREAK = "BREAK"
    FIELD = "FIELD"          # On field duty — critical assignments only (policy)
    LEAVE = "LEAVE"
    TRAINING = "TRAINING"    # No new assignments unless explicitly overridden
    SUSPENDED = "SUSPENDED"  # Cannot self-transition; admin/supervisor only


class OfficerRank(str, py_enum.Enum):
    """Standardized rank ladder (subset; extend via migration as needed)."""
    CONSTABLE = "CONSTABLE"
    HEAD_CONSTABLE = "HEAD_CONSTABLE"
    ASI = "ASI"                       # Assistant Sub-Inspector
    SI = "SI"                         # Sub-Inspector
    INSPECTOR = "INSPECTOR"
    DSP = "DSP"                       # Deputy Superintendent
    SP = "SP"                         # Superintendent
    DIG = "DIG"
    IG = "IG"


class SkillCode(str, py_enum.Enum):
    """Fixed, enumerated skill catalog. New skills added via migration only.

    Rationale: standardized certification, deterministic scoring, consistent
    analytics, no spelling variants, RBAC-compatible.
    """
    CYBER_FORENSICS = "CYBER_FORENSICS"
    DIGITAL_EVIDENCE = "DIGITAL_EVIDENCE"
    HOMICIDE = "HOMICIDE"
    ROBBERY = "ROBBERY"
    NARCOTICS = "NARCOTICS"
    MISSING_PERSONS = "MISSING_PERSONS"
    FINANCIAL_CRIME = "FINANCIAL_CRIME"
    FRAUD = "FRAUD"
    TRAFFICKING = "TRAFFICKING"
    ORGANIZED_CRIME = "ORGANIZED_CRIME"
    TERRORISM = "TERRORISM"
    FORENSICS = "FORENSICS"
    BALLISTICS = "BALLISTICS"
    DNA = "DNA"
    INTERVIEWING = "INTERVIEWING"
    SURVEILLANCE = "SURVEILLANCE"
    OSINT = "OSINT"
    NEGOTIATION = "NEGOTIATION"
    LANGUAGE_HINDI = "LANGUAGE_HINDI"
    LANGUAGE_KANNADA = "LANGUAGE_KANNADA"
    LANGUAGE_MARATHI = "LANGUAGE_MARATHI"


class Specialization(str, py_enum.Enum):
    """Investigator specialization categories (align with case categories)."""
    CYBER_CRIME = "CYBER_CRIME"
    FINANCIAL_CRIME = "FINANCIAL_CRIME"
    NARCOTICS = "NARCOTICS"
    ORGANIZED_CRIME = "ORGANIZED_CRIME"
    MISSING_PERSONS = "MISSING_PERSONS"
    WOMEN_AND_CHILD = "WOMEN_AND_CHILD"
    HOMICIDE = "HOMICIDE"
    FORENSICS = "FORENSICS"


class CertificationStatus(str, py_enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUSPENDED = "SUSPENDED"


class BurnoutRisk(str, py_enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OfficerSkill(Base):
    """Officer ↔ Skill assignment (from the fixed SkillCode catalog)."""
    __tablename__ = "officer_skills"
    officer_id = Column(String, ForeignKey("officers.officer_id", ondelete="CASCADE"),
                        primary_key=True)
    skill_code = Column(Enum(SkillCode), primary_key=True)
    proficiency = Column(Integer, default=3)  # 1–5 scale
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_officer_skills_skill", "skill_code"),
    )


class OfficerSpecialization(Base):
    """Officer ↔ Specialization assignment."""
    __tablename__ = "officer_specializations"
    officer_id = Column(String, ForeignKey("officers.officer_id", ondelete="CASCADE"),
                        primary_key=True)
    specialization = Column(Enum(Specialization), primary_key=True)
    is_primary = Column(Boolean, default=False)  # An officer has one primary specialization
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_officer_specializations_spec", "specialization"),
    )


class OfficerCertification(Base):
    """Officer certification with validity window and issuing authority.

    Assignment rules (enforced in OfficerCapacityService / scoring engine):
      - mandatory certification expired/revoked → reject assignment
      - preferred certification expired → scoring penalty (not rejection)
    """
    __tablename__ = "officer_certifications"
    id = Column(String, primary_key=True)
    officer_id = Column(String, ForeignKey("officers.officer_id", ondelete="CASCADE"),
                        index=True)
    name = Column(String, index=True)             # e.g., "Certified Cyber Forensics Examiner"
    skill_code = Column(Enum(SkillCode), nullable=True, index=True)  # Optional link to a skill
    certificate_number = Column(String, nullable=True)
    issuing_authority = Column(String, nullable=True)
    issued_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    status = Column(Enum(CertificationStatus), default=CertificationStatus.ACTIVE, index=True)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_officer_certifications_officer_status", "officer_id", "status"),
    )


class OfficerAvailabilityLog(Base):
    """Audit trail of every availability_status transition."""
    __tablename__ = "officer_availability_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    officer_id = Column(String, ForeignKey("officers.officer_id", ondelete="CASCADE"),
                        index=True)
    from_status = Column(String, nullable=True)
    to_status = Column(String)
    reason = Column(Text, nullable=True)
    actor_id = Column(String, nullable=True)  # User who performed the transition
    created_at = Column(DateTime, default=func.now(), index=True)


class OfficerWorkloadReconciliation(Base):
    """Records mismatches between cached counters and DB-derived truth."""
    __tablename__ = "officer_workload_reconciliation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    officer_id = Column(String, ForeignKey("officers.officer_id", ondelete="CASCADE"),
                        index=True)
    field = Column(String)                 # 'current_case_count' | 'current_task_count'
    cached_value = Column(Integer)
    actual_value = Column(Integer)
    correction_applied = Column(Boolean, default=True)
    reconciled_at = Column(DateTime, default=func.now(), index=True)


class AssignmentRecord(Base):
    """Immutable record of a supervisor-approved (or overridden) assignment.

    Persists the full AssignmentScore that justified the recommendation, plus
    override metadata. This is the audit + explainability backbone consumed by
    Phase 8.3 and future LLM explanations.
    """
    __tablename__ = "assignment_records"
    id = Column(String, primary_key=True)
    investigation_id = Column(String, index=True)
    officer_id = Column(String, index=True)
    recommended_officer_id = Column(String, nullable=True)  # What the engine suggested
    was_override = Column(Boolean, default=False, index=True)  # True if supervisor chose different
    overall_score = Column(Float, nullable=True)
    component_scores = Column(JSON, nullable=True)  # Full breakdown
    explanation = Column(JSON, nullable=True)       # List[str] human-readable reasons
    override_reason = Column(Text, nullable=True)
    supervisor_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        Index("ix_assignment_records_officer_created", "officer_id", "created_at"),
    )


