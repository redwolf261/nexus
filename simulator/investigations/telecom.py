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

from simulator.schemas.population import Citizen

def generate_telecom_data(
    crime_events: List[CrimeEvent],
    criminals: List[CriminalProfile],
    citizens: List[Citizen],
    rng: np.random.Generator
) -> List[CallDetailRecord]:
    """
    Generate rich, highly connected CDR networks.
    Mixes crime coordination calls with massive background citizen noise.
    """
    cdrs: List[CallDetailRecord] = []
    
    # Extract available phones
    criminal_phones = []
    for c in criminals:
        criminal_phones.extend(c.phone_ids)
        
    citizen_phones = []
    for c in citizens:
        if c.phone_primary:
            citizen_phones.append(c.phone_primary)
        if getattr(c, 'phone_secondary', None):
            citizen_phones.append(c.phone_secondary)
        
    if not criminal_phones or not citizen_phones:
        return []
        
    all_phones = np.array(criminal_phones + citizen_phones)
    
    # 1. Background Noise (Citizen-to-Citizen, Citizen-to-Criminal)
    # Generate ~2 calls per phone randomly distributed over the simulation dates
    # To find date range:
    if crime_events:
        start_date = min(e.occurred_date for e in crime_events)
        end_date = max(e.occurred_date for e in crime_events)
    else:
        start_date = datetime.now().date()
        end_date = start_date
        
    days = (end_date - start_date).days
    if days < 1:
        days = 1
        
    total_noise_calls = len(all_phones) * 2
    
    # Fast vectorized sampling
    callers = rng.choice(all_phones, size=total_noise_calls)
    receivers = rng.choice(all_phones, size=total_noise_calls)
    
    # Filter out self-calls
    valid_mask = callers != receivers
    callers = callers[valid_mask]
    receivers = receivers[valid_mask]
    total_noise_calls = len(callers)
    
    # Sample random timestamps
    random_days = rng.integers(0, days + 1, size=total_noise_calls)
    random_seconds = rng.integers(0, 86400, size=total_noise_calls)
    durations = rng.integers(10, 1200, size=total_noise_calls)
    
    # Vectorized array to lists for fast instantiation
    callers_list = callers.tolist()
    receivers_list = receivers.tolist()
    random_days_list = random_days.tolist()
    random_seconds_list = random_seconds.tolist()
    durations_list = durations.tolist()
    
    start_dt = datetime.combine(start_date, datetime.min.time())
    
    # Pre-generate random coordinates within Karnataka bounds (~ 12 to 18 lat, 74 to 78 lng)
    # This is a bit coarse but works for noise
    lats = rng.uniform(12.0, 18.0, size=total_noise_calls).round(5)
    lngs = rng.uniform(74.0, 78.0, size=total_noise_calls).round(5)
    
    for i in range(total_noise_calls):
        call_time = start_dt + timedelta(days=random_days_list[i], seconds=random_seconds_list[i])
        cdrs.append(CallDetailRecord(
            cdr_id=f"CDR-N-{i:08d}",
            caller_phone_id=callers_list[i],
            receiver_phone_id=receivers_list[i],
            timestamp=call_time,
            duration_seconds=durations_list[i],
            cell_tower_lat=lats[i],
            cell_tower_lng=lngs[i],
            call_type="voice"
        ))
        
    # 2. Crime Spikes (Criminal-to-Criminal coordination)
    crim_map: Dict[str, CriminalProfile] = {c.criminal_id: c for c in criminals}
    
    for event in crime_events:
        if not event.primary_criminal_id or not event.accomplice_criminal_ids:
            continue
            
        primary = crim_map.get(event.primary_criminal_id)
        if not primary or not primary.phone_ids:
            continue
            
        primary_phone = rng.choice(primary.phone_ids)
        
        # Multiple calls per accomplice before the crime
        for accomplice_id in event.accomplice_criminal_ids:
            acc = crim_map.get(accomplice_id)
            if not acc or not acc.phone_ids:
                continue
                
            acc_phone = rng.choice(acc.phone_ids)
            
            # Spike: 3-5 calls in the 24 hours preceding the event
            num_pre_calls = rng.integers(3, 6)
            for _ in range(num_pre_calls):
                call_time = datetime.combine(event.occurred_date, event.occurred_time) - timedelta(minutes=int(rng.integers(10, 1440)))
                # Alternate caller
                caller, receiver = (primary_phone, acc_phone) if rng.random() > 0.5 else (acc_phone, primary_phone)
                cdrs.append(CallDetailRecord(
                    cdr_id=f"CDR-C-{len(cdrs):08d}",
                    caller_phone_id=caller,
                    receiver_phone_id=receiver,
                    timestamp=call_time,
                    duration_seconds=int(rng.integers(20, 600)),
                    cell_tower_lat=round(event.latitude + rng.uniform(-0.02, 0.02), 5),
                    cell_tower_lng=round(event.longitude + rng.uniform(-0.02, 0.02), 5),
                    call_type="voice"
                ))
                
            # Post-crime escape coordination
            num_post_calls = rng.integers(1, 3)
            for _ in range(num_post_calls):
                call_time = datetime.combine(event.occurred_date, event.occurred_time) + timedelta(minutes=int(rng.integers(5, 120)))
                caller, receiver = (primary_phone, acc_phone) if rng.random() > 0.5 else (acc_phone, primary_phone)
                cdrs.append(CallDetailRecord(
                    cdr_id=f"CDR-C-{len(cdrs):08d}",
                    caller_phone_id=caller,
                    receiver_phone_id=receiver,
                    timestamp=call_time,
                    duration_seconds=int(rng.integers(10, 180)),
                    cell_tower_lat=round(event.latitude + rng.uniform(-0.05, 0.05), 5),
                    cell_tower_lng=round(event.longitude + rng.uniform(-0.05, 0.05), 5),
                    call_type="voice"
                ))

    # Sort chronologically
    cdrs.sort(key=lambda x: x.timestamp)
    
    return cdrs
