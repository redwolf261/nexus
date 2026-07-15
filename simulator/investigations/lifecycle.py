"""
NEXUS Simulator — Investigation Lifecycle Generator
Creates chronological investigation logs (InvestigationLog) for FIRs.
"""
from __future__ import annotations
import numpy as np
from datetime import timedelta, datetime
from typing import List, Dict, Any

from simulator.crimes.fir import FIR
from simulator.schemas.investigations import Evidence, ArrestRecord, Chargesheet, InvestigationLog

def generate_investigation_logs(
    firs: List[FIR],
    evidence_list: List[Evidence],
    arrests: List[ArrestRecord],
    chargesheets: List[Chargesheet],
    rng: np.random.Generator
) -> List[InvestigationLog]:
    logs: List[InvestigationLog] = []
    
    # Organize records by fir_id
    evidence_by_fir: Dict[str, List[Evidence]] = {}
    for e in evidence_list:
        evidence_by_fir.setdefault(e.fir_id, []).append(e)
        
    arrests_by_fir: Dict[str, List[ArrestRecord]] = {}
    for a in arrests:
        arrests_by_fir.setdefault(a.fir_id, []).append(a)
        
    chargesheets_by_fir: Dict[str, List[Chargesheet]] = {}
    for c in chargesheets:
        chargesheets_by_fir.setdefault(c.fir_id, []).append(c)

    log_counter = 0
    
    # Sort FIRs by reported date to process chronologically
    firs_sorted = sorted(firs, key=lambda f: f.reported_date)
    
    # Track open cases per officer: officer_id -> list of close_dates
    active_cases: Dict[str, List[datetime]] = {}

    for fir in firs_sorted:
        fir_dt = datetime.combine(fir.reported_date, datetime.min.time()) + timedelta(hours=int(rng.integers(8, 20)))
        
        # 1. FIR Filed
        logs.append(InvestigationLog(
            log_id=f"ILOG-{log_counter:08d}",
            fir_id=fir.fir_id,
            event_type="FIR_FILED",
            timestamp=fir_dt,
            officer_id=fir.sho_officer_id,
            description=f"FIR {fir.fir_number} registered at {fir.station_id}"
        ))
        log_counter += 1
        
        # 2. Officer Assigned
        assigned_dt = fir_dt + timedelta(hours=int(rng.integers(1, 24)))
        io_id = fir.investigating_officer_id
        
        # Calculate Workload at assignment time
        workload = 0
        if io_id:
            # clean up closed cases
            active_cases.setdefault(io_id, [])
            active_cases[io_id] = [dt for dt in active_cases[io_id] if dt > assigned_dt]
            workload = len(active_cases[io_id])
            
        delay_multiplier = 1.0
        if workload > 15:
            delay_multiplier = rng.uniform(2.0, 4.0) # Massive delay if overloaded
            
        logs.append(InvestigationLog(
            log_id=f"ILOG-{log_counter:08d}",
            fir_id=fir.fir_id,
            event_type="OFFICER_ASSIGNED",
            timestamp=assigned_dt,
            officer_id=io_id,
            description=f"Officer {io_id} assigned as IO (Current Load: {workload} cases)"
        ))
        log_counter += 1
        
        # 3. Evidence
        for ev in evidence_by_fir.get(fir.fir_id, []):
            hours_delay = int(rng.integers(9, 18) * delay_multiplier)
            ev_dt = datetime.combine(ev.collection_date, datetime.min.time()) + timedelta(hours=hours_delay)
            logs.append(InvestigationLog(
                log_id=f"ILOG-{log_counter:08d}",
                fir_id=fir.fir_id,
                event_type="EVIDENCE_COLLECTED",
                timestamp=ev_dt,
                officer_id=ev.collection_officer_id or fir.investigating_officer_id,
                description=f"Evidence {ev.evidence_id} collected: {ev.description}"
            ))
            log_counter += 1
            
        # 4. Suspect Identified (synthetic event before arrest)
        arrs = arrests_by_fir.get(fir.fir_id, [])
        for arr in arrs:
            days_delay = int(rng.integers(1, 5) * delay_multiplier)
            ident_dt = datetime.combine(arr.arrest_date, datetime.min.time()) - timedelta(days=days_delay)
            # ensure ident_dt is after FIR assigned
            if ident_dt < assigned_dt:
                ident_dt = assigned_dt + timedelta(hours=12)
            
            logs.append(InvestigationLog(
                log_id=f"ILOG-{log_counter:08d}",
                fir_id=fir.fir_id,
                event_type="SUSPECT_IDENTIFIED",
                timestamp=ident_dt,
                officer_id=fir.investigating_officer_id,
                description=f"Suspect {arr.accused_name} identified through investigation"
            ))
            log_counter += 1
            
            # 5. Arrest
            arr_dt = datetime.combine(arr.arrest_date, datetime.min.time()) + timedelta(hours=int(rng.integers(6, 22)))
            logs.append(InvestigationLog(
                log_id=f"ILOG-{log_counter:08d}",
                fir_id=fir.fir_id,
                event_type="ARREST",
                timestamp=arr_dt,
                officer_id=arr.arresting_officer_id or fir.investigating_officer_id,
                description=f"Accused {arr.accused_name} arrested at {arr.arrest_location}"
            ))
            log_counter += 1
            
        # 6. Chargesheet
        for cs in chargesheets_by_fir.get(fir.fir_id, []):
            cs_dt = datetime.combine(cs.filed_date, datetime.min.time()) + timedelta(hours=10)
            logs.append(InvestigationLog(
                log_id=f"ILOG-{log_counter:08d}",
                fir_id=fir.fir_id,
                event_type="CHARGESHEET",
                timestamp=cs_dt,
                officer_id=cs.filing_officer_id or fir.investigating_officer_id,
                description=f"Chargesheet filed against {cs.num_accused_charged} accused"
            ))
            log_counter += 1
            
        # 7. Closed
        close_dt = fir_dt + timedelta(days=int(rng.integers(180, 400) * delay_multiplier))
        if fir.status == "closed" or fir.status == "convicted" or fir.status == "acquitted":
            logs.append(InvestigationLog(
                log_id=f"ILOG-{log_counter:08d}",
                fir_id=fir.fir_id,
                event_type="CLOSED",
                timestamp=close_dt,
                officer_id=fir.investigating_officer_id,
                description=f"Case closed with status: {fir.status}"
            ))
            log_counter += 1
            
        if io_id:
            active_cases[io_id].append(close_dt)

    # Sort logs by timestamp
    logs.sort(key=lambda x: x.timestamp)
    return logs
