"""
NEXUS Simulator — Parquet Exporter
High-performance columnar export for large-scale datasets.
Requires pyarrow. Automatically skipped if not installed.
"""
from __future__ import annotations
import logging
from pathlib import Path
from datetime import date, time, datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False
    logger.warning("pyarrow not installed. Parquet export will be skipped.")


def _to_dict_list(items: List[Any], key_exclusions: set = None) -> List[dict]:
    """Flatten a list of dataclass instances to list of dicts."""
    from dataclasses import fields as dc_fields, asdict as dc_asdict
    key_exclusions = key_exclusions or set()
    result = []
    for item in items:
        if hasattr(item, "__dataclass_fields__"):
            row = {}
            for f in dc_fields(item):
                if f.name in key_exclusions:
                    continue
                v = getattr(item, f.name)
                if isinstance(v, (list, dict)) and v and hasattr(getattr(v, "__iter__", None), "__call__"):
                    v = str(v)
                elif isinstance(v, (date, datetime)):
                    v = v.isoformat()
                elif isinstance(v, time):
                    v = v.strftime("%H:%M:%S")
                elif isinstance(v, bool):
                    pass  # keep as bool
                row[f.name] = v
            result.append(row)
        elif isinstance(item, dict):
            result.append(item)
    return result


def export_parquet(sim_data: dict, output_dir: Path) -> None:
    """Export major tables as Parquet files (requires pyarrow)."""
    if not HAS_PYARROW:
        logger.warning("Parquet export skipped: pyarrow not installed.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Tables to export as Parquet
    tables_to_export = {
        "firs":         ("firs.parquet", {"victims", "accused_list"}),
        "criminals":    ("criminals.parquet", {"modus_operandi", "known_associates", "alias_names", "vehicle_ids", "phone_ids", "preferred_crime_types"}),
        "evidence":     ("evidence.parquet", {"chain_of_custody", "tags"}),
        "arrests":      ("arrests.parquet", set()),
        "patrol_logs":  ("patrol_logs.parquet", set()),
        "cctv_events":  ("cctv_events.parquet", set()),
    }

    for key, (filename, exclusions) in tables_to_export.items():
        data = sim_data.get(key, [])
        if not data:
            continue

        rows = _to_dict_list(data, exclusions)
        if not rows:
            continue

        try:
            table = pa.Table.from_pylist(rows)
            pq.write_table(table, output_dir / filename, compression="snappy")
            logger.info(f"  Wrote {len(rows):,} rows → {filename} (Parquet)")
        except Exception as e:
            logger.error(f"  Failed to write {filename}: {e}")
