"""
NEXUS Simulator — Crime Event Generator
Assembles raw crime events from:
  - Criminal profile (who commits)
  - Calendar context (when / risk level)
  - Location (where)
  - Victim selection (who is victimized)
  - MO fingerprint (how)
Each crime event is a rich dict that will be assembled into FIRs, evidence, etc.
"""
from __future__ import annotations
import random
import uuid
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import List, Optional, Dict, Any

from simulator.config.constants import CRIME_CATEGORIES, MO_TIME_SLOTS
from simulator.crimes.categories import CRIME_CATEGORY_MAP, get_crime_duration_minutes
from simulator.crimes.modus_operandi import MoFingerprint, generate_mo_fingerprint
from simulator.criminals.profiles import CriminalProfile
from simulator.geography.karnataka import Station
from simulator.geography.coordinates import Coordinate, CoordinateSampler
from simulator.timeline.calendar import DayContext


# Crime type probability weights for random crime (when no criminal drives)
CRIME_TYPE_BASE_WEIGHTS = {
    "THEFT":     20,
    "BURGLARY":  12,
    "ROBBERY":   6,
    "DACOITY":   2,
    "CHAIN":     10,
    "VEH_THEFT": 10,
    "PICK":      5,
    "TRESPASS":  4,
    "ARSON":     2,
    "ASSAULT":   8,
    "MURDER":    1,
    "ATTEMPT_M": 2,
    "KIDNAP":    1,
    "RIOTING":   2,
    "FRAUD":     6,
    "CYBER":     5,
    "ATM_FRAUD": 3,
    "NARCOTICS": 3,
    "POSSESS":   2,
    "HIT_RUN":   3,
    "DRUNK_DRV": 4,
}

# Time slot → hour range
TIME_SLOT_HOURS: Dict[str, tuple] = {
    "early_morning_0400_0600": (4, 6),
    "morning_0600_0900":       (6, 9),
    "mid_morning_0900_1200":   (9, 12),
    "afternoon_1200_1600":     (12, 16),
    "evening_1600_1900":       (16, 19),
    "night_1900_2200":         (19, 22),
    "late_night_2200_0400":    (22, 27),  # 27 = 3:00 AM next day
}


@dataclass
class CrimeEvent:
    """Raw crime event — the fundamental unit of simulation output."""
    event_id: str
    crime_type: str                 # e.g. "BURGLARY"
    crime_category: str             # e.g. "property"
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
    station_id: str                 # Nearest station (jurisdiction)
    primary_criminal_id: Optional[str]
    accomplice_criminal_ids: List[str]
    gang_id: Optional[str]
    victim_citizen_ids: List[str]
    witness_citizen_ids: List[str]
    vehicle_ids_involved: List[str]
    phone_ids_involved: List[str]
    modus_operandi: MoFingerprint
    estimated_loss_inr: float
    day_context: str                # season
    festival_context: Optional[str]
    is_gang_crime: bool
    fir_registered: bool = False    # Updated when FIR is created
    fir_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def _pick_crime_type(
    rng: random.Random,
    day_ctx: DayContext,
    criminal: Optional[CriminalProfile] = None,
) -> str:
    """Select a crime type weighted by criminal expertise + day risk multipliers."""
    weights = dict(CRIME_TYPE_BASE_WEIGHTS)

    # Apply criminal expertise bias
    if criminal:
        for crime_type in criminal.preferred_crime_types:
            if crime_type in weights:
                weights[crime_type] *= 3.0

    # Apply daily risk multipliers
    for crime_type, mult in day_ctx.crime_multipliers.items():
        if crime_type in weights:
            weights[crime_type] = weights[crime_type] * mult

    crime_types = list(weights.keys())
    crime_weights = [weights[ct] for ct in crime_types]
    return rng.choices(crime_types, weights=crime_weights, k=1)[0]


def _estimate_loss(crime_type: str, rng: random.Random) -> float:
    """Estimate financial loss for a crime."""
    loss_ranges = {
        "THEFT":     (500, 50_000),
        "BURGLARY":  (5_000, 500_000),
        "ROBBERY":   (1_000, 200_000),
        "DACOITY":   (10_000, 2_000_000),
        "CHAIN":     (5_000, 300_000),
        "VEH_THEFT": (20_000, 1_500_000),
        "PICK":      (200, 10_000),
        "TRESPASS":  (0, 1_000),
        "ARSON":     (10_000, 5_000_000),
        "ASSAULT":   (0, 50_000),       # medical expenses
        "MURDER":    (0, 0),
        "ATTEMPT_M": (0, 0),
        "KIDNAP":    (0, 2_000_000),    # ransom
        "RIOTING":   (1_000, 200_000),
        "FRAUD":     (10_000, 10_000_000),
        "CYBER":     (5_000, 5_000_000),
        "ATM_FRAUD": (5_000, 200_000),
        "NARCOTICS": (50_000, 50_000_000),
        "POSSESS":   (1_000, 100_000),
        "HIT_RUN":   (0, 100_000),
        "DRUNK_DRV": (0, 5_000),
    }
    lo, hi = loss_ranges.get(crime_type, (0, 10_000))
    if lo == hi == 0:
        return 0.0
    return round(rng.uniform(lo, hi), 2)


