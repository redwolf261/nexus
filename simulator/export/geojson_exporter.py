"""
NEXUS Simulator — GeoJSON Exporter
Exports spatial datasets as GeoJSON FeatureCollections:
  - crimes.geojson: All FIR locations with properties
  - stations.geojson: All police stations
  - hotspots.geojson: Crime density aggregation points
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def _fir_feature(fir) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [fir.longitude, fir.latitude],
        },
        "properties": {
            "fir_id":          fir.fir_id,
            "fir_number":      fir.fir_number,
            "crime_type":      fir.crime_type,
            "crime_category":  fir.crime_category,
            "severity":        fir.severity,
            "occurred_date":   fir.occurred_date.isoformat(),
            "status":          fir.status,
            "district":        fir.district_name,
            "station_id":      fir.station_id,
            "loss_inr":        fir.estimated_loss_inr,
            "is_gang_crime":   fir.is_gang_crime,
            "season":          fir.season,
        },
    }


def _station_feature(station) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [station.longitude, station.latitude],
        },
        "properties": {
            "station_id":       station.station_id,
            "name":             station.name,
            "district":         station.district_name,
            "taluk":            station.taluk,
            "station_type":     station.station_type,
            "officer_quota":    station.officer_quota,
            "population_served":station.population_served,
            "is_cyber_cell":    station.is_cyber_cell,
            "phone":            station.phone,
        },
    }


def _build_hotspot_grid(firs: list, grid_size: float = 0.1) -> List[Dict]:
    """
    Aggregate FIRs into a grid of hotspot cells.
    grid_size: degrees (~11km at Karnataka latitudes)
    """
    grid: Dict[tuple, list] = defaultdict(list)
    for fir in firs:
        cell_lat = round(fir.latitude  / grid_size) * grid_size
        cell_lng = round(fir.longitude / grid_size) * grid_size
        grid[(cell_lat, cell_lng)].append(fir)

    features = []
    for (cell_lat, cell_lng), cell_firs in grid.items():
        from collections import Counter
        crime_types = Counter(f.crime_type for f in cell_firs)
        top_crime = crime_types.most_common(1)[0][0] if crime_types else "UNKNOWN"
        avg_severity = sum(f.severity for f in cell_firs) / len(cell_firs)
        gang_count = sum(1 for f in cell_firs if f.is_gang_crime)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [cell_lng, cell_lat],
            },
            "properties": {
                "crime_count":   len(cell_firs),
                "top_crime":     top_crime,
                "avg_severity":  round(avg_severity, 2),
                "gang_count":    gang_count,
                "total_loss_inr":round(sum(f.estimated_loss_inr for f in cell_firs), 2),
                "grid_lat":      cell_lat,
                "grid_lng":      cell_lng,
            },
        })

    return sorted(features, key=lambda f: f["properties"]["crime_count"], reverse=True)


def export_geojson(sim_data: dict, output_dir: Path) -> None:
    """Export spatial datasets as GeoJSON FeatureCollections."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Crimes
    firs = sim_data.get("firs", [])
    if firs:
        features = [_fir_feature(f) for f in firs]
        _write_geojson(features, output_dir / "crimes.geojson")

    # Stations
    stations = sim_data.get("stations", [])
    if stations:
        features = [_station_feature(s) for s in stations]
        _write_geojson(features, output_dir / "stations.geojson")

    # Hotspot grid
    if firs:
        hotspot_features = _build_hotspot_grid(firs, grid_size=0.1)
        _write_geojson(hotspot_features, output_dir / "hotspots.geojson")
        logger.info(f"  Built {len(hotspot_features)} hotspot grid cells")


def _write_geojson(features: list, path: Path) -> None:
    fc = {"type": "FeatureCollection", "features": features}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
    logger.info(f"  Wrote {len(features):,} features -> {path.name}")
