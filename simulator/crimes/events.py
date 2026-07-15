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
import numpy as np
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
from simulator.schemas.crimes import CrimeEvent


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




def _pick_crime_type(
    rng: np.random.Generator,
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
    crime_weights = np.array(crime_weights) / sum(crime_weights)
    return rng.choice(crime_types, p=crime_weights)


def _estimate_loss(crime_type: str, rng: np.random.Generator) -> float:
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


def _pick_crime_time(time_slot: str, rng: np.random.Generator) -> time:
    """Convert time slot to a concrete time object."""
    h_min, h_max = TIME_SLOT_HOURS.get(time_slot, (8, 20))
    h_max = min(h_max, 23)
    h_min = max(h_min, 0)
    hour = int(rng.integers(h_min, h_max + 1))
    minute = int(rng.integers(0, 59 + 1))
    return time(hour % 24, minute)


def generate_crime_events(
    day_ctx: DayContext,
    active_criminals: List[CriminalProfile],
    rng: np.random.Generator,
    coord_sampler: CoordinateSampler,
    stations: List[Station],
    count: int,
    citizens_by_station: Optional[Dict[str, List]] = None,
    vehicles_by_criminal: Optional[Dict[str, List]] = None,
    phones_by_criminal: Optional[Dict[str, List]] = None,
    campaigns: Optional[List[Any]] = None,
    pois: Optional[List[Any]] = None,
    active_surges: Optional[Dict[str, int]] = None,
) -> List[CrimeEvent]:
    """
    Generate `count` crime events for a given day.
    Called by the simulation engine per tick.
    """
    events: List[CrimeEvent] = []
    station_map: Dict[str, Station] = {s.station_id: s for s in stations}
    campaigns = campaigns or []
    
    # 1. Process Campaign Crimes First
    for camp in campaigns:
        # Find the criminal driving the campaign
        criminal = next((c for c in active_criminals if c.gang_id == camp.gang_id and c.is_gang_leader), None)
        if not criminal:
            continue
            
        crime_type = camp.crime_category
        cat_meta = CRIME_CATEGORY_MAP.get(crime_type, {})
        
        # All campaign crimes happen in the target district
        district_stations = [s for s in stations if s.district_id == camp.target_district_id]
        station = rng.choice(district_stations) if district_stations else rng.choice(stations)
        coord = coord_sampler.sample_near_station(station, radius_km=15, noise_pct=0.05)
        
        # MO fingerprint
        mo = generate_mo_fingerprint(
            crime_event_id=f"EVT-CAMP-{int(rng.integers(0, 99999999 + 1)):08d}",
            rng=rng,
            criminal=criminal,
        )

        crime_time = _pick_crime_time(mo.time_slot, rng)
        duration = get_crime_duration_minutes(crime_type, rng)
        loss = _estimate_loss(crime_type, rng)

        max_v = 3 if cat_meta.get("severity", 1) <= 3 else 5
        num_victims = int(rng.integers(1, max_v + 1))

        accomplice_ids: List[str] = []
        if criminal and criminal.is_gang_member and mo.num_offenders > 1:
            potential = criminal.known_associates[:mo.num_offenders - 1]
            accomplice_ids = potential[:min(len(potential), mo.num_offenders - 1)]

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

        nearest_poi_id = None
        if pois:
            # find nearest POI using simple euclidean
            min_dist = float('inf')
            for p in pois:
                if p.station_id == station.station_id or p.district_id == station.district_id:
                    d = (p.latitude - coord.latitude)**2 + (p.longitude - coord.longitude)**2
                    if d < min_dist:
                        min_dist = d
                        nearest_poi_id = p.poi_id

        event_id = f"EVT-{len(events):08d}-{day_ctx.date.strftime('%Y%m%d')}"

        events.append(CrimeEvent(
            event_id=event_id,
            campaign_id=camp.campaign_id,
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
            nearest_poi_id=nearest_poi_id,
            primary_criminal_id=criminal.criminal_id,
            accomplice_criminal_ids=accomplice_ids,
            gang_id=criminal.gang_id,
            victim_citizen_ids=[f"VIC-{int(rng.integers(0, 9999999 + 1)):07d}" for _ in range(num_victims)],
            witness_citizen_ids=[f"WIT-{int(rng.integers(0, 9999999 + 1)):07d}" for _ in range(int(rng.integers(0, 2 + 1)))],
            vehicle_ids_involved=vehicle_ids,
            phone_ids_involved=phone_ids,
            modus_operandi=mo,
            estimated_loss_inr=loss,
            day_context=day_ctx.season,
            festival_context=day_ctx.festival,
            is_gang_crime=True,
        ))
        camp.num_crimes_committed += 1
        count -= 1

    # 2. Process Random/Background Crimes
    if count < 0: count = 0
    active_surges = active_surges or {}
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
            
        # Police Patrol Surge Effect:
        # If the district is surging, the police presence is very high. 50% chance the crime is aborted.
        if station.district_id in active_surges:
            if rng.random() < 0.5:
                continue # Crime aborted due to patrol presence

        # MO Drift (Crime Evolution)
        if criminal and rng.random() < 0.05: # 5% chance of MO mutating
            drift_attr = rng.choice(["preferred_time_slot", "weapon", "escape_vehicle", "typical_num_offenders"])
            if drift_attr == "preferred_time_slot":
                criminal.modus_operandi.preferred_time_slot = rng.choice(["morning_0600_0900", "mid_morning_0900_1200", "afternoon_1200_1600", "evening_1600_1900", "late_night_2200_0400", "night_1900_2200", "early_morning_0400_0600"])
                criminal.modus_operandi.operates_at_night = criminal.modus_operandi.preferred_time_slot in ["late_night_2200_0400", "night_1900_2200", "early_morning_0400_0600"]
            elif drift_attr == "weapon":
                criminal.modus_operandi.weapon = rng.choice(["knife", "iron_rod", "bare_hands", "firearm", "country_bomb"])
            elif drift_attr == "escape_vehicle":
                criminal.modus_operandi.escape_vehicle = rng.choice(["motorcycle", "scooter", "car", "suv", "public_transit", "foot"])
            elif drift_attr == "typical_num_offenders":
                criminal.modus_operandi.typical_num_offenders = int(rng.integers(1, 5))
                criminal.modus_operandi.uses_accomplices = criminal.modus_operandi.typical_num_offenders > 1

        # MO fingerprint
        mo = generate_mo_fingerprint(
            crime_event_id=f"EVT-{int(rng.integers(0, 99999999 + 1)):08d}",
            rng=rng,
            criminal=criminal,
        )

        crime_time = _pick_crime_time(mo.time_slot, rng)
        duration = get_crime_duration_minutes(crime_type, rng)
        loss = _estimate_loss(crime_type, rng)

        # Victim count (1-3 typically)
        max_v = 3 if cat_meta.get("severity", 1) <= 3 else 5
        num_victims = int(rng.integers(1, max_v + 1))

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

        nearest_poi_id = None
        if pois:
            min_dist = float('inf')
            for p in pois:
                if p.station_id == station.station_id or p.district_id == station.district_id:
                    d = (p.latitude - coord.latitude)**2 + (p.longitude - coord.longitude)**2
                    if d < min_dist:
                        min_dist = d
                        nearest_poi_id = p.poi_id

        event_id = f"EVT-{len(events):08d}-{day_ctx.date.strftime('%Y%m%d')}"

        events.append(CrimeEvent(
            event_id=event_id,
            campaign_id=None,
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
            nearest_poi_id=nearest_poi_id,
            primary_criminal_id=criminal.criminal_id if criminal else None,
            accomplice_criminal_ids=accomplice_ids,
            gang_id=criminal.gang_id if criminal and criminal.is_gang_member else None,
            victim_citizen_ids=[f"VIC-{int(rng.integers(0, 9999999 + 1)):07d}" for _ in range(num_victims)],
            witness_citizen_ids=[f"WIT-{int(rng.integers(0, 9999999 + 1)):07d}" for _ in range(int(rng.integers(0, 2 + 1)))],
            vehicle_ids_involved=vehicle_ids,
            phone_ids_involved=phone_ids,
            modus_operandi=mo,
            estimated_loss_inr=loss,
            day_context=day_ctx.season,
            festival_context=day_ctx.festival,
            is_gang_crime=criminal.is_gang_member if criminal else False,
        ))

    return events