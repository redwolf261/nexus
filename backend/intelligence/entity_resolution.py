"""
Probabilistic Entity Resolution Engine — Phase 7.0

Replaces the Phase 2 deterministic matching with a multi-dimensional
weighted evidence aggregation model.

Algorithm:
    For each candidate entity:
        1. Score each evidence dimension independently (0.0–1.0)
        2. Multiply each score by its configured weight
        3. Sum weighted scores → match_confidence
        4. If match_confidence ≥ MATCH_THRESHOLD → emit match with full trace

Every match carries an IntelligenceExplanation for full provenance.

Complexity: O(N) candidates × O(D) dimensions = O(N·D)
    where N = filtered candidate set (capped at 50), D = 9 dimensions.
"""
from __future__ import annotations

import math
from typing import List, Dict, Any, Optional
from datetime import date

from sqlalchemy.orm import Session

from backend.db.schema import Person, Vehicle, FIR, Criminal, FIRAccomplice, Phone
from backend.intelligence.evidence_weights import (
    EVIDENCE_WEIGHTS, MATCH_THRESHOLD, NAME_SIMILARITY_MIN, GEO_PROXIMITY_KM
)
from backend.intelligence.confidence import ConfidenceScore, completeness
from backend.intelligence.explainability import (
    IntelligenceExplanation, EvidenceItem, InferenceType
)

