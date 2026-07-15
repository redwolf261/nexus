"""
NEXUS Simulator — CCTV Event Generator
Generates synthetic CCTV event metadata linked to crime locations:
  - Camera ID, location, timestamp
  - Vehicle plate captured
  - Person silhouette class
  - Linked FIR (if crime occurred nearby)
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from simulator.crimes.fir import FIR
from simulator.geography.karnataka import Station
from simulator.schemas.investigations import CCTVEvent


CAMERA_TYPES = ["dome", "bullet", "ptz", "traffic_enforcement", "atm_internal", "bodycam"]
CAMERA_OWNERS = ["BBMP", "Police Department", "Traffic Police", "Bank", "Private Business", "KSTDC"]
SILHOUETTE_CLASSES = ["male_adult", "female_adult", "juvenile", "group_2", "group_3plus", "unidentifiable"]
VEHICLE_COLORS = ["white", "black", "red", "blue", "silver", "grey", "green", "yellow", "orange"]




def generate_cctv_events(
    firs: List[FIR],
    stations: List[Station],
    id_factory,
    rng: np.random.Generator,
    coverage_fraction: float = 0.35,
) -> List[CCTVEvent]:
    """
    Generate CCTV events.
    ~35% of FIRs have a CCTV capture nearby.
    Additional background CCTV events (non-crime) also generated.
    """
    events: List[CCTVEvent] = []
    event_counter = 0

    station_map = {s.station_id: s for s in stations}

    # Crime-linked events
    for fir in firs:
        if rng.random() > coverage_fraction:
            continue

        station = station_map.get(fir.station_id)
        if not station:
            continue

        # 1-3 cameras caught something
        num_cameras = int(rng.integers(1, 3 + 1))
        for _ in range(num_cameras):
            has_vehicle = rng.random() < 0.60

            event_dt = datetime.combine(
                fir.occurred_date,
                time(int(rng.integers(0, 23 + 1)), int(rng.integers(0, 59 + 1))),
            )

            plate = id_factory.vehicle_registration() if has_vehicle else None
            vtype = rng.choice(["motorcycle", "car", "auto_rickshaw", "van"]) if has_vehicle else None
            vcolor = rng.choice(VEHICLE_COLORS) if has_vehicle else None

            events.append(CCTVEvent(
                cctv_event_id=f"CCTV-{event_counter:08d}",
                camera_id=f"CAM-{station.district_id}-{int(rng.integers(1000, 9999 + 1))}",
                camera_type=rng.choice(CAMERA_TYPES),
                camera_owner=rng.choice(CAMERA_OWNERS),
                location_description=f"Near crime scene, {station.taluk}, {station.district_name}",
                latitude=round(fir.latitude + rng.uniform(-0.002, 0.002), 6),
                longitude=round(fir.longitude + rng.uniform(-0.002, 0.002), 6),
                district_id=fir.district_id,
                station_id=fir.station_id,
                event_timestamp=event_dt,
                vehicle_plate_captured=plate,
                vehicle_type=vtype,
                vehicle_color=vcolor,
                person_silhouette_class=rng.choice(SILHOUETTE_CLASSES),
                num_persons_captured=int(rng.integers(1, 4 + 1)),
                linked_fir_id=fir.fir_id,
                is_primary_evidence=rng.random() < 0.40,
                footage_available=rng.random() < 0.70,
                footage_quality=rng.choice(
                    ["high_res", "medium_res", "low_res", "corrupted"],
                    p=[0.3, 0.45, 0.2, 0.05]
                ),
            ))
            event_counter += 1

    return events