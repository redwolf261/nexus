"""Assignment Aggregate (Phase 8.2 Milestone 4).

DDD Domain Aggregate encapsulating investigation assignment lifecycle, history,
validation status, recommendation metadata, workload snapshot, and policy version.

Serves as the single domain object operating between the AssignmentService and
consumers (M5 Supervisor Dashboard, Phase 8.4 Approval workflows, Phase 10 LLM).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.assignment.contracts import (
    AssignmentScore,
    OfficerWorkload,
    AssignmentValidationResult,
    RankedRecommendation,
)


@dataclass(frozen=True)
class AssignmentHistoryRecord:
    """Immutable snapshot of a single assignment event within the aggregate."""
    id: str
    assignment_id: str
    investigation_id: str
    officer_id: str
    assigned_by: str
    timestamp: datetime
    reason: Optional[str] = None
    recommendation_score: Optional[float] = None
    policy_version: Optional[str] = None
    manual_override: bool = False
    override_reason: Optional[str] = None
    previous_officer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "investigation_id": self.investigation_id,
            "officer_id": self.officer_id,
            "assigned_by": self.assigned_by,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "reason": self.reason,
            "recommendation_score": self.recommendation_score,
            "policy_version": self.policy_version,
            "manual_override": self.manual_override,
            "override_reason": self.override_reason,
            "previous_officer": self.previous_officer,
        }


@dataclass
class AssignmentAggregate:
    """DDD Aggregate for an Investigation's Assignment Context.

    Encapsulates:
      - Current assignment state
      - Version (optimistic concurrency token)
      - Append-only assignment history
      - Current validation result
      - Latest recommendation list / top recommendation score
      - Officer workload snapshot
      - Active policy version
    """

    investigation_id: str
    current_officer_id: Optional[str]
    investigation_status: str
    investigation_priority: str
    version: int
    policy_version: str

    # Component state
    history: List[AssignmentHistoryRecord] = field(default_factory=list)
    validation: Optional[AssignmentValidationResult] = None
    top_recommendation: Optional[RankedRecommendation] = None
    officer_workload: Optional[OfficerWorkload] = None

    @property
    def is_assigned(self) -> bool:
        return self.current_officer_id is not None and len(self.current_officer_id.strip()) > 0

    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid if self.validation else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "current_officer_id": self.current_officer_id,
            "investigation_status": self.investigation_status,
            "investigation_priority": self.investigation_priority,
            "version": self.version,
            "policy_version": self.policy_version,
            "is_assigned": self.is_assigned,
            "is_valid": self.is_valid,
            "history": [h.to_dict() for h in self.history],
            "validation": self.validation.to_dict() if self.validation else None,
            "top_recommendation": self.top_recommendation.to_dict() if self.top_recommendation else None,
            "officer_workload": self.officer_workload.to_dict() if self.officer_workload else None,
        }
