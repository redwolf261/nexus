"""
NEXUS Simulator — Telecom Generator
Generates Call Detail Records (CDRs) showing communication between entities,
especially gangs and associates coordinating crimes.
"""
from __future__ import annotations
import numpy as np
from typing import List, Dict, Optional
from datetime import timedelta, datetime

from simulator.schemas.investigations import CallDetailRecord
from simulator.schemas.crimes import CrimeEvent
from simulator.criminals.profiles import CriminalProfile

def generate_telecom_data(
    crime_events: List[CrimeEvent],
    criminals: List[CriminalProfile],
    rng: np.random.Generator
) -> List[CallDetailRecord]:
    """
    Generate CDRs. Criminals communicate before and after their crimes with their accomplices.
    """
    cdrs: List[CallDetailRecord] = []
    
    # Map criminals for easy phone lookup
    crim_map: Dict[str, CriminalProfile] = {c.criminal_id: c for c in criminals}
    
    for event in crime_events:
        if not event.primary_criminal_id or not event.accomplice_criminal_ids:
            continue
            
        primary = crim_map.get(event.primary_criminal_id)
        if not primary or not primary.phone_ids:
            continue
            
        primary_phone = rng.choice(primary.phone_ids)
        
        for accomplice_id in event.accomplice_criminal_ids:
            acc = crim_map.get(accomplice_id)
            if not acc or not acc.phone_ids:
                continue
                
            acc_phone = rng.choice(acc.phone_ids)
            
            # Generate a call before the crime (planning)
            if rng.random() < 0.7:
                call_time = datetime.combine(event.occurred_date, event.occurred_time) - timedelta(hours=int(rng.integers(1, 24)))
                cdrs.append(CallDetailRecord(
                    cdr_id=f"CDR-{len(cdrs):08d}",
                    caller_phone_id=primary_phone,
                    receiver_phone_id=acc_phone,
                    timestamp=call_time,
                    duration_seconds=int(rng.integers(15, 300)),
                    cell_tower_lat=round(event.latitude + rng.uniform(-0.02, 0.02), 5),
                    cell_tower_lng=round(event.longitude + rng.uniform(-0.02, 0.02), 5),
                    call_type="voice"
                ))
                
            # Generate a call after the crime (coordination/escape)
            if rng.random() < 0.8:
                call_time = datetime.combine(event.occurred_date, event.occurred_time) + timedelta(minutes=int(rng.integers(5, 60)))
                # Sometimes the accomplice calls the primary
                if rng.random() < 0.5:
                    caller, receiver = acc_phone, primary_phone
                else:
                    caller, receiver = primary_phone, acc_phone
                    
                cdrs.append(CallDetailRecord(
                    cdr_id=f"CDR-{len(cdrs):08d}",
                    caller_phone_id=caller,
                    receiver_phone_id=receiver,
                    timestamp=call_time,
                    duration_seconds=int(rng.integers(10, 120)),
                    cell_tower_lat=round(event.latitude + rng.uniform(-0.05, 0.05), 5),
                    cell_tower_lng=round(event.longitude + rng.uniform(-0.05, 0.05), 5),
                    call_type="voice"
                ))

    return cdrs
