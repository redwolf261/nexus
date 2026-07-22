"""
Confidence propagation framework for the NEXUS Analytical Intelligence Engine.

Every analytical result carries a structured ConfidenceScore instead of
a raw float. This ensures that consumers of analytical APIs understand
the provenance and reliability of each inference.

Mathematical formulation (weighted geometric mean):
    overall = (evidence_quality^w1 × data_completeness^w2
               × algorithm_confidence^w3 × source_reliability^w4
               × recency_weight^w5) ^ (1 / sum_of_weights)

Geometric mean is used instead of arithmetic mean because a single
zero-dimension (e.g. no data at all) should drag the overall confidence
close to zero rather than merely reducing it.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, date
import math


@dataclass
class ConfidenceScore:
    """
    Structured confidence score for any analytical inference.

    All component scores are in [0.0, 1.0].
    overall_confidence is computed on demand via compute().
    """
    evidence_quality: float = 1.0       # How clean / reliable is the raw data?
    data_completeness: float = 1.0      # What fraction of expected fields are present?
    algorithm_confidence: float = 1.0   # Intrinsic algorithm certainty
    source_reliability: float = 1.0     # Is the source a verified official record?
    recency_weight: float = 1.0         # Exponential decay based on data age
    overall_confidence: float = field(init=False, default=0.0)

    # Component weights for geometric mean
    _WEIGHTS = (0.25, 0.20, 0.30, 0.15, 0.10)

    def compute(self) -> "ConfidenceScore":
        """Compute overall_confidence using weighted geometric mean."""
        components = [
            self.evidence_quality,
            self.data_completeness,
            self.algorithm_confidence,
            self.source_reliability,
            self.recency_weight,
        ]
        # Clamp to [0.001, 1.0] to avoid log(0)
        clamped = [max(0.001, min(1.0, c)) for c in components]
        weights = self._WEIGHTS
        log_sum = sum(w * math.log(c) for w, c in zip(weights, clamped))
        self.overall_confidence = round(math.exp(log_sum / sum(weights)), 4)
        return self

    def to_dict(self) -> dict:
        return {
            "evidence_quality": round(self.evidence_quality, 4),
            "data_completeness": round(self.data_completeness, 4),
            "algorithm_confidence": round(self.algorithm_confidence, 4),
            "source_reliability": round(self.source_reliability, 4),
            "recency_weight": round(self.recency_weight, 4),
            "overall_confidence": round(self.overall_confidence, 4),
        }

    @staticmethod
    def recency_factor(reference_date: Optional[date], half_life_days: int = 180) -> float:
        """
        Compute exponential decay weight based on how recent the data is.
        Score = 0.5^(days_old / half_life_days)
        Recent data (days_old=0) → 1.0; half-life old data → 0.5.
        """
        if reference_date is None:
            return 0.5  # Unknown date → mid-confidence
        if isinstance(reference_date, datetime):
            reference_date = reference_date.date()
        days_old = (date.today() - reference_date).days
        days_old = max(0, days_old)
        return round(0.5 ** (days_old / half_life_days), 4)


def completeness(obj, required_fields: List[str]) -> float:
    """Compute data completeness: fraction of required fields that are non-null."""
    if not required_fields:
        return 1.0
    filled = sum(1 for f in required_fields if getattr(obj, f, None) is not None)
    return round(filled / len(required_fields), 4)
