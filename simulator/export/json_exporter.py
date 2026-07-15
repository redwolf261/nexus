"""
NEXUS Simulator — JSON Exporter
Exports simulation summary and key datasets as JSON.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import date, time, datetime
from typing import Any

logger = logging.getLogger(__name__)


class _DateEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.strftime("%H:%M:%S")
        if hasattr(obj, "__dataclass_fields__"):
            return {f: getattr(obj, f) for f in obj.__dataclass_fields__}
        return super().default(obj)


def export_json(sim_data: dict, output_dir: Path) -> None:
    """Export simulation summary and metadata as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Summary JSON
    summary = {
        "simulation_summary": {
            "total_districts": len(sim_data.get("districts", [])),
            "total_stations":  len(sim_data.get("stations", [])),
            "total_officers":  len(sim_data.get("officers", [])),
            "total_citizens":  len(sim_data.get("citizens", [])),
            "total_criminals": len(sim_data.get("criminals", [])),
            "total_gangs":     len(sim_data.get("gangs", [])),
            "total_firs":      len(sim_data.get("firs", [])),
            "total_victims":   len(sim_data.get("victims", [])),
            "total_accused":   len(sim_data.get("accused", [])),
            "total_evidence":  len(sim_data.get("evidence", [])),
            "total_arrests":   len(sim_data.get("arrests", [])),
            "total_chargesheets": len(sim_data.get("chargesheets", [])),
            "total_patrol_logs": len(sim_data.get("patrol_logs", [])),
            "total_cctv_events": len(sim_data.get("cctv_events", [])),
            "entity_resolution_records": len(sim_data.get("entity_resolution", [])),
        }
    }

    summary_path = output_dir / "simulation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, cls=_DateEncoder, ensure_ascii=False)
    logger.info(f"  Wrote simulation summary -> {summary_path.name}")

    # Gang network JSON (for quick visualization)
    gangs = sim_data.get("gangs", [])
    if gangs:
        gang_network = []
        for g in gangs[:100]:  # Cap for JSON size
            gang_network.append({
                "gang_id": g.gang_id,
                "name": g.name,
                "specialization": g.specialization,
                "threat_level": g.threat_level,
                "num_members": g.num_members,
                "leader": g.leader_criminal_id,
                "members": g.member_criminal_ids,
                "territories": g.territory_district_names,
                "is_active": g.is_active,
            })
        gang_path = output_dir / "gang_network.json"
        with open(gang_path, "w", encoding="utf-8") as f:
            json.dump(gang_network, f, indent=2, ensure_ascii=False)
        logger.info(f"  Wrote gang network -> {gang_path.name}")

    # Crime type statistics JSON
    firs = sim_data.get("firs", [])
    if firs:
        from collections import Counter
        crime_counts = Counter(f.crime_type for f in firs)
        district_counts = Counter(f.district_id for f in firs)
        stats = {
            "crime_type_distribution": dict(crime_counts.most_common()),
            "district_distribution": dict(district_counts.most_common(15)),
            "total_loss_inr": sum(f.estimated_loss_inr for f in firs),
            "gang_crimes_fraction": sum(1 for f in firs if f.is_gang_crime) / len(firs),
            "status_distribution": dict(Counter(f.status for f in firs)),
        }
        stats_path = output_dir / "crime_statistics.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"  Wrote crime statistics -> {stats_path.name}")
