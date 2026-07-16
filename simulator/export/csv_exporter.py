"""
NEXUS Simulator — CSV Exporter
Exports all simulation datasets as UTF-8-BOM CSV files.
UTF-8-BOM ensures Kannada characters render correctly in Excel.
"""
from __future__ import annotations
import csv
import logging
from pathlib import Path
from dataclasses import asdict, fields
from datetime import date, time, datetime
from typing import List, Any, Dict

logger = logging.getLogger(__name__)


def _serialize_value(v: Any) -> str:
    """Convert Python objects to CSV-safe strings."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, time):
        return v.strftime("%H:%M:%S")
    if isinstance(v, (list, tuple)):
        return "|".join(str(x) for x in v)
    if isinstance(v, dict):
        return str(v)
    return str(v)


def _write_csv(data: List[Any], path: Path, flat_fn=None) -> int:
    """
    Write a list of dataclass instances to CSV.
    flat_fn: optional function to convert an object to a flat dict.
    """
    if not data:
        logger.warning(f"  No data to write: {path.name}")
        return 0

    rows = []
    for item in data:
        if flat_fn:
            row = flat_fn(item)
        elif hasattr(item, "__dataclass_fields__"):
            row = {}
            for f in fields(item):
                v = getattr(item, f.name)
                # Skip complex nested objects (victims/accused lists — they have their own table)
                if isinstance(v, list) and v and hasattr(v[0], "__dataclass_fields__"):
                    continue
                row[f.name] = _serialize_value(v)
        elif isinstance(item, dict):
            row = {k: _serialize_value(v) for k, v in item.items()}
        else:
            row = {"value": str(item)}
        rows.append(row)

    if not rows:
        return 0

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"  Wrote {len(rows):,} rows -> {path.name}")
    return len(rows)


def export_all_csv(sim_data: dict, output_dir: Path) -> Dict[str, int]:
    """
    Export all simulation datasets as CSV.
    sim_data keys: districts, stations, officers, citizens, criminals, gangs,
                   firs, victims, accused, evidence, arrests, chargesheets,
                   patrol_logs, cctv_events, modus_operandi, entity_resolution
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, int] = {}

    table_map = {
        "districts":        "districts.csv",
        "stations":         "stations.csv",
        "pois":             "pois.csv",
        "officers":         "officers.csv",
        "citizens":         "persons.csv",
        "criminals":        "criminals.csv",
        "gangs":            "gangs.csv",
        "firs":             "firs.csv",
        "victims":          "victims.csv",
        "accused":          "accused.csv",
        "evidence":         "evidence.csv",
        "arrests":          "arrests.csv",
        "chargesheets":     "chargesheets.csv",
        "patrol_logs":      "patrol_logs.csv",
        "cctv_events":      "cctv_events.csv",
        "modus_operandi":   "modus_operandi.csv",
        "entity_resolution":"entity_resolution.csv",
        "noisy_firs":       "firs_with_noise.csv",
        "vehicles":         "vehicles.csv",
        "phones":           "phones.csv",
        "cdrs":             "cdrs.csv",
        "daily_context":    "daily_context.csv",
        "campaigns":        "ground_truth_campaigns.csv",
        "investigation_logs": "investigation_logs.csv",
        "financial_transactions": "financial_transactions.csv",
        "intelligence_tips": "intelligence_tips.csv",
        "social_ties":      "social_network.csv",
        "masterminds":      "ground_truth_masterminds.csv",
        "court_cases":      "court_cases.csv",
        "informants":       "informants.csv",
        "cell_towers":      "cell_towers.csv",
        "cctv_cameras":     "cctv_cameras.csv",
        "anpr_cameras":     "anpr_cameras.csv",
        "cell_pings":       "cell_tower_pings.csv",
        "vehicle_gps":      "vehicle_gps.csv",
        "cctv_logs":        "cctv_logs.csv",
        "anpr_logs":        "anpr_logs.csv",
    }

    for key, filename in table_map.items():
        data = sim_data.get(key, [])
        if not data:
            continue

        path = output_dir / filename

        # Special handlers for dataclasses with nested list children
        if key in {"gangs"}:
            written[key] = _write_csv(data, path, flat_fn=_flatten_gang)
        elif key in {"criminals"}:
            written[key] = _write_csv(data, path, flat_fn=_flatten_criminal)
        elif key in {"modus_operandi"}:
            written[key] = _write_csv(data, path, flat_fn=_flatten_mo)
        elif key in {"entity_resolution"}:
            written[key] = _write_csv(data, path)  # Already dicts
        elif key in {"masterminds"}:
            written[key] = _write_csv(data, path, flat_fn=_flatten_mastermind)
        else:
            written[key] = _write_csv(data, path)

    logger.info(f"CSV export complete. {sum(written.values()):,} total rows across {len(written)} tables.")
    return written


