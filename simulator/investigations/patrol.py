"""
NEXUS Simulator — Patrol Log Generator
Generates daily patrol logs for each station:
  - Officer, vehicle, route, shift
  - Area covered (km)
  - Incidents noted during patrol
  - Checkpost data
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import date, time
from typing import List, Optional, Dict

from simulator.config.constants import PATROL_VEHICLE_TYPES
from simulator.geography.karnataka import Station
from simulator.population.officers import Officer


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
    patrol_type: str        # "routine" | "nakabandi" | "flag_march" | "area_domination"


PATROL_AREAS = [
    "Market Area", "Residential Colony", "Industrial Zone", "Highway Patrol",
    "Border Checkpost", "Bus Stand Area", "Railway Station Area", "School Zone",
    "ATM Cluster", "Bank Street", "Old Town", "New Extension"
]

INCIDENT_NOTES_POOL = [
    "Suspicious vehicle noted and verified",
    "Traffic violation cases booked",
    "Drunk driving case detected",
    "Rowdy sheeter found at home, warned",
    "Checkpost conducted — no major violations",
    "Beat area surveyed — all clear",
    "Night patrol conducted in sensitive area",
    "Nakabandi conducted — 15 vehicles checked",
    "Intelligence-based patrol near ATM cluster",
    "Two-wheeler verification done",
    "Patrolled market area during night hours",
    "Anti-chain snatching patrol conducted",
]

PATROL_TYPES = ["routine", "nakabandi", "flag_march", "area_domination", "intelligence_based"]


def generate_patrol_logs(
    stations: List[Station],
    officers: List[Officer],
    sim_dates: List[date],
    id_factory,
    rng: random.Random,
    logs_per_station_per_day: int = 2,
) -> List[PatrolLog]:
    """
    Generate patrol logs for all stations over all simulation dates.
    Limits output to avoid excessive size.
    """
    all_logs: List[PatrolLog] = []
    log_counter = 0

    # Build officer lookup by station
    officers_by_station: Dict[str, List[Officer]] = {}
    for off in officers:
        officers_by_station.setdefault(off.station_id, []).append(off)

    # Sample dates to keep size manageable
    sample_dates = sim_dates[::3]  # every 3rd day

    for patrol_date in sample_dates:
        for station in stations:
            station_offs = officers_by_station.get(station.station_id, [])
            if not station_offs:
                continue

            for _ in range(min(logs_per_station_per_day, len(station_offs))):
                officer = rng.choice(station_offs)
                shift = officer.shift
                if "morning" in shift:
                    start_h, end_h = 6, 14
                elif "afternoon" in shift:
                    start_h, end_h = 14, 22
                elif "night" in shift:
                    start_h, end_h = 22, 6
                else:
                    start_h, end_h = 9, 18

                incidents = rng.randint(0, 4)
                notes = rng.choice(INCIDENT_NOTES_POOL) if incidents > 0 else "No significant incidents"

                vehicle_reg = id_factory.vehicle_registration()

                all_logs.append(PatrolLog(
                    log_id=f"PAT-{log_counter:08d}",
                    patrol_date=patrol_date,
                    station_id=station.station_id,
                    district_id=station.district_id,
                    district_name=station.district_name,
                    officer_id=officer.officer_id,
                    officer_rank=officer.rank,
                    vehicle_type=rng.choice(PATROL_VEHICLE_TYPES),
                    vehicle_reg=vehicle_reg,
                    shift=shift,
                    start_time=time(start_h % 24, rng.randint(0, 30)),
                    end_time=time(end_h % 24, rng.randint(0, 30)),
                    area_covered_km=round(rng.uniform(20, 150), 1),
                    beat_area=rng.choice(PATROL_AREAS),
                    checkpost_count=rng.randint(0, 5),
                    vehicles_checked=rng.randint(0, 80),
                    persons_checked=rng.randint(0, 50),
                    incidents_observed=incidents,
                    incident_notes=notes,
                    patrol_type=rng.choices(
                        PATROL_TYPES,
                        weights=[50, 20, 5, 15, 10],
                        k=1,
                    )[0],
                ))
                log_counter += 1

    return all_logs
