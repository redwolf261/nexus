"""
NEXUS Simulator — Modus Operandi Fingerprint
Generates a structured MO fingerprint for each crime event.
The fingerprint is derived from the criminal's profile MO template
with slight random variation to simulate inconsistency in real crimes.
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Optional

from simulator.config.constants import (
    MO_ENTRY_METHODS, MO_TIME_SLOTS, MO_TARGET_TYPES,
    MO_ESCAPE_VEHICLES, MO_WEAPONS, MO_STOLEN_PROPERTY, MO_NUM_OFFENDERS
)
from simulator.criminals.profiles import CriminalProfile, MoTemplate


@dataclass
class MoFingerprint:
    """Per-crime MO fingerprint used for similarity analysis."""
    crime_event_id: str
    criminal_id: Optional[str]
    entry_method: str
    time_slot: str
    target_type: str
    escape_vehicle: str
    weapon: str
    stolen_property: str
    num_offenders: int
    operates_at_night: bool
    # Derived similarity features (for DBSCAN/clustering)
    is_solo: bool
    uses_vehicle_escape: bool
    is_violent: bool

    def to_vector_dict(self) -> dict:
        """Return a numeric encoding suitable for ML clustering."""
        return {
            "entry_method": MO_ENTRY_METHODS.index(self.entry_method) if self.entry_method in MO_ENTRY_METHODS else 0,
            "time_slot": MO_TIME_SLOTS.index(self.time_slot) if self.time_slot in MO_TIME_SLOTS else 0,
            "target_type": MO_TARGET_TYPES.index(self.target_type) if self.target_type in MO_TARGET_TYPES else 0,
            "escape_vehicle": MO_ESCAPE_VEHICLES.index(self.escape_vehicle) if self.escape_vehicle in MO_ESCAPE_VEHICLES else 0,
            "weapon": MO_WEAPONS.index(self.weapon) if self.weapon in MO_WEAPONS else 0,
            "stolen_property": MO_STOLEN_PROPERTY.index(self.stolen_property) if self.stolen_property in MO_STOLEN_PROPERTY else 0,
            "num_offenders": self.num_offenders,
            "operates_at_night": int(self.operates_at_night),
            "is_solo": int(self.is_solo),
            "uses_vehicle_escape": int(self.uses_vehicle_escape),
            "is_violent": int(self.is_violent),
        }


def generate_mo_fingerprint(
    crime_event_id: str,
    rng: random.Random,
    criminal: Optional[CriminalProfile] = None,
    deviation_probability: float = 0.20,
) -> MoFingerprint:
    """
    Generate an MO fingerprint for a crime event.
    If a criminal profile is provided, derive from their template (with deviation).
    Otherwise generate randomly.
    """
    if criminal and criminal.modus_operandi:
        template: MoTemplate = criminal.modus_operandi

        def maybe_deviate(value: str, pool: list) -> str:
            if rng.random() < deviation_probability:
                return rng.choice(pool)
            return value

        entry_method = maybe_deviate(template.entry_method, MO_ENTRY_METHODS)
        time_slot    = maybe_deviate(template.preferred_time_slot, MO_TIME_SLOTS)
        target_type  = maybe_deviate(template.target_type, MO_TARGET_TYPES)
        escape_veh   = maybe_deviate(template.escape_vehicle, MO_ESCAPE_VEHICLES)
        weapon       = maybe_deviate(template.weapon, MO_WEAPONS)
        stolen_prop  = maybe_deviate(template.stolen_property, MO_STOLEN_PROPERTY)
        num_off      = template.typical_num_offenders if rng.random() > 0.15 else rng.choice(MO_NUM_OFFENDERS)
        at_night     = template.operates_at_night if rng.random() > 0.10 else not template.operates_at_night

    else:
        entry_method = rng.choice(MO_ENTRY_METHODS)
        time_slot    = rng.choice(MO_TIME_SLOTS)
        target_type  = rng.choice(MO_TARGET_TYPES)
        escape_veh   = rng.choice(MO_ESCAPE_VEHICLES)
        weapon       = rng.choice(MO_WEAPONS)
        stolen_prop  = rng.choice(MO_STOLEN_PROPERTY)
        num_off      = rng.choice(MO_NUM_OFFENDERS)
        at_night     = rng.random() < 0.55

    return MoFingerprint(
        crime_event_id=crime_event_id,
        criminal_id=criminal.criminal_id if criminal else None,
        entry_method=entry_method,
        time_slot=time_slot,
        target_type=target_type,
        escape_vehicle=escape_veh,
        weapon=weapon,
        stolen_property=stolen_prop,
        num_offenders=num_off,
        operates_at_night=at_night,
        is_solo=num_off == 1,
        uses_vehicle_escape=escape_veh not in {"on_foot", "unknown"},
        is_violent=weapon not in {"none", "bare_hands"},
    )