# ── Flatten helpers for complex objects ────────────────────────────────────

def _flatten_gang(gang) -> dict:
    return {
        "gang_id": gang.gang_id,
        "name": gang.name,
        "specialization": gang.specialization,
        "leader_criminal_id": gang.leader_criminal_id,
        "member_criminal_ids": "|".join(gang.member_criminal_ids),
        "territory_district_ids": "|".join(gang.territory_district_ids),
        "territory_district_names": "|".join(gang.territory_district_names),
        "preferred_time_slot": gang.preferred_time_slot,
        "escape_vehicle_type": gang.escape_vehicle_type,
        "communication_method": gang.communication_method,
        "num_members": gang.num_members,
        "threat_level": gang.threat_level,
        "financial_links": "|".join(gang.financial_links),
        "is_interstate": gang.is_interstate,
        "total_crimes_attributed": gang.total_crimes_attributed,
        "is_active": gang.is_active,
        "formation_year": gang.formation_year,
    }


def _flatten_criminal(c) -> dict:
    return {
        "criminal_id": c.criminal_id,
        "citizen_id": c.citizen_id,
        "name_en": c.name_en,
        "name_kn": c.name_kn,
        "alias_names": "|".join(c.alias_names),
        "age": c.age,
        "gender": c.gender,
        "district_id": c.district_id,
        "district_name": c.district_name,
        "station_id": c.station_id,
        "home_lat": c.home_lat,
        "home_lng": c.home_lng,
        "risk_level": c.risk_level,
        "expertise": c.expertise,
        "preferred_crime_types": "|".join(c.preferred_crime_types),
        "operating_radius_km": c.operating_radius_km,
        "recidivism_probability": c.recidivism_probability,
        "career_stage": c.career_stage,
        "is_gang_member": c.is_gang_member,
        "gang_id": c.gang_id or "",
        "is_gang_leader": c.is_gang_leader,
        "known_associates": "|".join(c.known_associates[:10]),
        "total_crimes_committed": c.total_crimes_committed,
        "total_arrests": c.total_arrests,
        "is_currently_active": c.is_currently_active,
        "is_currently_arrested": c.is_currently_arrested,
        # MO fields
        "mo_entry_method": c.modus_operandi.entry_method if c.modus_operandi else "",
        "mo_time_slot": c.modus_operandi.preferred_time_slot if c.modus_operandi else "",
        "mo_target_type": c.modus_operandi.target_type if c.modus_operandi else "",
        "mo_escape_vehicle": c.modus_operandi.escape_vehicle if c.modus_operandi else "",
        "mo_weapon": c.modus_operandi.weapon if c.modus_operandi else "",
        "mo_stolen_property": c.modus_operandi.stolen_property if c.modus_operandi else "",
        "mo_num_offenders": c.modus_operandi.typical_num_offenders if c.modus_operandi else 1,
        "mo_operates_at_night": c.modus_operandi.operates_at_night if c.modus_operandi else False,
    }


def _flatten_mo(mo) -> dict:
    return {
        "crime_event_id": mo.crime_event_id,
        "criminal_id": mo.criminal_id or "",
        "entry_method": mo.entry_method,
        "time_slot": mo.time_slot,
        "target_type": mo.target_type,
        "escape_vehicle": mo.escape_vehicle,
        "weapon": mo.weapon,
        "stolen_property": mo.stolen_property,
        "num_offenders": mo.num_offenders,
        "operates_at_night": mo.operates_at_night,
        "is_solo": mo.is_solo,
        "uses_vehicle_escape": mo.uses_vehicle_escape,
        "is_violent": mo.is_violent,
    }

def _flatten_mastermind(m) -> dict:
    return {
        "mastermind_id": m.mastermind_id,
        "citizen_id": m.citizen_id,
        "name_en": m.name_en,
        "alias": m.alias,
        "wealth_level": m.wealth_level,
        "controlled_gang_ids": "|".join(m.controlled_gang_ids),
        "front_business": m.front_business
    }
