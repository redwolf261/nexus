"""
NEXUS Simulator — Gang Generator
Creates organized crime groups with:
  - Leader, members, hierarchy
  - Territory (district list)
  - Crime specialization
  - Communication methods, financial links
  - Shared vehicles, preferred schedule
Gangs evolve over time — members can be arrested, new members recruited.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from simulator.config.constants import (
    GANG_SPECIALIZATIONS, KARNATAKA_DISTRICTS,
    MO_ESCAPE_VEHICLES, MO_TIME_SLOTS,
)
from simulator.criminals.profiles import CriminalProfile
from simulator.schemas.criminals import Gang
from simulator.schemas.criminals import Gang


COMMUNICATION_METHODS = [
    "mobile_phone", "encrypted_app", "physical_meetings", "code_words",
    "local_contacts", "hawala_network"
]

GANG_NAMES_PREFIX = [
    "Bengaluru", "Mysuru", "Coastal", "North Karnataka", "Deccan",
    "Border", "Highway", "District", "City", "Metro", "Rural", "Urban"
]
GANG_NAMES_SUFFIX = [
    "Gang", "Syndicate", "Network", "Group", "Crew", "Ring", "Cartel",
    "Cell", "Squad", "Faction"
]




def generate_gangs(
    criminals: List[CriminalProfile],
    num_gangs: int,
    rng: np.random.Generator,
    sim_start_year: int = 2021,
) -> List[Gang]:
    """
    Form num_gangs gangs from the criminal pool.
    Higher-risk criminals are preferentially selected as leaders.
    """
    gangs: List[Gang] = []

    # Sort criminals by risk for leader selection
    high_risk = [c for c in criminals if c.risk_level in {"high", "very_high"} and c.is_currently_active]
    medium_risk = [c for c in criminals if c.risk_level == "medium" and c.is_currently_active]
    available_pool = high_risk + medium_risk

    if len(available_pool) < num_gangs:
        available_pool = [c for c in criminals if c.is_currently_active]

    rng.shuffle(available_pool)
    assigned_to_gang: set = set()

    district_meta = {d["id"]: d["name"] for d in KARNATAKA_DISTRICTS}
    district_ids = [d["id"] for d in KARNATAKA_DISTRICTS]

    for gang_idx in range(min(num_gangs, len(available_pool))):
        # Pick a leader
        leader = None
        for candidate in available_pool:
            if candidate.criminal_id not in assigned_to_gang:
                leader = candidate
                break
        if leader is None:
            break

        # Gang size: 3–15 members
        target_size = int(rng.integers(3, 15 + 1))

        # Prefer criminals near the leader's district
        nearby = [
            c for c in available_pool
            if c.criminal_id != leader.criminal_id
            and c.criminal_id not in assigned_to_gang
            and c.district_id == leader.district_id
        ]
        far_candidates = [
            c for c in available_pool
            if c.criminal_id != leader.criminal_id
            and c.criminal_id not in assigned_to_gang
            and c.district_id != leader.district_id
        ]

        pool_for_gang = nearby[:target_size] + far_candidates[:max(0, target_size - len(nearby))]
        members = pool_for_gang[:target_size - 1]  # -1 for leader

        all_member_ids = [leader.criminal_id] + [m.criminal_id for m in members]
        for mid in all_member_ids:
            assigned_to_gang.add(mid)

        # Update criminal profiles
        leader.is_gang_member = True
        leader.is_gang_leader = True
        leader.gang_id = f"GANG-{gang_idx:04d}"
        for m in members:
            m.is_gang_member = True
            m.gang_id = f"GANG-{gang_idx:04d}"

        # Known associates: gang members know each other
        for m in members:
            if leader.criminal_id not in m.known_associates:
                m.known_associates.append(leader.criminal_id)
            for other in members:
                if other.criminal_id != m.criminal_id and other.criminal_id not in m.known_associates:
                    m.known_associates.append(other.criminal_id)

        # Territory: home district + 1-3 adjacent districts
        territory_ids = [leader.district_id]
        num_districts = min(int(rng.integers(1, 4)), len(district_ids) - 1)
        additional = list(rng.choice([d for d in district_ids if d != leader.district_id], size=num_districts, replace=False))
        territory_ids.extend(additional)
        territory_names = [district_meta.get(d, d) for d in territory_ids]

        # Specialization often derived from leader's expertise
        specialization = leader.preferred_crime_types[0] if leader.preferred_crime_types else rng.choice(GANG_SPECIALIZATIONS)

        # Threat level based on size + risk
        avg_risk = sum(1 if m.risk_level == "low" else 2 if m.risk_level == "medium" else 3 if m.risk_level == "high" else 4 for m in [leader] + members) / (len(members) + 1)
        if avg_risk >= 3.5 or len(members) >= 12:
            threat_level = "critical"
        elif avg_risk >= 2.5 or len(members) >= 8:
            threat_level = "high"
        elif avg_risk >= 1.5:
            threat_level = "medium"
        else:
            threat_level = "low"

        num_links = int(rng.integers(1, 4))
        financial_links = list(rng.choice(
            ["hawala", "real_estate", "transport_business", "agriculture", "liquor", "sand_mining"],
            size=num_links, replace=False
        ))

        gangs.append(Gang(
            gang_id=f"GANG-{gang_idx:04d}",
            name=f"{rng.choice(GANG_NAMES_PREFIX)} {rng.choice(GANG_NAMES_SUFFIX)} {gang_idx+1}",
            specialization=specialization,
            leader_criminal_id=leader.criminal_id,
            member_criminal_ids=all_member_ids,
            territory_district_ids=territory_ids,
            territory_district_names=territory_names,
            preferred_time_slot=rng.choice(MO_TIME_SLOTS),
            escape_vehicle_type=rng.choice(MO_ESCAPE_VEHICLES),
            communication_method=rng.choice(COMMUNICATION_METHODS),
            num_members=len(all_member_ids),
            threat_level=threat_level,
            financial_links=financial_links,
            is_interstate=rng.random() < 0.15,
            total_crimes_attributed=int(rng.integers(5, 50 + 1)),
            is_active=rng.random() < 0.75,
            formation_year=int(rng.integers(sim_start_year - 5, sim_start_year + 1 + 1)),
        ))

    return gangs