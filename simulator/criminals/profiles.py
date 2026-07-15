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
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from simulator.config.constants import (
    CRIME_CATEGORIES, MO_ENTRY_METHODS, MO_TIME_SLOTS,
    MO_TARGET_TYPES, MO_ESCAPE_VEHICLES, MO_WEAPONS,
    MO_STOLEN_PROPERTY, MO_NUM_OFFENDERS, GANG_SPECIALIZATIONS,
)
from simulator.population.citizens import Citizen


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


@dataclass
class MoTemplate:
    """Structured Modus Operandi fingerprint for a criminal."""
    entry_method: str
    preferred_time_slot: str
    target_type: str
    escape_vehicle: str
    weapon: str
    stolen_property: str
    typical_num_offenders: int
    uses_accomplices: bool
    operates_at_night: bool

    def to_dict(self) -> dict:
        return {
            "entry_method": self.entry_method,
            "preferred_time_slot": self.preferred_time_slot,
            "target_type": self.target_type,
            "escape_vehicle": self.escape_vehicle,
            "weapon": self.weapon,
            "stolen_property": self.stolen_property,
            "typical_num_offenders": self.typical_num_offenders,
            "uses_accomplices": self.uses_accomplices,
            "operates_at_night": self.operates_at_night,
        }


@dataclass
class CriminalProfile:
    criminal_id: str
    citizen_id: str
    name_en: str
    name_kn: str
    age: int
    gender: str
    district_id: str
    district_name: str
    station_id: str
    home_lat: float
    home_lng: float
    risk_level: str
    expertise: str              # property | violent | fraud | narcotics | opportunistic
    preferred_crime_types: List[str]
    operating_radius_km: float
    modus_operandi: MoTemplate
    recidivism_probability: float
    career_stage: str
    is_gang_member: bool = False
    gang_id: Optional[str] = None
    is_gang_leader: bool = False
    vehicle_ids: List[str] = field(default_factory=list)
    phone_ids: List[str] = field(default_factory=list)
    known_associates: List[str] = field(default_factory=list)   # criminal_ids
    alias_names: List[str] = field(default_factory=list)
    total_crimes_committed: int = 0
    total_arrests: int = 0
    is_currently_active: bool = True
    is_currently_arrested: bool = False


def _build_mo_template(rng: random.Random, expertise: str, risk_level: str) -> MoTemplate:
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
    rng: random.Random,
) -> List[CriminalProfile]:
    """
    Select a fraction of adult citizens to become criminals.
    Assign risk levels, expertise, MO templates, etc.
    """
    # Select eligible adults only (age 16+)
    eligible = [c for c in citizens if c.age >= 16]
    n_criminals = int(len(eligible) * criminal_fraction)
    selected = rng.sample(eligible, min(n_criminals, len(eligible)))

    profiles: List[CriminalProfile] = []

    for idx, citizen in enumerate(selected):
        risk = rng.choices(RISK_LEVELS, weights=[0.35, 0.35, 0.20, 0.10], k=1)[0]
        expertise = rng.choices(
            list(EXPERTISE_MAP.keys()),
            weights=[0.40, 0.25, 0.20, 0.08, 0.07],
            k=1,
        )[0]

        preferred_crimes = rng.sample(EXPERTISE_MAP[expertise], min(3, len(EXPERTISE_MAP[expertise])))

        # Operating radius depends on risk and crime type
        radius_map = {"low": 10, "medium": 30, "high": 80, "very_high": 200}
        base_radius = radius_map[risk]
        operating_radius = base_radius * rng.uniform(0.5, 1.5)

        recidivism_prob = {"low": 0.25, "medium": 0.45, "high": 0.65, "very_high": 0.80}[risk]

        career_stage = rng.choices(
            CAREER_STAGES,
            weights=[0.05, 0.15, 0.35, 0.25, 0.10, 0.05, 0.05],
            k=1,
        )[0]

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
            total_crimes_committed=rng.randint(0, {"low": 3, "medium": 8, "high": 20, "very_high": 50}[risk]),
        ))

    return profiles
