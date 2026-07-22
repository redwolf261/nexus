"""
Evidence weight matrix for the probabilistic entity resolution engine.

Each dimension contributes a weighted partial confidence to the overall
match score. Weights sum to 1.0. Individual scores are scaled 0.0–1.0
before weighting.

Mathematical formulation:
    confidence = Σ(weight_i × evidence_score_i)  for all dimensions i
    where Σweight_i = 1.0

These values are tunable by investigators / administrators without
changing business logic.
"""
from typing import Dict

# Weight matrix: dimension -> weight (must sum to 1.0)
EVIDENCE_WEIGHTS: Dict[str, float] = {
    "aadhaar_match":       0.25,   # Exact government ID match — highest certainty
    "phone_exact":         0.20,   # Exact phone number match — very high certainty
    "name_jaro_winkler":   0.15,   # Fuzzy name similarity (Jaro-Winkler)
    "shared_fir":          0.12,   # Appeared in same FIR cluster
    "vehicle_match":       0.10,   # Shared/identical vehicle registration
    "address_similarity":  0.07,   # Address fuzzy similarity
    "geographic_proximity":0.05,   # Home coordinates within threshold km
    "shared_associate":    0.04,   # Known to share a mutual associate
    "temporal_overlap":    0.02,   # Active criminal career overlaps in time
}

# Minimum threshold: below this confidence, no match is reported
MATCH_THRESHOLD: float = 0.40

# Fuzzy name similarity threshold: below this, name dimension scores 0
# FIX HIGH #2: Lowered from 0.75 to 0.70 for better recall on Indian name variants
NAME_SIMILARITY_MIN: float = 0.70

# Geographic proximity radius in km — within this is full proximity score
GEO_PROXIMITY_KM: float = 5.0

# Recency decay half-life in days — used by temporal intelligence
RECENCY_HALF_LIFE_DAYS: int = 180

assert abs(sum(EVIDENCE_WEIGHTS.values()) - 1.0) < 1e-9, \
    "EVIDENCE_WEIGHTS must sum to 1.0"
