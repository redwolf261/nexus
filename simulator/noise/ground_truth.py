"""
NEXUS Simulator — Entity Resolution Ground Truth
Maintains the canonical entity mapping table.
Maps all alias records back to their true canonical IDs.
Exported separately for evaluation / benchmarking.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class EntityResolutionRecord:
    """One row in the ground truth entity resolution table."""
    canonical_id: str           # The true entity ID (e.g. CRM-0000001)
    canonical_name: str
    alias_id: Optional[str]     # Alias record ID (e.g. FIR-xxx-NOISE)
    alias_value: str            # The alias string or noisy record ID
    alias_type: str             # "name_variant" | "duplicate_fir" | "ocr_error" | "abbreviation" | "kannada"
    confidence: float           # How confident we are this alias maps to canonical (1.0 = certain)
    source_module: str          # Which noise module created this


class EntityResolutionGroundTruth:
    """
    Accumulates all ground truth entity resolution mappings
    across the simulation.
    """

    def __init__(self) -> None:
        self._records: List[EntityResolutionRecord] = []

    def add(
        self,
        canonical_id: str,
        canonical_name: str,
        alias_value: str,
        alias_type: str,
        confidence: float = 1.0,
        alias_id: Optional[str] = None,
        source_module: str = "noise",
    ) -> None:
        self._records.append(EntityResolutionRecord(
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            alias_id=alias_id,
            alias_value=alias_value,
            alias_type=alias_type,
            confidence=confidence,
            source_module=source_module,
        ))

    def add_from_noise_map(self, noise_map: Dict[str, str], fir_map: Dict[str, object]) -> None:
        """
        Bulk-add from noise injector's noise_map {noisy_id: canonical_id}.
        """
        for noisy_id, canonical_id in noise_map.items():
            fir = fir_map.get(canonical_id)
            canonical_name = fir.complainant_name if fir else "Unknown"
            self.add(
                canonical_id=canonical_id,
                canonical_name=canonical_name,
                alias_value=noisy_id,
                alias_id=noisy_id,
                alias_type="duplicate_fir",
                confidence=1.0,
                source_module="noise_injector",
            )

    def add_criminal_aliases(
        self,
        criminal_id: str,
        canonical_name: str,
        aliases: List[str],
    ) -> None:
        """Add name aliases for a criminal."""
        for alias in aliases:
            alias_type = "kannada" if any(ord(c) > 3000 for c in alias) else "name_variant"
            self.add(
                canonical_id=criminal_id,
                canonical_name=canonical_name,
                alias_value=alias,
                alias_type=alias_type,
                confidence=1.0,
                source_module="alias_generator",
            )

    def to_records(self) -> List[Dict]:
        """Return all records as list of dicts for export."""
        return [
            {
                "canonical_id": r.canonical_id,
                "canonical_name": r.canonical_name,
                "alias_id": r.alias_id or "",
                "alias_value": r.alias_value,
                "alias_type": r.alias_type,
                "confidence": r.confidence,
                "source_module": r.source_module,
            }
            for r in self._records
        ]

    def __len__(self) -> int:
        return len(self._records)
