"""
NEXUS Simulator — Arrest Records & Chargesheets
Generates arrest records, bail records, and chargesheet filings
linked to FIRs and accused persons.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Dict

from simulator.crimes.fir import FIR, Accused


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
    arrest_type: str        # "preventive" | "warrant" | "suo_moto"
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
    status: str             # "filed" | "pending_trial" | "convicted" | "acquitted"
    next_hearing_date: Optional[date]


COURTS = [
    "Chief Judicial Magistrate Court", "Additional Sessions Court",
    "Fast Track Court", "District Sessions Court", "JMFC Court",
]

SENTENCES = [
    "3 months imprisonment", "6 months imprisonment", "1 year imprisonment",
    "2 years imprisonment", "5 years imprisonment", "7 years imprisonment",
    "Life imprisonment", "Fine of Rs. 5,000", "Fine of Rs. 10,000",
    "Rigorous imprisonment 3 years", "Rigorous imprisonment 7 years",
]


def generate_arrests(
    firs: List[FIR],
    officers_by_station: Dict[str, list],
    rng: random.Random,
) -> tuple[List[ArrestRecord], List[Chargesheet]]:
    """
    Generate arrest records for FIRs with known accused.
    ~30% of FIRs result in arrests.
    ~50% of arrests result in chargesheets.
    """
    arrests: List[ArrestRecord] = []
    chargesheets: List[Chargesheet] = []
    arrest_counter = 0
    cs_counter = 0

    for fir in firs:
        # Decide if arrests were made
        arrest_probability = 0.15 + (fir.severity * 0.05)  # More severe = more likely arrested
        if rng.random() > arrest_probability:
            continue

        # Arrests per FIR (1-3)
        num_arrests = rng.randint(1, min(3, fir.num_accused))
        fir_arrests: List[ArrestRecord] = []

        station_offs = officers_by_station.get(fir.station_id, [])
        arresting_off = rng.choice(station_offs).officer_id if station_offs else None

        for i in range(num_arrests):
            accused = fir.accused_list[i] if i < len(fir.accused_list) else None

            arrest_delay = rng.randint(0, 30)  # days after FIR
            arrest_date = fir.reported_date + timedelta(days=arrest_delay)

            remand_days = rng.randint(1, 15)
            bail_granted = rng.random() < 0.65
            bail_date = arrest_date + timedelta(days=rng.randint(7, 90)) if bail_granted else None
            bail_amount = rng.choice([10_000, 25_000, 50_000, 100_000, 200_000]) if bail_granted else 0.0

            is_convicted = (not bail_granted) and rng.random() < 0.30
            conviction_date = arrest_date + timedelta(days=rng.randint(180, 900)) if is_convicted else None

            district_code = fir.district_id.replace("KA-", "").replace("-", "")
            court = rng.choice(COURTS)

            arrest = ArrestRecord(
                arrest_id=f"ARR-{arrest_counter:07d}",
                fir_id=fir.fir_id,
                accused_id=accused.accused_id if accused else f"ACC-{fir.fir_id}-{i:03d}",
                criminal_id=accused.criminal_id if accused else None,
                accused_name=accused.name_en if accused else "Unknown",
                arresting_officer_id=arresting_off,
                arrest_date=arrest_date,
                arrest_location=f"Near {rng.choice(['Bus Stand', 'Market', 'Highway', 'Railway Station'])}, {fir.district_name}",
                district_id=fir.district_id,
                station_id=fir.station_id,
                arrest_type=rng.choice(["warrant", "suo_moto", "preventive"]),
                is_juvenile=rng.random() < 0.03,
                remand_days=remand_days,
                bail_granted=bail_granted,
                bail_date=bail_date,
                bail_amount_inr=bail_amount,
                bail_court=court if bail_granted else None,
                is_convicted=is_convicted,
                conviction_date=conviction_date,
                sentence=rng.choice(SENTENCES) if is_convicted else None,
            )
            arrests.append(arrest)
            fir_arrests.append(arrest)
            arrest_counter += 1

        # Chargesheet
        if fir_arrests and rng.random() < 0.55:
            cs_date = fir.reported_date + timedelta(days=rng.randint(30, 90))
            filing_off = arresting_off

            chargesheets.append(Chargesheet(
                chargesheet_id=f"CS-{cs_counter:07d}",
                fir_id=fir.fir_id,
                filed_date=cs_date,
                filing_officer_id=filing_off,
                court_name=rng.choice(COURTS),
                court_case_number=f"CC/{rng.randint(1, 9999)}/{fir.occurred_date.year}",
                ipc_sections=fir.ipc_sections,
                num_accused_charged=len(fir_arrests),
                accused_ids=[a.accused_id for a in fir_arrests],
                status=rng.choices(
                    ["filed", "pending_trial", "convicted", "acquitted"],
                    weights=[40, 35, 15, 10],
                    k=1,
                )[0],
                next_hearing_date=cs_date + timedelta(days=rng.randint(30, 180)),
            ))
            cs_counter += 1

    return arrests, chargesheets
