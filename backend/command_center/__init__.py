"""Command Center Package (Phase 8.3 Milestones 1, 2, 3, & 4).

Provides aggregated supervisor dashboard DTOs, real-time incremental patch engines,
workspace contracts, unified investigation timelines, operational case health scoring,
deterministic decision support, supervisor action engines, executive KPIs, district analytics,
trend statistics, heatmaps, and executive aggregators.
"""

from backend.command_center.contracts import (
    SupervisorDashboardDTO,
    ActiveInvestigationItem,
    AnalystWorkloadItem,
    ApprovalQueueItem,
    SLAAlertItem,
    IntelligenceFeedItem,
    CommandMetricsDTO,
    OperationalAlertItem,
    DashboardPatchDTO,
    PresenceStatusDTO,
    NotificationDigestDTO,
    ReplayResponseDTO,
)
from backend.command_center.workspace_contracts import (
    InvestigationWorkspaceDTO,
    TimelineEventDTO,
    CaseHealthDTO,
    DecisionRecommendationDTO,
    SupervisorActionPayload,
)
from backend.command_center.executive_contracts import (
    KPIDTO,
    DistrictAnalyticsDTO,
    TrendDTO,
    HeatmapDTO,
    ExecutiveDashboardDTO,
)
from backend.command_center.sla_monitor import SLAMonitorService
from backend.command_center.alert_engine import OperationalAlertEngine
from backend.command_center.aggregation import CommandCenterAggregator
from backend.command_center.dashboard_service import (
    DashboardAggregationService,
    CacheEntry,
    CacheInvalidationReason,
)
from backend.command_center.subscription_manager import (
    SubscriptionRegistry,
    SupervisorSession,
    DashboardSubscription,
)
from backend.command_center.patch_engine import DeltaComputer, PatchBuilder, DashboardDelta
from backend.command_center.event_router import OperationalEventRouter
from backend.command_center.presence_service import PresenceService
from backend.command_center.notification_pipeline import NotificationPipeline
from backend.command_center.replay_service import ReplayService
from backend.command_center.timeline_service import InvestigationTimelineService
from backend.command_center.case_health_engine import CaseHealthEngine
from backend.command_center.decision_support_engine import DecisionSupportEngine
from backend.command_center.supervisor_action_engine import SupervisorActionEngine
from backend.command_center.workspace_aggregator import InvestigationWorkspaceAggregator
from backend.command_center.kpi_engine import KPIEngine
from backend.command_center.district_analytics import DistrictAnalyticsEngine
from backend.command_center.trend_engine import TrendAnalysisEngine
from backend.command_center.heatmap_engine import HeatmapEngine
from backend.command_center.executive_dashboard import ExecutiveDashboardAggregator

__all__ = [
    "SupervisorDashboardDTO",
    "ActiveInvestigationItem",
    "AnalystWorkloadItem",
    "ApprovalQueueItem",
    "SLAAlertItem",
    "IntelligenceFeedItem",
    "CommandMetricsDTO",
    "OperationalAlertItem",
    "DashboardPatchDTO",
    "PresenceStatusDTO",
    "NotificationDigestDTO",
    "ReplayResponseDTO",
    "InvestigationWorkspaceDTO",
    "TimelineEventDTO",
    "CaseHealthDTO",
    "DecisionRecommendationDTO",
    "SupervisorActionPayload",
    "KPIDTO",
    "DistrictAnalyticsDTO",
    "TrendDTO",
    "HeatmapDTO",
    "ExecutiveDashboardDTO",
    "SLAMonitorService",
    "OperationalAlertEngine",
    "CommandCenterAggregator",
    "DashboardAggregationService",
    "CacheEntry",
    "CacheInvalidationReason",
    "SubscriptionRegistry",
    "SupervisorSession",
    "DashboardSubscription",
    "DeltaComputer",
    "PatchBuilder",
    "DashboardDelta",
    "OperationalEventRouter",
    "PresenceService",
    "NotificationPipeline",
    "ReplayService",
    "InvestigationTimelineService",
    "CaseHealthEngine",
    "DecisionSupportEngine",
    "SupervisorActionEngine",
    "InvestigationWorkspaceAggregator",
    "KPIEngine",
    "DistrictAnalyticsEngine",
    "TrendAnalysisEngine",
    "HeatmapEngine",
    "ExecutiveDashboardAggregator",
]
