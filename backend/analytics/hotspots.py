from __future__ import annotations

from typing import List, Tuple


def extract_hotspots(coords: List[Tuple[float, float]]) -> List[dict]:
    """
    Cluster FIR coordinates using DBSCAN and return hotspot centroids.

    Parameters
    ----------
    coords : list of (lat, lng) tuples from postgres_repo.get_fir_coordinates()

    Returns
    -------
    List of hotspot dicts with cluster_id, lat, lng, intensity (0-1).
    """
    if not coords:
        return []

    try:
        import numpy as np
        from sklearn.cluster import DBSCAN
    except ImportError:
        # Graceful fallback: return centroid of all points as single hotspot
        lats = [c[0] for c in coords]
        lngs = [c[1] for c in coords]
        return [{
            "cluster_id": "HS-001",
            "lat": round(sum(lats) / len(lats), 6),
            "lng": round(sum(lngs) / len(lngs), 6),
            "intensity": 1.0,
        }]

    # Convert degrees → radians for haversine metric
    import math
    X = np.radians(np.array(coords, dtype=float))

    # eps = 5 km in radians (Earth radius ≈ 6371 km)
    eps_rad = 5.0 / 6371.0
    db = DBSCAN(eps=eps_rad, min_samples=3, algorithm="ball_tree", metric="haversine")
    labels = db.fit_predict(X)

    hotspots = []
    unique_labels = set(labels) - {-1}   # -1 = noise

    if not unique_labels:
        # No clusters found — return top-3 individual points as weak hotspots
        for i, (lat, lng) in enumerate(coords[:3]):
            hotspots.append({
                "cluster_id": f"HS-{i+1:03d}",
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "intensity": round(0.3 - i * 0.05, 2),
            })
        return hotspots

    # Compute cluster sizes to normalize intensity
    max_cluster_size = max(
        int((labels == label).sum()) for label in unique_labels
    )

    for label in sorted(unique_labels):
        mask = labels == label
        cluster_points = np.array(coords)[mask]
        centroid_lat = float(cluster_points[:, 0].mean())
        centroid_lng = float(cluster_points[:, 1].mean())
        size = int(mask.sum())
        intensity = round(size / max_cluster_size, 3)
        hotspots.append({
            "cluster_id": f"HS-{label + 1:03d}",
            "lat": round(centroid_lat, 6),
            "lng": round(centroid_lng, 6),
            "intensity": intensity,
        })

    # Sort by intensity descending
    hotspots.sort(key=lambda h: h["intensity"], reverse=True)
    return hotspots

