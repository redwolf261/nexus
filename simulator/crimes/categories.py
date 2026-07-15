"""
NEXUS Simulator — Crime Category Module
Maps crime type IDs to their metadata and provides lookup helpers.
"""
from __future__ import annotations
from typing import Dict, Optional
from simulator.config.constants import CRIME_CATEGORIES


# Fast lookup map
CRIME_CATEGORY_MAP: Dict[str, Dict] = {c["id"]: c for c in CRIME_CATEGORIES}


def get_crime_category(crime_id: str) -> Optional[Dict]:
    """Return the metadata dict for a crime type ID."""
    return CRIME_CATEGORY_MAP.get(crime_id)


def get_ipc_section(crime_id: str) -> str:
    """Return IPC section string for a crime type."""
    cat = CRIME_CATEGORY_MAP.get(crime_id, {})
    return cat.get("ipc", "Unknown")


def get_crime_severity(crime_id: str) -> int:
    """Return severity level (1-6) for a crime type."""
    cat = CRIME_CATEGORY_MAP.get(crime_id, {})
    return cat.get("severity", 1)


def get_crime_duration_minutes(crime_id: str, rng) -> int:
    """Return a random crime duration in minutes within the typical range."""
    cat = CRIME_CATEGORY_MAP.get(crime_id, {})
    mn = cat.get("typical_duration_min", 5)
    mx = cat.get("typical_duration_max", 60)
    return rng.randint(mn, mx)
