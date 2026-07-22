"""Phase 8.2 Assignment & Workload Management package.

Public contract surface for the assignment engine. Milestones 2–5 build
against the models exported here without needing to know internal details.
"""

from backend.assignment.contracts import (
    AssignmentScore,
    CapacityDetails,
    CapacityViolation,
    RejectionReason,
    WorkloadSummary,
    ScoringContext,
    RankedRecommendation,
)
from backend.assignment.officer_repository import OfficerRepository
from backend.assignment.availability import (
    AvailabilityStateManager,
    AvailabilityTransitionError,
)
from backend.assignment.capacity_service import OfficerCapacityService
from backend.assignment.reconciliation import ReconciliationService
from backend.assignment.scoring_engine import AssignmentScoringEngine
from backend.assignment.recommendation_service import RecommendationService

__all__ = [
    "AssignmentScore",
    "CapacityDetails",
    "CapacityViolation",
    "RejectionReason",
    "WorkloadSummary",
    "ScoringContext",
    "RankedRecommendation",
    "OfficerRepository",
    "AvailabilityStateManager",
    "AvailabilityTransitionError",
    "OfficerCapacityService",
    "ReconciliationService",
    "AssignmentScoringEngine",
    "RecommendationService",
]
