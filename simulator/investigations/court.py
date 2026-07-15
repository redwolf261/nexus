from __future__ import annotations
import numpy as np
from datetime import timedelta
from typing import List

from simulator.schemas.investigations import Chargesheet, CourtCase

def generate_court_cases(
    chargesheets: List[Chargesheet],
    rng: np.random.Generator
) -> List[CourtCase]:
    cases: List[CourtCase] = []
    
    for cs in chargesheets:
        # Not all chargesheets resolve within the simulation window, some remain pending.
        # Verdict is heavily weighted by the severity of the IPC sections, but we simplify here.
        
        is_pending = rng.random() < 0.4 # 40% of cases are still pending in court
        
        if is_pending:
            verdict = "PENDING"
            verdict_date = None
            sentence_type = None
            sentence_months = 0
            fine_amount = 0.0
        else:
            # Conviction rate ~ 60%
            is_convicted = rng.random() < 0.6
            verdict = "CONVICTION" if is_convicted else "ACQUITTAL"
            verdict_date = cs.filed_date + timedelta(days=int(rng.integers(90, 700)))
            
            if is_convicted:
                sentence_type = rng.choice(["PRISON", "FINE", "BOTH"])
                sentence_months = int(rng.integers(6, 120)) if sentence_type in ["PRISON", "BOTH"] else 0
                fine_amount = float(rng.integers(1000, 50000)) if sentence_type in ["FINE", "BOTH"] else 0.0
            else:
                sentence_type = None
                sentence_months = 0
                fine_amount = 0.0
                
        cases.append(CourtCase(
            case_id=f"CASE-{cs.chargesheet_id.split('-')[-1]}",
            chargesheet_id=cs.chargesheet_id,
            fir_id=cs.fir_id,
            court_name=cs.court_name,
            judge_name=f"Hon. Judge {rng.integers(1, 100)}",
            filing_date=cs.filed_date,
            verdict_date=verdict_date,
            verdict=verdict,
            sentence_type=sentence_type,
            sentence_months=sentence_months,
            fine_amount_inr=fine_amount
        ))
        
    return cases