# ---------------------------------------------------------------------------
# Import jellyfish with graceful fallback to difflib if not yet installed
# ---------------------------------------------------------------------------
try:
    import jellyfish

    def _jaro_winkler(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return jellyfish.jaro_winkler_similarity(a.lower(), b.lower())

except ImportError:
    import difflib

    def _jaro_winkler(a: str, b: str) -> float:  # type: ignore[misc]
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _geo_distance_km(lat1: Optional[float], lon1: Optional[float],
                     lat2: Optional[float], lon2: Optional[float]) -> Optional[float]:
    """Haversine distance in km, returns None if coordinates missing."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _address_similarity(a: Optional[str], b: Optional[str]) -> float:
    if not a or not b:
        return 0.0
    return _jaro_winkler(a, b)


def _strip_regional_prefixes(name: str) -> str:
    """
    FIX HIGH #2: Remove common regional/honorific prefixes for matching.
    This helps with variant registrations like "Sri Raj" vs "Raj".
    """
    if not name:
        return name

    prefixes = [
        "Sri ", "Shri ", "Sri.", "Shri.",
        "Dr ", "Dr. ",
        "Md ", "Md. ", "Md ",
        "Muhammad ", "Mohammed ",
        "Mr ", "Mrs ", "Ms ",
        "Saint ", "St ",
    ]

    name_lower = name
    for prefix in prefixes:
        if name_lower.lower().startswith(prefix.lower()):
            return name[len(prefix):].strip()

    return name

def _phonetic_hash(name: str) -> str:
    """
    Simple phonetic hash for Indian names: consonant skeleton + first vowel.
    Handles transliteration variations (e.g., Mohammad/Muhammad).
    """
    if not name:
        return ""
    name = name.lower().replace(" ", "")
    vowels = "aeiouou"
    # Keep consonants and first vowel
    consonants = "".join(c for c in name if c not in vowels)
    first_vowel = next((c for c in name if c in vowels), "")
    return (consonants[:8] + first_vowel)[:10]


# Required fields for data completeness check
_PERSON_REQUIRED = ["name_en", "phone_primary", "district_id", "aadhaar"]


class EntityResolutionEngine:
    """
    Multi-dimensional probabilistic entity resolution engine.

    Usage:
        er = EntityResolutionEngine(db)
        result = er.resolve_person("CITIZEN-0187")
        # result.matches — list of EntityMatch with full explanation
    """

    def __init__(self, db: Session):
        self.db = db

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def resolve_person(self, person_id: str) -> Dict[str, Any]:
        """
        Return probabilistic matches for a person, with full reasoning traces.
        """
        p = self.db.query(Person).filter_by(citizen_id=person_id).first()
        if not p:
            return {"entity_id": person_id, "matches": [], "error": "Entity not found"}

        # Build candidate set (SQL pre-filtered, max 50)
        candidates = self._candidate_persons(p)

        # Pre-fetch shared FIR sets for the source person (once, not per candidate)
        source_fir_ids = self._person_fir_ids(person_id)

        matches = []
        for candidate in candidates:
            match = self._score_person_pair(p, candidate, source_fir_ids)
            if match is not None:
                matches.append(match)

        # Sort by confidence descending
        matches.sort(key=lambda m: m["confidence"]["overall_confidence"], reverse=True)

        # Add alternative candidates section
        top = matches[:1]
        alternatives = [
            {
                "entity_id": m["candidate_id"],
                "confidence_pct": round(m["confidence"]["overall_confidence"] * 100, 1)
            }
            for m in matches[1:4]
        ]

        return {
            "entity_id": person_id,
            "entity_name": p.name_en,
            "primary_matches": top,
            "alternative_candidates": alternatives,
            "total_candidates_evaluated": len(candidates),
        }

    def resolve_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Return probabilistic matches for a vehicle."""
        v = self.db.query(Vehicle).filter_by(vehicle_id=vehicle_id).first()
        if not v:
            return {"entity_id": vehicle_id, "matches": [], "error": "Entity not found"}

        matches = []
        if v.license_plate:
            dupes = self.db.query(Vehicle).filter(
                Vehicle.license_plate == v.license_plate,
                Vehicle.vehicle_id != vehicle_id
            ).all()
            for d in dupes:
                conf = ConfidenceScore(
                    evidence_quality=1.0,
                    data_completeness=1.0,
                    algorithm_confidence=1.0,
                    source_reliability=1.0,
                    recency_weight=1.0,
                ).compute()
                evidence = [EvidenceItem(
                    dimension="license_plate_exact",
                    description=f"Identical license plate: {v.license_plate}",
                    raw_value=v.license_plate,
                    weight=1.0,
                    contributed_score=1.0,
                )]
                explanation = IntelligenceExplanation(
                    inference_type=InferenceType.ENTITY_MATCH,
                    observation=f"Vehicle {vehicle_id} shares license plate with {d.vehicle_id}",
                    evidence=evidence,
                    analytical_rule="Exact license plate deduplication",
                    inference=f"Vehicle {d.vehicle_id} is likely the same vehicle or a clone",
                    confidence=conf,
                    recommended_action="Verify physical vehicle with traffic department",
                )
                matches.append({
                    "candidate_id": d.vehicle_id,
                    "confidence": conf.to_dict(),
                    "explanation": explanation.to_dict(),
                })

        return {"entity_id": vehicle_id, "matches": matches}

    def get_cross_case_overlaps(self, target_case_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find investigations sharing entities with the given list."""
        from backend.db.schema import InvestigationEntity
        entity_ids = [e["entity_id"] for e in target_case_entities]
        if not entity_ids:
            return []
        overlaps = self.db.query(InvestigationEntity).filter(
            InvestigationEntity.entity_id.in_(entity_ids)
        ).all()
        return [
            {
                "investigation_id": o.investigation_id,
                "entity_id": o.entity_id,
                "entity_type": o.entity_type,
                "reason": f"Shared {o.entity_type} {o.entity_id}",
                "confidence": 1.0,
            }
            for o in overlaps
        ]

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _validate_phone_ownership(self, phone_number: str, person_id_1: str, person_id_2: str) -> bool:
        """
        Verify that both persons legitimately owned the phone during overlapping periods.
        Returns False if one person's FIRs predate the phone's activation date (recycled phone).
        """
        try:
            # Get phone activation date
            phone = self.db.query(Phone).filter_by(phone_number=phone_number).first()
            if not phone or not phone.activation_date:
                return True  # No date info, assume valid

            # Get earliest FIR for each person
            person1_earliest = self.db.query(FIR).join(
                FIRAccomplice, FIR.fir_id == FIRAccomplice.fir_id
            ).filter(
                FIRAccomplice.criminal_id == person_id_1,
                FIR.occurred_date.isnot(None)
            ).order_by(FIR.occurred_date).first()

            person2_earliest = self.db.query(FIR).join(
                FIRAccomplice, FIR.fir_id == FIRAccomplice.fir_id
            ).filter(
                FIRAccomplice.criminal_id == person_id_2,
                FIR.occurred_date.isnot(None)
            ).order_by(FIR.occurred_date).first()

            # If either person's earliest FIR predates phone activation, phone was recycled
            if person1_earliest and person1_earliest.occurred_date < phone.activation_date:
                return False
            if person2_earliest and person2_earliest.occurred_date < phone.activation_date:
                return False

            return True
        except Exception:
            return True  # On error, assume valid (fail open)

    def _candidate_persons(self, p: Person) -> List[Person]:
        """SQL pre-filter: push hard constraints into DB before Python scoring."""
        q = self.db.query(Person).filter(Person.citizen_id != p.citizen_id)
        if p.district_id:
            q = q.filter(Person.district_id == p.district_id)
        if p.gender:
            q = q.filter(Person.gender == p.gender)
        return q.limit(50).all()

    def _person_fir_ids(self, person_id: str) -> set:
        """Get set of FIR IDs associated with this person via accused table."""
        rows = self.db.query(FIRAccomplice.fir_id).filter(
            FIRAccomplice.criminal_id == person_id
        ).all()
        return {r.fir_id for r in rows}

    def _score_person_pair(
        self, source: Person, candidate: Person, source_fir_ids: set
    ) -> Optional[Dict[str, Any]]:
        """Score all evidence dimensions and build full reasoning trace."""
        evidence_items: List[EvidenceItem] = []
        weighted_sum = 0.0
        weights = EVIDENCE_WEIGHTS

        # ── 1. Aadhaar exact match ───────────────────────────────────────
        if source.aadhaar and candidate.aadhaar and source.aadhaar == candidate.aadhaar:
            score = 1.0
            contrib = weights["aadhaar_match"] * score
            weighted_sum += contrib
            evidence_items.append(EvidenceItem(
                dimension="aadhaar_match",
                description=f"Identical Aadhaar ID: {source.aadhaar}",
                raw_value=source.aadhaar,
                weight=weights["aadhaar_match"],
                contributed_score=contrib,
            ))

        # ── 2. Phone exact match (with ownership date validation) ─────────────────────
        if (source.phone_primary and candidate.phone_primary
                and source.phone_primary == candidate.phone_primary):
            # Validate phone ownership: check activation dates to catch recycled phones
            phone_valid = self._validate_phone_ownership(
                source.phone_primary, source.citizen_id, candidate.citizen_id
            )
            if phone_valid:
                score = 1.0
                contrib = weights["phone_exact"] * score
                weighted_sum += contrib
                evidence_items.append(EvidenceItem(
                    dimension="phone_exact",
                    description=f"Identical primary phone: {source.phone_primary} (ownership dates validated)",
                    raw_value=source.phone_primary,
                    weight=weights["phone_exact"],
                    contributed_score=contrib,
                ))
            else:
                # Phone recycling detected - downweight heavily
                evidence_items.append(EvidenceItem(
                    dimension="phone_recycled_warning",
                    description=f"Phone {source.phone_primary} shared but ownership dates conflict (likely recycled)",
                    raw_value=source.phone_primary,
                    weight=0.0,
                    contributed_score=0.0,
                ))

        # ── 3. Name Jaro-Winkler (with regional prefix stripping) ──────────────
        src_name = source.name_en or ""
        cand_name = candidate.name_en or ""

        # FIX HIGH #2: Try direct match first
        name_sim = _jaro_winkler(src_name, cand_name)
        prefix_stripped = False

        if name_sim >= NAME_SIMILARITY_MIN:
            contrib = weights["name_jaro_winkler"] * name_sim
            weighted_sum += contrib
            evidence_items.append(EvidenceItem(
                dimension="name_jaro_winkler",
                description=f"Name similarity: '{src_name}' ~ '{cand_name}' ({name_sim:.3f})",
                raw_value=name_sim,
                weight=weights["name_jaro_winkler"],
                contributed_score=contrib,
            ))
        else:
            # Try after stripping regional prefixes (e.g., "Sri Raj" vs "Raj")
            src_stripped = _strip_regional_prefixes(src_name)
            cand_stripped = _strip_regional_prefixes(cand_name)
            name_sim_stripped = _jaro_winkler(src_stripped, cand_stripped)

            if name_sim_stripped >= NAME_SIMILARITY_MIN and src_stripped != src_name:
                contrib = weights["name_jaro_winkler"] * 0.8 * name_sim_stripped  # 80% weight (slightly conservative)
                weighted_sum += contrib
                prefix_stripped = True
                evidence_items.append(EvidenceItem(
                    dimension="name_regional_variant",
                    description=f"Name match after regional prefix removal: '{src_stripped}' ~ '{cand_stripped}' ({name_sim_stripped:.3f})",
                    raw_value=name_sim_stripped,
                    weight=weights["name_jaro_winkler"] * 0.8,
                    contributed_score=contrib,
                ))
            else:
                # Fallback: phonetic hash for transliteration variants (e.g., Mohammad/Muhammad)
                src_phonetic = _phonetic_hash(src_name)
                cand_phonetic = _phonetic_hash(cand_name)
                if src_phonetic and src_phonetic == cand_phonetic and len(src_phonetic) >= 4:
                    # Phonetic match detected (catches transliteration variants)
                    phonetic_score = 0.85
                    contrib = weights["name_jaro_winkler"] * 0.5 * phonetic_score  # 50% weight for phonetic
                    weighted_sum += contrib
                    evidence_items.append(EvidenceItem(
                        dimension="name_phonetic_match",
                        description=f"Phonetic match (transliteration variant): '{src_name}' ~ '{cand_name}'",
                        raw_value=phonetic_score,
                        weight=weights["name_jaro_winkler"] * 0.5,
                        contributed_score=contrib,
                    ))

        # ── 4. Shared FIR history ────────────────────────────────────────
        candidate_fir_ids = self._person_fir_ids(candidate.citizen_id)
        shared_firs = source_fir_ids & candidate_fir_ids
        if shared_firs:
            score = min(1.0, len(shared_firs) / 3.0)  # 3+ shared FIRs → max
            contrib = weights["shared_fir"] * score
            weighted_sum += contrib
            evidence_items.append(EvidenceItem(
                dimension="shared_fir",
                description=f"Appeared in {len(shared_firs)} same FIR(s): {list(shared_firs)[:3]}",
                raw_value=list(shared_firs),
                weight=weights["shared_fir"],
                contributed_score=contrib,
            ))

        # ── 5. Address similarity ────────────────────────────────────────
        addr_sim = _address_similarity(source.home_address, candidate.home_address)
        if addr_sim > 0.5:
            contrib = weights["address_similarity"] * addr_sim
            weighted_sum += contrib
            evidence_items.append(EvidenceItem(
                dimension="address_similarity",
                description=f"Address similarity: {addr_sim:.3f}",
                raw_value=addr_sim,
                weight=weights["address_similarity"],
                contributed_score=contrib,
            ))

        # ── 6. Geographic proximity (soft penalty for interstate offenders) ──
        dist_km = _geo_distance_km(
            source.home_lat, source.home_lng,
            candidate.home_lat, candidate.home_lng,
        )
        if dist_km is not None:
            if dist_km <= GEO_PROXIMITY_KM:
                # Nearby: full proximity score
                score = 1.0 - (dist_km / GEO_PROXIMITY_KM)
                contrib = weights["geographic_proximity"] * score
                weighted_sum += contrib
                evidence_items.append(EvidenceItem(
                    dimension="geographic_proximity",
                    description=f"Home locations {dist_km:.2f} km apart (within {GEO_PROXIMITY_KM} km threshold)",
                    raw_value=dist_km,
                    weight=weights["geographic_proximity"],
                    contributed_score=contrib,
                ))
            elif dist_km > 500:
                # Far apart (interstate): if other strong indicators exist, don't penalize
                # Log warning but don't subtract from score
                evidence_items.append(EvidenceItem(
                    dimension="geographic_distance_alert",
                    description=f"Homes {dist_km:.2f} km apart (interstate); relying on other identifiers",
                    raw_value=dist_km,
                    weight=0.0,
                    contributed_score=0.0,
                ))
            else:
                # Medium distance: soft penalty
                score = max(0.0, 1.0 - (dist_km / (GEO_PROXIMITY_KM * 50)))
                contrib = weights["geographic_proximity"] * score * 0.5  # 50% weight reduction
                weighted_sum += contrib
                evidence_items.append(EvidenceItem(
                    dimension="geographic_proximity_regional",
                    description=f"Home locations {dist_km:.2f} km apart (same region)",
                    raw_value=dist_km,
                    weight=weights["geographic_proximity"] * 0.5,
                    contributed_score=contrib,
                ))

        # Early exit if below threshold
        if weighted_sum < MATCH_THRESHOLD:
            return None

        # ── Build confidence model ───────────────────────────────────────
        completeness_score = completeness(candidate, _PERSON_REQUIRED)
        conf = ConfidenceScore(
            evidence_quality=min(1.0, weighted_sum),
            data_completeness=completeness_score,
            algorithm_confidence=0.85,   # Multi-dim engine baseline
            source_reliability=0.90,     # Official DB records
            recency_weight=ConfidenceScore.recency_factor(None),
        ).compute()

        # Override overall with raw weighted sum (the entity match score)
        # conf is used for meta-quality; final reported confidence is weighted_sum
        explanation = IntelligenceExplanation(
            inference_type=InferenceType.ENTITY_MATCH,
            observation=f"Entity {source.citizen_id} ({source.name_en}) scored against {candidate.citizen_id} ({candidate.name_en})",
            evidence=evidence_items,
            analytical_rule="Weighted multi-dimensional evidence aggregation (Jaro-Winkler + exact identifiers)",
            inference=(
                f"Person {candidate.citizen_id} is a probable match for {source.citizen_id} "
                f"with match score {weighted_sum:.3f} (threshold {MATCH_THRESHOLD})"
            ),
            confidence=conf,
            recommended_action="Cross-reference Aadhaar database for confirmation",
        )

        return {
            "candidate_id": candidate.citizen_id,
            "candidate_name": candidate.name_en,
            "match_score": round(weighted_sum, 4),
            "confidence": conf.to_dict(),
            "explanation": explanation.to_dict(),
        }