def _pick_crime_time(time_slot: str, rng: random.Random) -> time:
    """Convert time slot to a concrete time object."""
    h_min, h_max = TIME_SLOT_HOURS.get(time_slot, (8, 20))
    h_max = min(h_max, 23)
    h_min = max(h_min, 0)
    hour = rng.randint(h_min, h_max)
    minute = rng.randint(0, 59)
    return time(hour % 24, minute)


def generate_crime_events(
    day_ctx: DayContext,
    active_criminals: List[CriminalProfile],
    rng: random.Random,
    coord_sampler: CoordinateSampler,
    stations: List[Station],
    count: int,
    citizens_by_station: Optional[Dict[str, List]] = None,
    vehicles_by_criminal: Optional[Dict[str, List]] = None,
    phones_by_criminal: Optional[Dict[str, List]] = None,
) -> List[CrimeEvent]:
    """
    Generate `count` crime events for a given day.
    Called by the simulation engine per tick.
    """
    events: List[CrimeEvent] = []
    station_map: Dict[str, Station] = {s.station_id: s for s in stations}

    for _ in range(count):
        # Pick a criminal (70% driven by criminal, 30% opportunistic/unknown)
        if active_criminals and rng.random() < 0.70:
            criminal = rng.choice(active_criminals)
        else:
            criminal = None

        crime_type = _pick_crime_type(rng, day_ctx, criminal)
        cat_meta = CRIME_CATEGORY_MAP.get(crime_type, {})

        # Generate location
        if criminal:
            # Crime within operating radius of criminal's home
            coord, station = coord_sampler.sample_population_weighted(noise_pct=0.05)
            # Override with criminal's district-biased station
            district_stations = [s for s in stations if s.district_id == criminal.district_id]
            if district_stations and rng.random() < 0.65:
                nearby_station = rng.choice(district_stations)
                coord = coord_sampler.sample_near_station(
                    nearby_station,
                    radius_km=min(criminal.operating_radius_km, 50),
                    noise_pct=0.08,
                )
                station = nearby_station
        else:
            coord, station = coord_sampler.sample_population_weighted(noise_pct=0.10)

        # MO fingerprint
        mo = generate_mo_fingerprint(
            crime_event_id=f"EVT-{rng.randint(0, 99999999):08d}",
            rng=rng,
            criminal=criminal,
        )

        crime_time = _pick_crime_time(mo.time_slot, rng)
        duration = get_crime_duration_minutes(crime_type, rng)
        loss = _estimate_loss(crime_type, rng)

        # Victim count (1-3 typically)
        num_victims = rng.randint(1, 3 if cat_meta.get("severity", 1) <= 3 else 5)

        # Accomplices (from known associates if gang criminal)
        accomplice_ids: List[str] = []
        if criminal and criminal.is_gang_member and mo.num_offenders > 1:
            potential = criminal.known_associates[:mo.num_offenders - 1]
            accomplice_ids = potential[:min(len(potential), mo.num_offenders - 1)]

        # Vehicles and phones
        vehicle_ids: List[str] = []
        if vehicles_by_criminal and criminal and criminal.criminal_id in vehicles_by_criminal:
            vids = vehicles_by_criminal[criminal.criminal_id]
            if vids:
                vehicle_ids = [rng.choice(vids)]

        phone_ids: List[str] = []
        if phones_by_criminal and criminal and criminal.criminal_id in phones_by_criminal:
            pids = phones_by_criminal[criminal.criminal_id]
            if pids:
                phone_ids = [rng.choice(pids)]

        event_id = f"EVT-{len(events):08d}-{day_ctx.date.strftime('%Y%m%d')}"

        events.append(CrimeEvent(
            event_id=event_id,
            crime_type=crime_type,
            crime_category=cat_meta.get("category", "other"),
            ipc_section=cat_meta.get("ipc", "Unknown"),
            severity=cat_meta.get("severity", 1),
            occurred_date=day_ctx.date,
            occurred_time=crime_time,
            crime_duration_minutes=duration,
            latitude=coord.latitude,
            longitude=coord.longitude,
            location_accuracy_meters=coord.accuracy_meters,
            district_id=station.district_id,
            district_name=station.district_name,
            station_id=station.station_id,
            primary_criminal_id=criminal.criminal_id if criminal else None,
            accomplice_criminal_ids=accomplice_ids,
            gang_id=criminal.gang_id if criminal and criminal.is_gang_member else None,
            victim_citizen_ids=[f"VIC-{rng.randint(0, 9999999):07d}" for _ in range(num_victims)],
            witness_citizen_ids=[f"WIT-{rng.randint(0, 9999999):07d}" for _ in range(rng.randint(0, 2))],
            vehicle_ids_involved=vehicle_ids,
            phone_ids_involved=phone_ids,
            modus_operandi=mo,
            estimated_loss_inr=loss,
            day_context=day_ctx.season,
            festival_context=day_ctx.festival,
            is_gang_crime=criminal.is_gang_member if criminal else False,
        ))

    return events
