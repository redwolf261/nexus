"""
Spatial Analytics Engine — Phase 7.0

Moves beyond simple hotspot visualization to provide:
    - Spatial clustering of crime incidents (DBSCAN on lat/lng)
    - Travel corridor detection for recurring offenders
    - District transition analysis
    - Escape route inference based on FIR sequences

All results carry full IntelligenceExplanation provenance.
Deterministic: same input → same output.

Complexity:
    Spatial clustering: O(N²) worst case, O(N log N) with index
    Travel corridor: O(F²) per criminal where F = FIR count
"""
from __future__ import annotations

import math
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from backend.db.schema import FIR, Criminal, FIRAccomplice
from backend.intelligence.confidence import ConfidenceScore
from backend.intelligence.explainability import (
    IntelligenceExplanation, EvidenceItem, InferenceType
)

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Spatial DBSCAN: 0.5 km radius neighbourhood
SPATIAL_EPS_KM    = 0.5
SPATIAL_MIN_FIRS  = 3
MAX_FIRS          = 10000

# Degrees per km approximation for eps conversion
KM_PER_DEGREE_LAT = 111.0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class SpatialAnalyticsEngine:
    """
    Spatial analytics for crime incident data.

    Usage:
        engine = SpatialAnalyticsEngine(db)
        clusters = engine.detect_hotspot_clusters(district_id="DIST-01")
    """

    def __init__(self, db: Session):
        self.db = db
        self._default_station_coords = self._load_station_coords()

    def _load_station_coords(self) -> Dict[str, Tuple[float, float]]:
        """Load all police station coordinates for default GPS detection."""
        try:
            from backend.db.schema import Station
            stations = self.db.query(Station).filter(
                Station.latitude.isnot(None),
                Station.longitude.isnot(None)
            ).all()
            return {
                s.station_id: (s.latitude, s.longitude)
                for s in stations
            }
        except Exception:
            return {}

    def _is_default_gps(self, lat: float, lng: float, station_id: str) -> bool:
        """Check if coordinates match a police station (lazy data entry marker)."""
        if station_id not in self._default_station_coords:
            return False
        s_lat, s_lng = self._default_station_coords[station_id]
        dist = _haversine(lat, lng, s_lat, s_lng)
        return dist < 0.1  # Within 100m = likely lazy default entry

    def detect_hotspot_clusters(
        self,
        district_id: Optional[str] = None,
        crime_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cluster FIR locations into spatial hotspots using DBSCAN.
        Returns clusters with centroids, radii, FIR counts, and dominant crime type.
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not installed", "clusters": []}

        firs = self._fetch_geo_firs(district_id, crime_category)
        if len(firs) < SPATIAL_MIN_FIRS:
            return {"clusters": [], "total_firs": len(firs), "message": "Insufficient geo data"}

        coords = np.array([[f.latitude, f.longitude] for f in firs])

        # DBSCAN on lat/lng coordinates with eps in degrees
        eps_deg = SPATIAL_EPS_KM / KM_PER_DEGREE_LAT
        db_model = DBSCAN(eps=eps_deg, min_samples=SPATIAL_MIN_FIRS, metric="haversine")
        # haversine metric expects radians
        coords_rad = np.radians(coords)
        labels = db_model.fit_predict(coords_rad)

        clusters = self._extract_clusters(firs, labels)
        return {
            "clusters": clusters,
            "total_firs_with_coords": len(firs),
            "total_clusters": len(clusters),
            "unclustered_firs": int(np.sum(labels == -1)),
        }

    def detect_travel_corridors(self, criminal_id: str) -> Dict[str, Any]:
        """
        Detect geographic movement corridors for a specific criminal.
        Uses sequential FIR locations to infer travel paths.
        Ordered by occurred_datetime for accurate chronological sequencing.
        """
        rows = self.db.query(FIRAccomplice).filter_by(criminal_id=criminal_id).all()
        fir_ids = [r.fir_id for r in rows]
        if not fir_ids:
            return {"criminal_id": criminal_id, "corridors": [], "error": "No FIR history"}

        firs = (
            self.db.query(FIR)
            .filter(FIR.fir_id.in_(fir_ids))
            .filter(FIR.latitude.isnot(None), FIR.longitude.isnot(None))
            .order_by(FIR.occurred_datetime)  # CRITICAL FIX: Use datetime for precise ordering
            .all()
        )

        if len(firs) < 2:
            return {"criminal_id": criminal_id, "corridors": [], "message": "Insufficient location data"}

        corridors = []
        for i in range(len(firs) - 1):
            f1, f2 = firs[i], firs[i + 1]
            dist = _haversine(f1.latitude, f1.longitude, f2.latitude, f2.longitude)
            bearing = self._bearing(f1.latitude, f1.longitude, f2.latitude, f2.longitude)

            # Check timestamp precision: if times are defaults (12:00:00), confidence is lower
            has_time_precision = (
                (f1.occurred_time and f1.occurred_time.hour != 12) or
                (f2.occurred_time and f2.occurred_time.hour != 12)
            )
            time_precision_factor = 1.0 if has_time_precision else 0.75

            conf = ConfidenceScore(
                evidence_quality=1.0,
                data_completeness=1.0,
                algorithm_confidence=0.75 * time_precision_factor,  # Penalize if inferred time
                source_reliability=0.90,
                recency_weight=ConfidenceScore.recency_factor(f2.occurred_date),
            ).compute()

            evidence = [EvidenceItem(
                dimension="sequential_fir_movement",
                description=f"FIR {f1.fir_id} → FIR {f2.fir_id}: {dist:.1f} km, bearing {bearing:.0f}°",
                raw_value=dist,
                weight=1.0,
                contributed_score=min(1.0, dist / 50),
            )]

            # Add timestamp precision indicator
            if not has_time_precision:
                evidence.append(EvidenceItem(
                    dimension="timestamp_precision_warning",
                    description=f"Time-of-day not available; assuming noon for both FIRs. Corridor direction inference carries uncertainty.",
                    raw_value="inferred_time",
                    weight=0.0,
                    contributed_score=0.0,
                ))

            explanation = IntelligenceExplanation(
                inference_type=InferenceType.TRAVEL_CORRIDOR,
                observation=f"Criminal {criminal_id} appeared at two locations {dist:.1f} km apart",
                evidence=evidence,
                analytical_rule="Sequential FIR location analysis with haversine distance",
                inference=f"Likely travel corridor from ({f1.latitude:.4f}, {f1.longitude:.4f}) to ({f2.latitude:.4f}, {f2.longitude:.4f})",
                confidence=conf,
                recommended_action="Check ANPR cameras along inferred corridor for vehicle sightings",
            )

            corridors.append({
                "from_fir": f1.fir_id,
                "to_fir": f2.fir_id,
                "from_coords": {"lat": f1.latitude, "lng": f1.longitude},
                "to_coords": {"lat": f2.latitude, "lng": f2.longitude},
                "distance_km": round(dist, 2),
                "bearing_degrees": round(bearing, 1),
                "from_date": str(f1.occurred_date),
                "to_date": str(f2.occurred_date),
                "confidence": conf.to_dict(),
                "explanation": explanation.to_dict(),
            })

        return {
            "criminal_id": criminal_id,
            "total_locations": len(firs),
            "corridors": corridors,
            "total_distance_km": round(sum(c["distance_km"] for c in corridors), 2),
        }

    def district_transition_analysis(self) -> Dict[str, Any]:
        """
        Compute district-to-district criminal movement frequencies.
        Returns a transition matrix of criminals moving between districts.
        """
        rows = self.db.query(FIRAccomplice).all()
        criminal_firs: Dict[str, List[str]] = {}
        for r in rows:
            criminal_firs.setdefault(r.criminal_id, []).append(r.fir_id)

        transitions: Dict[str, int] = {}
        for cid, fir_ids in criminal_firs.items():
            if len(fir_ids) < 2:
                continue
            firs = (
                self.db.query(FIR)
                .filter(FIR.fir_id.in_(fir_ids), FIR.district_id.isnot(None))
                .order_by(FIR.occurred_date)
                .all()
            )
            districts = [f.district_id for f in firs if f.district_id]
            for i in range(len(districts) - 1):
                if districts[i] != districts[i + 1]:
                    key = f"{districts[i]}→{districts[i+1]}"
                    transitions[key] = transitions.get(key, 0) + 1

        top = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:20]
        return {
            "total_transitions_detected": len(transitions),
            "top_corridors": [{"corridor": k, "frequency": v} for k, v in top],
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _fetch_geo_firs(
        self, district_id: Optional[str], crime_category: Optional[str]
    ) -> List[FIR]:
        q = (self.db.query(FIR)
             .filter(FIR.latitude.isnot(None), FIR.longitude.isnot(None)))
        if district_id:
            q = q.filter(FIR.district_id == district_id)
        if crime_category:
            q = q.filter(FIR.crime_category == crime_category)
        return q.limit(MAX_FIRS).all()

    def _extract_clusters(self, firs: List[FIR], labels: np.ndarray) -> List[Dict[str, Any]]:
        unique_labels = set(labels) - {-1}
        fir_map = {f.fir_id: f for f in firs}
        clusters = []

        for label in sorted(unique_labels):
            mask = labels == label
            cluster_firs = [firs[i] for i, m in enumerate(mask) if m]
            if not cluster_firs:
                continue

            lats = [f.latitude for f in cluster_firs]
            lons = [f.longitude for f in cluster_firs]
            centroid_lat = float(np.mean(lats))
            centroid_lon = float(np.mean(lons))

            # Radius = max haversine distance from centroid to any point
            radius_km = max(
                _haversine(centroid_lat, centroid_lon, f.latitude, f.longitude)
                for f in cluster_firs
            )

            # Detect lazy data entry (default police station GPS)
            default_gps_count = sum(
                1 for f in cluster_firs
                if f.station_id and self._is_default_gps(f.latitude, f.longitude, f.station_id)
            )
            is_suspicious_hotspot = default_gps_count > len(cluster_firs) * 0.5

            categories = [f.crime_category for f in cluster_firs if f.crime_category]
            dominant = max(set(categories), key=categories.count) if categories else "Unknown"

            # Reduce confidence if lazy data entry detected
            base_confidence = 0.85 if not is_suspicious_hotspot else 0.5
            conf = ConfidenceScore(
                evidence_quality=min(1.0, len(cluster_firs) / 10),
                data_completeness=1.0 if not is_suspicious_hotspot else 0.6,
                algorithm_confidence=base_confidence,
                source_reliability=0.95 if not is_suspicious_hotspot else 0.70,
                recency_weight=0.90,
            ).compute()

            evidence = [
                EvidenceItem(
                    dimension="spatial_density",
                    description=f"{len(cluster_firs)} FIRs within {radius_km:.2f} km radius",
                    raw_value=len(cluster_firs),
                    weight=0.6,
                    contributed_score=min(1.0, len(cluster_firs) / 10) * 0.6,
                ),
                EvidenceItem(
                    dimension="crime_category_concentration",
                    description=f"Dominant crime: {dominant}",
                    raw_value=dominant,
                    weight=0.4,
                    contributed_score=0.4,
                ),
            ]

            if is_suspicious_hotspot:
                evidence.append(EvidenceItem(
                    dimension="lazy_data_entry_warning",
                    description=f"{default_gps_count}/{len(cluster_firs)} FIRs use default police station GPS (likely lazy data entry)",
                    raw_value=default_gps_count,
                    weight=0.0,
                    contributed_score=0.0,
                ))

            explanation = IntelligenceExplanation(
                inference_type=InferenceType.SPATIAL_CLUSTER,
                observation=f"{len(cluster_firs)} FIRs concentrated within {radius_km:.2f} km",
                evidence=evidence,
                analytical_rule=f"DBSCAN(eps={SPATIAL_EPS_KM} km, min_samples={SPATIAL_MIN_FIRS}) haversine metric",
                inference=f"Crime hotspot at ({centroid_lat:.4f}, {centroid_lon:.4f}): predominantly {dominant}",
                confidence=conf,
                recommended_action=f"Increase patrol frequency within {math.ceil(radius_km * 1.5)} km of hotspot centroid",
            )

            clusters.append({
                "cluster_id": f"HOTSPOT-{label:03d}",
                "centroid": {"lat": round(centroid_lat, 6), "lng": round(centroid_lon, 6)},
                "radius_km": round(radius_km, 3),
                "fir_count": len(cluster_firs),
                "dominant_crime": dominant,
                "fir_ids": [f.fir_id for f in cluster_firs],
                "confidence": conf.to_dict(),
                "explanation": explanation.to_dict(),
            })

        clusters.sort(key=lambda c: c["fir_count"], reverse=True)
        return clusters

    @staticmethod
    def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute compass bearing from point 1 to point 2 in degrees."""
        dlon = math.radians(lon2 - lon1)
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        x = math.sin(dlon) * math.cos(lat2_r)
        y = (math.cos(lat1_r) * math.sin(lat2_r)
             - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))
        return (math.degrees(math.atan2(x, y)) + 360) % 360
