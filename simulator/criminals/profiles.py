"""
NEXUS Simulator — Criminal Profile Generator
Selects a fraction of citizens to become criminals and assigns them:
  - Risk level, expertise, preferred crime types
  - Operating hours, operating radius
  - MO template, recidivism probability
  - Career state (active/arrested/retired)
  - Vehicle + phone associations
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from simulator.config.constants import (
    CRIME_CATEGORIES, MO_ENTRY_METHODS, MO_TIME_SLOTS,
    MO_TARGET_TYPES, MO_ESCAPE_VEHICLES, MO_WEAPONS,
    MO_STOLEN_PROPERTY, MO_NUM_OFFENDERS, GANG_SPECIALIZATIONS,
)
from simulator.population.citizens import Citizen
from simulator.schemas.criminals import MoTemplate, CriminalProfile
from simulator.schemas.criminals import MoTemplate, CriminalProfile
from simulator.schemas.criminals import MoTemplate, CriminalProfile


RISK_LEVELS = ["low", "medium", "high", "very_high"]

# Criminal expertise is tied to crime category
EXPERTISE_MAP: Dict[str, List[str]] = {
    "property":  ["THEFT", "BURGLARY", "VEH_THEFT", "TRESPASS", "ARSON"],
    "violent":   ["ASSAULT", "ROBBERY", "DACOITY", "CHAIN", "RIOTING"],
    "fraud":     ["FRAUD", "CYBER", "ATM_FRAUD"],
    "narcotics": ["NARCOTICS", "POSSESS"],
    "opportunistic": ["THEFT", "PICK", "CHAIN", "DRUNK_DRV"],
}

CAREER_STAGES = ["juvenile", "emerging", "active", "experienced", "notorious", "retired", "arrested"]






def _build_mo_template(rng: np.random.Generator, expertise: str, risk_level: str) -> MoTemplate:
    """Build a consistent MO template for a given criminal expertise."""
    is_violent = expertise == "violent"
    is_fraud = expertise == "fraud"
    operates_at_night = rng.random() < (0.7 if expertise in {"property", "violent"} else 0.3)

    time_slot = rng.choice(
        ["late_night_2200_0400", "night_1900_2200", "early_morning_0400_0600"]
        if operates_at_night
        else ["morning_0600_0900", "mid_morning_0900_1200", "afternoon_1200_1600", "evening_1600_1900"]
    )

    weapon = rng.choice(["knife", "iron_rod", "bare_hands", "none"]) if is_violent else "none"
    if risk_level in {"high", "very_high"} and is_violent:
        weapon = rng.choice(["knife", "iron_rod", "country_bomb", "firearm"])

    typical_n = rng.choice(MO_NUM_OFFENDERS)

    return MoTemplate(
        entry_method=rng.choice(MO_ENTRY_METHODS if not is_fraud else ["digital_access", "social_engineering", "fake_police"]),
        preferred_time_slot=time_slot,
        target_type=rng.choice(MO_TARGET_TYPES),
        escape_vehicle=rng.choice(MO_ESCAPE_VEHICLES),
        weapon=weapon,
        stolen_property=rng.choice(MO_STOLEN_PROPERTY),
        typical_num_offenders=typical_n,
        uses_accomplices=typical_n > 1,
        operates_at_night=operates_at_night,
    )


def generate_criminal_profiles(
    citizens: List[Citizen],
    criminal_fraction: float,
    rng: np.random.Generator,
) -> List[CriminalProfile]:
    """
    Select a fraction of adult citizens to become criminals.
    Assign risk levels, expertise, MO templates, etc.
    """
    # Select eligible adults only (age 16+)
    eligible = [c for c in citizens if c.age >= 16]
    n_criminals = int(len(eligible) * criminal_fraction)
    selected = list(rng.choice(eligible, size=min(n_criminals, len(eligible)), replace=False))

    profiles: List[CriminalProfile] = []

    for idx, citizen in enumerate(selected):
        risk = rng.choice(RISK_LEVELS, p=[0.35, 0.35, 0.20, 0.10])
        expertise = rng.choice(
            list(EXPERTISE_MAP.keys()),
            p=[0.40, 0.25, 0.20, 0.08, 0.07]
        )

        preferred_crimes = list(rng.choice(EXPERTISE_MAP[expertise], size=min(3, len(EXPERTISE_MAP[expertise])), replace=False))

        # Operating radius depends on risk and crime type
        radius_map = {"low": 10, "medium": 30, "high": 80, "very_high": 200}
        base_radius = radius_map[risk]
        operating_radius = base_radius * rng.uniform(0.5, 1.5)

        recidivism_prob = {"low": 0.25, "medium": 0.45, "high": 0.65, "very_high": 0.80}[risk]

        career_stage = rng.choice(
            CAREER_STAGES,
            p=[0.05, 0.15, 0.35, 0.25, 0.10, 0.05, 0.05]
        )

        mo = _build_mo_template(rng, expertise, risk)

        profiles.append(CriminalProfile(
            criminal_id=f"CRM-{idx:07d}",
            citizen_id=citizen.citizen_id,
            name_en=citizen.name_en,
            name_kn=citizen.name_kn,
            age=citizen.age,
            gender=citizen.gender,
            district_id=citizen.district_id,
            district_name=citizen.district_name,
            station_id=citizen.station_id,
            home_lat=citizen.home_lat,
            home_lng=citizen.home_lng,
            risk_level=risk,
            expertise=expertise,
            preferred_crime_types=preferred_crimes,
            operating_radius_km=round(operating_radius, 1),
            modus_operandi=mo,
            recidivism_probability=round(recidivism_prob, 2),
            career_stage=career_stage,
            is_currently_active=career_stage not in {"retired", "arrested"},
            is_currently_arrested=career_stage == "arrested",
            total_crimes_committed=int(rng.integers(0, {"low": 3, "medium": 8, "high": 20, "very_high": 50}[risk] + 1)),
        ))

    return profiles