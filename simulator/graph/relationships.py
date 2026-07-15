"""
NEXUS Simulator — Graph Relationship Types
Defines all 11 edge types in the knowledge graph with their properties.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class GraphEdge:
    """A typed, weighted edge in the crime knowledge graph."""
    source_id: str
    source_type: str    # "Person" | "Vehicle" | "FIR" | "Phone" | "Gang" | "Evidence" | "Location" | "Officer"
    target_id: str
    target_type: str
    relation: str       # See EDGE_TYPES below
    weight: float       # 0.0–1.0 confidence/strength
    timestamp: Optional[date]
    properties: dict


# All valid relation types
EDGE_TYPES = {
    # Criminal relations
    "COMMITTED":          "Person → FIR — accused committed the crime",
    "ACCOMPLICE_IN":      "Person → FIR — accomplice in the crime",
    "MEMBER_OF":          "Person → Gang — gang membership",
    "LEADS":              "Person → Gang — leadership",
    "ASSOCIATED_WITH":    "Person → Person — known associates",

    # Asset relations
    "OWNS_VEHICLE":       "Person → Vehicle — registered owner",
    "USED_VEHICLE_IN":    "Vehicle → FIR — vehicle used in crime",
    "OWNS_PHONE":         "Person → Phone — phone subscriber",
    "PHONE_LINKED_TO":    "Phone → FIR — phone used in / linked to crime",
    "CONTACTED":          "Phone → Phone — call record between two phones",

    # Victimization
    "VICTIM_IN":          "Person → FIR — person was victim",
    "WITNESSED":          "Person → FIR — person was witness",

    # Investigation
    "INVESTIGATED_BY":    "FIR → Officer — assigned investigating officer",
    "REGISTERED_AT":      "FIR → Station — station where FIR was registered",

    # Evidence
    "EVIDENCE_FOR":       "Evidence → FIR — evidence pertains to FIR",
    "LINKS_SUSPECT":      "Evidence → Person — evidence links to a person",

    # Location
    "OCCURRED_AT":        "FIR → Location — crime location",
    "HOME_DISTRICT":      "Person → District — home district",

    # Gang
    "OPERATES_IN":        "Gang → District — gang territory",
    "SPECIALIZES_IN":     "Gang → CrimeType — crime specialization",
}
