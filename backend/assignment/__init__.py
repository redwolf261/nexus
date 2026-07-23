"""Phase 8.2 Assignment & Workload Management package.

Public contract surface for the assignment + workload engines.
Milestones 2–5 build against the models exported here without needing
to know internal details.
"""

from backend.assignment.contracts import (
    AssignmentScore,
    CapacityDetails,
    CapacityViolation,
    RejectionReason,
    WorkloadSummary,
    ScoringContext,
    RankedRecommendation,
    # Milestone 3: Workload Engine DTOs
    WorkloadBreakdown,
    OfficerWorkload,
    BurnoutAssessment,
    CapacityMetrics,
    TeamMetrics,
    RebalanceRecommendation,
    # Milestone 4: Assignment Service DTOs
    AssignmentValidationResult,
    CompletionEstimate,
    BulkRecommendationItem,
    AssignmentRecordDTO,
    # Milestone 5: Governance DTOs
    GovernanceMetricsDTO,
    EscalationItemDTO,
    SnapshotDTO,
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

# Milestone 3: Workload Engine
from backend.assignment.workload_policy import WorkloadPolicy, DEFAULT_POLICY
from backend.assignment.workload_engine import (
    WorkloadEngine,
    OfficerSnapshot,
    InvestigationSnapshot,
    TaskSnapshot,
)
from backend.assignment.workload_loader import WorkloadDataLoader

# Milestone 4: Assignment Service & Aggregate
from backend.assignment.aggregate import AssignmentAggregate, AssignmentHistoryRecord
from backend.assignment.assignment_service import AssignmentService

# Milestone 5: Governance & Approval Engine
from backend.assignment.override_policy import (
    OverridePolicyEngine, ApprovalPolicy, PolicyResult, DecisionEnum, OverrideReasonEnum
)
from backend.assignment.decision_aggregate import AssignmentDecision
from backend.assignment.governance_service import AssignmentGovernanceService

__all__ = [
    # M1: Contracts
    "AssignmentScore",
    "CapacityDetails",
    "CapacityViolation",
    "RejectionReason",
    "WorkloadSummary",
    "ScoringContext",
    "RankedRecommendation",
    # M3: Workload DTOs
    "WorkloadBreakdown",
    "OfficerWorkload",
    "BurnoutAssessment",
    "CapacityMetrics",
    "TeamMetrics",
    "RebalanceRecommendation",
    # M4: Assignment DTOs
    "AssignmentValidationResult",
    "CompletionEstimate",
    "BulkRecommendationItem",
    "AssignmentRecordDTO",
    # M5: Governance DTOs
    "GovernanceMetricsDTO",
    "EscalationItemDTO",
    "SnapshotDTO",
    # M1: Services
    "OfficerRepository",
    "AvailabilityStateManager",
    "AvailabilityTransitionError",
    "OfficerCapacityService",
    "ReconciliationService",
    # M2: Scoring
    "AssignmentScoringEngine",
    "RecommendationService",
    # M3: Workload Engine
    "WorkloadPolicy",
    "DEFAULT_POLICY",
    "WorkloadEngine",
    "OfficerSnapshot",
    "InvestigationSnapshot",
    "TaskSnapshot",
    "WorkloadDataLoader",
    # M4: Service & Aggregate
    "AssignmentAggregate",
    "AssignmentHistoryRecord",
    "AssignmentService",
    # M5: Governance
    "OverridePolicyEngine",
    "ApprovalPolicy",
    "PolicyResult",
    "DecisionEnum",
    "OverrideReasonEnum",
    "AssignmentDecision",
    "AssignmentGovernanceService",
]
