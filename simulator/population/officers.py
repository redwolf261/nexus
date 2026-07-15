"""
NEXUS Simulator — Police Officer Generator
Creates officers with:
  - Rank, badge number
  - Station assignment
  - Tenure, shift pattern
  - Specialization
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from simulator.config.constants import POLICE_RANKS, EN_MALE_FIRST_NAMES, EN_FEMALE_FIRST_NAMES, EN_SURNAMES
from simulator.geography.karnataka import Station


SHIFT_PATTERNS = ["morning_0600_1400", "afternoon_1400_2200", "night_2200_0600", "general_0900_1800"]

OFFICER_SPECIALIZATIONS = [
    "general", "cyber_crime", "narcotics", "traffic", "crime_branch",
    "sb_intelligence", "women_cell", "juvenile", "anti_corruption"
]


@dataclass
class Officer:
    officer_id: str
    badge_number: str
    name_en: str
    gender: str
    rank: str
    rank_level: int
    rank_abbr: str
    station_id: str
    district_id: str
    district_name: str
    phone: str
    doj: date                       # Date of joining
    tenure_years: int
    shift: str
    specialization: str
    is_investigating_officer: bool  # IO — handles FIR investigations
    is_station_house_officer: bool  # SHO — station head


def _badge(rng: random.Random, district_id: str, seq: int) -> str:
    code = district_id.replace("KA-", "").replace("-", "")
    return f"KSP/{code}/{seq:06d}"


def generate_officers(
    stations: List[Station],
    id_factory,
    rng: random.Random,
    officer_multiplier: float = 0.3,
) -> List[Officer]:
    """
    Generate officers for all stations.
    Each station gets officers according to its quota.
    """
    officers: List[Officer] = []
    officer_seq = 1

    # Rank distribution weights (more constables, fewer IOs)
    rank_weights = {
        "DGP": 0.001, "ADGP": 0.002, "IGP": 0.003, "DIG": 0.005,
        "SP": 0.01, "ASP": 0.01, "DSP": 0.02,
        "Inspector": 0.05, "Sub-Inspector": 0.10, "ASI": 0.10,
        "Head Constable": 0.25, "Constable": 0.44,
    }

    rank_meta = {r["rank"]: r for r in POLICE_RANKS}

    for station in stations:
        quota = max(4, int(station.officer_quota * officer_multiplier))
        sho_assigned = False

        for i in range(quota):
            gender = rng.choice(["M", "M", "M", "F"])  # ~25% female officers
            if gender == "M":
                first = rng.choice(EN_MALE_FIRST_NAMES)
            else:
                first = rng.choice(EN_FEMALE_FIRST_NAMES)
            last = rng.choice(EN_SURNAMES)
            name = f"{first} {last}"

            # Assign rank
            rank_name = rng.choices(
                list(rank_weights.keys()),
                weights=list(rank_weights.values()),
                k=1,
            )[0]
            rmeta = rank_meta[rank_name]

            # SHO is typically an Inspector or SI
            is_sho = (not sho_assigned) and rank_name in {"Inspector", "Sub-Inspector"}
            if is_sho:
                sho_assigned = True

            is_io = rank_name in {"Inspector", "Sub-Inspector", "ASI"}

            doj = date.today() - timedelta(days=rng.randint(365, 365 * 30))
            tenure = (date.today() - doj).days // 365

            officers.append(Officer(
                officer_id=f"OFF-{officer_seq:07d}",
                badge_number=_badge(rng, station.district_id, officer_seq),
                name_en=name,
                gender=gender,
                rank=rank_name,
                rank_level=rmeta["level"],
                rank_abbr=rmeta["abbr"],
                station_id=station.station_id,
                district_id=station.district_id,
                district_name=station.district_name,
                phone=id_factory.phone(),
                doj=doj,
                tenure_years=tenure,
                shift=rng.choice(SHIFT_PATTERNS),
                specialization=rng.choice(OFFICER_SPECIALIZATIONS),
                is_investigating_officer=is_io,
                is_station_house_officer=is_sho,
            ))
            officer_seq += 1

    return officers
