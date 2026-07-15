"""
NEXUS Simulator — Citizen Generator
Creates N citizens with:
  - Full name (English + Kannada)
  - Age, gender, DOB
  - Home address (district/taluk-aware)
  - Aadhaar (fake), DL (fake)
  - Occupation, socioeconomic class
  - Phone(s)
  - Linked station (nearest station to home)
"""
from __future__ import annotations
import numpy as np
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

from simulator.config.constants import (
    EN_MALE_FIRST_NAMES, EN_FEMALE_FIRST_NAMES, EN_SURNAMES,
    KN_MALE_FIRST_NAMES, KN_FEMALE_FIRST_NAMES, KN_SURNAMES,
)
from simulator.geography.karnataka import Station
from simulator.population.identifiers import IdentifierFactory
from simulator.schemas.population import Citizen
from simulator.schemas.population import Citizen
from simulator.schemas.population import Citizen


OCCUPATIONS = [
    "Farmer", "Daily Wage Labourer", "Auto Driver", "Shop Keeper",
    "Government Employee", "Private Employee", "Teacher", "Business Person",
    "Student", "Homemaker", "Driver", "Mechanic", "Electrician",
    "Contractor", "Advocate", "Doctor", "Engineer", "Tailor",
    "Vendor", "Security Guard", "Retired", "Unemployed"
]

SOCIOECONOMIC_CLASSES = ["BPL", "lower", "lower_middle", "middle", "upper_middle", "upper"]

RELIGIONS = ["Hindu", "Muslim", "Christian", "Jain", "Buddhist", "Sikh", "Other"]

CASTES = [
    "SC", "ST", "OBC", "General", "Vokkaliga", "Lingayat", "Brahmin",
    "Kuruba", "Bovi", "Nayaka", "Others"
]

EDUCATION_LEVELS = [
    "Illiterate", "Primary", "High School", "PUC", "Diploma",
    "Graduate", "Post Graduate", "Professional"
]




def _random_dob(rng: np.random.Generator, min_age: int = 16, max_age: int = 75) -> date:
    today = date.today()
    age_days = int(rng.integers(min_age * 365, max_age * 365 + 1))
    return today - timedelta(days=age_days)


def generate_citizens(
    n: int,
    stations: List[Station],
    id_factory: IdentifierFactory,
    rng: np.random.Generator,
) -> List[Citizen]:
    """Generate N citizens distributed across stations proportional to population."""
    citizens: List[Citizen] = []

    # Build weighted station pool
    weights = [s.population_served for s in stations]
    total_weight = sum(weights)

    for i in range(n):
        # Pick station proportional to population
        r = rng.uniform(0, total_weight)
        cumulative = 0.0
        station = stations[-1]
        for s, w in zip(stations, weights):
            cumulative += w
            if r <= cumulative:
                station = s
                break

        gender = rng.choice(["M", "F", "M", "M", "F"])  # slight male bias

        if gender == "M":
            first_en = rng.choice(EN_MALE_FIRST_NAMES)
            first_kn = rng.choice(KN_MALE_FIRST_NAMES)
        else:
            first_en = rng.choice(EN_FEMALE_FIRST_NAMES)
            first_kn = rng.choice(KN_FEMALE_FIRST_NAMES)

        last_en = rng.choice(EN_SURNAMES)
        last_kn = rng.choice(KN_SURNAMES)
        name_en = f"{first_en} {last_en}"
        name_kn = f"{first_kn} {last_kn}"

        dob = _random_dob(rng, 15, 75)
        age = (date.today() - dob).days // 365

        has_dl = age >= 18 and rng.random() < 0.55
        has_secondary = rng.random() < 0.35
        has_bank = rng.random() < 0.70

        phone_primary = id_factory.phone()
        phone_secondary = id_factory.phone() if has_secondary else None
        dl = id_factory.dl_number() if has_dl else None
        aadhaar = id_factory.aadhaar()
        bank_acc = id_factory.bank_account() if has_bank else None
        upi = id_factory.upi_id(name_en, phone_primary) if has_bank and rng.random() < 0.6 else None

        home_lat = round(station.latitude  + rng.uniform(-0.04, 0.04), 6)
        home_lng = round(station.longitude + rng.uniform(-0.04, 0.04), 6)
        home_address = (
            f"No. {int(rng.integers(1, 500 + 1))}, "
            f"{rng.choice(['Main Road', 'Cross Street', '1st Stage', 'Layout', 'Colony', 'Nagar'])}, "
            f"{station.taluk}, {station.district_name} - {int(rng.integers(560000, 597000 + 1))}"
        )

        is_migrant = rng.random() < 0.08

        citizens.append(Citizen(
            citizen_id=f"CIT-{i:08d}",
            name_en=name_en,
            name_kn=name_kn,
            first_name_en=first_en,
            last_name_en=last_en,
            gender=gender,
            dob=dob,
            age=age,
            aadhaar=aadhaar,
            dl_number=dl,
            phone_primary=phone_primary,
            phone_secondary=phone_secondary,
            occupation=rng.choice(OCCUPATIONS),
            socioeconomic_class=rng.choice(SOCIOECONOMIC_CLASSES),
            religion=rng.choice(RELIGIONS),
            caste=rng.choice(CASTES),
            education=rng.choice(EDUCATION_LEVELS),
            district_id=station.district_id,
            district_name=station.district_name,
            taluk=station.taluk,
            station_id=station.station_id,
            home_lat=home_lat,
            home_lng=home_lng,
            home_address=home_address,
            bank_account=bank_acc,
            upi_id=upi,
            is_migrant=is_migrant,
        ))

    return citizens