"""
Explainability layer for the NEXUS Analytical Intelligence Engine.

Every analytical inference is wrapped in an IntelligenceExplanation
before being returned to callers. This enforces the provenance chain:

    Observation → Evidence → Analytical Rule → Inference → Confidence → Recommended Action

No "black box" results may be returned by any Phase 7 module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from backend.intelligence.confidence import ConfidenceScore


class InferenceType(str, Enum):
    ENTITY_MATCH = "ENTITY_MATCH"
    CRIME_SERIES = "CRIME_SERIES"
    GRAPH_COMMUNITY = "GRAPH_COMMUNITY"
    GRAPH_CENTRALITY = "GRAPH_CENTRALITY"
    GRAPH_LINK_PREDICTION = "GRAPH_LINK_PREDICTION"
    TEMPORAL_ANOMALY = "TEMPORAL_ANOMALY"
    SPATIAL_CLUSTER = "SPATIAL_CLUSTER"
    TRAVEL_CORRIDOR = "TRAVEL_CORRIDOR"
    RISK_SCORE = "RISK_SCORE"


@dataclass
class EvidenceItem:
    """A single piece of evidence supporting an inference."""
    dimension: str          # e.g. "name_jaro_winkler", "shared_fir"
    description: str        # Human-readable description
    raw_value: Any          # The underlying raw value (score, id, etc.)
    weight: float           # Contribution weight in [0, 1]
    contributed_score: float  # weight × partial_score

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "description": self.description,
            "raw_value": self.raw_value,
            "weight": round(self.weight, 4),
            "contributed_score": round(self.contributed_score, 4),
        }


@dataclass
class IntelligenceExplanation:
    """
    Complete provenance record for a single analytical inference.

    Fields mirror the standard reasoning chain:
        observation → evidence → rule → inference → confidence → action
    """
    inference_type: InferenceType
    observation: str                        # What was observed
    evidence: List[EvidenceItem]            # Supporting evidence items
    analytical_rule: str                    # Algorithm / rule name
    inference: str                          # The conclusion drawn
    confidence: ConfidenceScore             # Structured confidence
    recommended_action: Optional[str] = None
    alternative_explanations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "inference_type": self.inference_type.value,
            "observation": self.observation,
            "evidence": [e.to_dict() for e in self.evidence],
            "analytical_rule": self.analytical_rule,
            "inference": self.inference,
            "confidence": self.confidence.to_dict(),
            "recommended_action": self.recommended_action,
            "alternative_explanations": self.alternative_explanations,
            "metadata": self.metadata,
        }

    def summary_text(self) -> str:
        """Generate a concise human-readable summary."""
        conf_pct = round(self.confidence.overall_confidence * 100, 1)
        lines = [
            f"[{self.inference_type.value}] Confidence: {conf_pct}%",
            f"Observation: {self.observation}",
            f"Inference:   {self.inference}",
            f"Algorithm:   {self.analytical_rule}",
            "Evidence:",
        ]
        for ev in self.evidence:
            lines.append(f"  • {ev.description} (contributed {ev.contributed_score:.3f})")
        if self.recommended_action:
            lines.append(f"Action: {self.recommended_action}")
        if self.alternative_explanations:
            lines.append("Alternatives: " + "; ".join(self.alternative_explanations))
        return "\n".join(lines)
