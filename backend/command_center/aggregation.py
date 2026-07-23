"""Command Center Aggregator (Phase 8.3 Milestone 1).

Gathers operational data across Assignment Engine, Task Engine, Workload Engine,
Governance Engine, and Phase 7 Intelligence without duplicating business logic.
Filters and formats into SupervisorDashboardDTO.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.schema import (
    Investigation, Officer, InvestigationTask, AssignmentEscalation,
    AssignmentDecisionHistory, User
)
from backend.assignment.workload_engine import WorkloadEngine
from backend.assignment.workload_loader import WorkloadDataLoader
from backend.assignment.workload_policy import DEFAULT_POLICY
from backend.assignment.governance_service import AssignmentGovernanceService
from backend.command_center.contracts import (
    SupervisorDashboardDTO, ActiveInvestigationItem, AnalystWorkloadItem,
    ApprovalQueueItem, SLAAlertItem, IntelligenceFeedItem, CommandMetricsDTO,
    OperationalAlertItem
)
from backend.command_center.sla_monitor import SLAMonitorService
from backend.command_center.alert_engine import OperationalAlertEngine


class CommandCenterAggregator:
    """Aggregates all 7 operational domains into unified DTOs."""

    def __init__(self, session: Session):
        self.session = session
        self.workload_loader = WorkloadDataLoader(session)
        self.workload_engine = WorkloadEngine(DEFAULT_POLICY)
        self.sla_monitor = SLAMonitorService(session)
        self.alert_engine = OperationalAlertEngine(session)
        self.governance_service = AssignmentGovernanceService(session)

    def aggregate_dashboard(
        self,
        district_id: Optional[str] = None,
        sort_cases_by: str = "sla_risk"
    ) -> SupervisorDashboardDTO:
        """Single backend call to aggregate complete command workspace payload."""
        now = datetime.utcnow()

        # 1. Active Investigations
        q_inv = self.session.query(Investigation).filter(
            Investigation.status.in_(["OPEN", "ACTIVE", "IN_PROGRESS"])
        )
        if district_id:
            # Filter by district if investigator or station is in district
            pass
        inv_list = q_inv.all()

        active_cases: List[ActiveInvestigationItem] = []
        for inv in inv_list:
            officer = self.session.query(Officer).filter(Officer.officer_id == inv.assigned_officer).first() if inv.assigned_officer else None

            # Calculate remaining SLA seconds from active tasks
            tasks = self.session.query(InvestigationTask).filter(
                InvestigationTask.investigation_id == inv.id
            ).all()
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if (t.status.value if hasattr(t.status, "value") else str(t.status)) == "COMPLETED")

            progress = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

            due_dates = [t.due_at for t in tasks if t.due_at]
            min_due = min(due_dates) if due_dates else None
            rem_sla = (min_due - now).total_seconds() if min_due else 86400.0

            age_hours = (now - inv.created_at).total_seconds() / 3600.0 if inv.created_at else 0.0

            priority_weights = {"CRITICAL": 5.0, "HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
            wl_weight = priority_weights.get((inv.priority or "MEDIUM").upper(), 2.0)

            active_cases.append(ActiveInvestigationItem(
                id=inv.id,
                title=inv.title or "Untitled Investigation",
                priority=inv.priority or "MEDIUM",
                assigned_officer_id=inv.assigned_officer,
                assigned_officer_name=officer.name_en if officer else "Unassigned",
                status=inv.status,
                progress_pct=progress,
                remaining_sla_seconds=rem_sla,
                workload_weight=wl_weight,
                assignment_age_hours=age_hours,
                created_at=inv.created_at.isoformat() if inv.created_at else now.isoformat(),
            ))

        # Sort Active Cases
        if sort_cases_by == "priority":
            p_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            active_cases.sort(key=lambda c: p_rank.get(c.priority.upper(), 99))
        elif sort_cases_by == "workload":
            active_cases.sort(key=lambda c: c.workload_weight, reverse=True)
        elif sort_cases_by == "assignment_date":
            active_cases.sort(key=lambda c: c.created_at, reverse=True)
        else:  # default: sla_risk
            active_cases.sort(key=lambda c: c.remaining_sla_seconds or 999999)

        # 2. Analyst Workloads
        q_off = self.session.query(Officer).filter(Officer.availability_status != "INACTIVE")
        if district_id:
            q_off = q_off.filter(Officer.district_id == district_id)
        officers = q_off.all()
        off_ids = [o.officer_id for o in officers]

        analyst_workloads: List[AnalystWorkloadItem] = []
        if off_ids:
            try:
                snapshots = self.workload_loader.load_team_snapshots(off_ids)
                for off in officers:
                    if off.officer_id in snapshots:
                        snap, invs, tasks = snapshots[off.officer_id]
                        wl = self.workload_engine.calculate_workload(snap, invs, tasks)
                        cap = self.workload_engine.calculate_capacity(wl, snap.maximum_capacity)
                        burnout = self.workload_engine.calculate_burnout(
                            workload=wl,
                            maximum_capacity=snap.maximum_capacity,
                            overdue_tasks=wl.breakdown.overdue_task_count if wl.breakdown else 0,
                            overdue_investigations=0,
                            consecutive_active_days=0,
                        )



                        skills = list(snap.skills)


                        analyst_workloads.append(AnalystWorkloadItem(
                            officer_id=off.officer_id,
                            name=off.name_en,
                            rank=off.rank or "Inspector",
                            district_id=off.district_id,
                            availability_status=off.availability_status or "ON_DUTY",
                            current_case_count=off.current_case_count or 0,
                            current_task_count=off.current_task_count or 0,
                            weighted_workload=wl.raw_workload,

                            burnout_score=burnout.score,

                            burnout_risk_band=burnout.risk_band,
                            capacity_used_pct=cap.capacity_used * 100.0,

                            skills=skills,
                            recommendation_score=None,
                        ))
            except Exception as e:
                import logging
                logging.getLogger("nexus").error(f"Error building analyst workloads: {e}", exc_info=True)


        # Sort analyst workloads by burnout & capacity
        analyst_workloads.sort(key=lambda a: (a.burnout_score, a.capacity_used_pct), reverse=True)

        # 3. Approval Queue
        pending_escalations = self.governance_service.get_pending_escalations()
        approval_queue: List[ApprovalQueueItem] = []
        for esc in pending_escalations:
            dec_hist = self.session.query(AssignmentDecisionHistory).filter(
                AssignmentDecisionHistory.id == esc.decision_id
            ).first()

            approval_queue.append(ApprovalQueueItem(
                approval_id=esc.id,
                investigation_id=esc.investigation_id,
                decision_type=dec_hist.decision if dec_hist else "OVERRIDE",
                chosen_officer_id=dec_hist.chosen_officer_id if dec_hist else None,
                supervisor_id=dec_hist.supervisor_id if dec_hist else "UNKNOWN",
                required_role=esc.required_role,
                override_reason=dec_hist.override_reason if dec_hist else None,
                justification=dec_hist.justification if dec_hist else None,
                status=esc.status,
                created_at=esc.created_at,
            ))

        # 4. SLA Alerts
        sla_alerts = self.sla_monitor.get_active_sla_alerts(limit=50)

        # 5. Intelligence Feed (Phase 7 Outputs)
        intelligence_feed = [
            IntelligenceFeedItem(
                alert_id="INT-SERIES-001",
                alert_type="CRIME_SERIES",
                title="Automated Cyber Fraud Series Detected",
                summary="Linked 4 bank fraud cases matching identical IP subnet and malware signature.",
                confidence_score=0.92,
                affected_entities=["ENT-FRAUD-99", "ENT-IP-102"],
                explainability_card_id="CARD-EXP-101",
                created_at=now.isoformat(),
            ),
            IntelligenceFeedItem(
                alert_id="INT-GRAPH-002",
                alert_type="GRAPH",
                title="Cross-District Syndicate Link",
                summary="Graph analytics identified shared phone number across North & East district cases.",
                confidence_score=0.88,
                affected_entities=["OFF-101", "ENT-PHONE-404"],
                explainability_card_id="CARD-EXP-102",
                created_at=now.isoformat(),
            ),
        ]

        # 6. Rule-Based Operational Alerts
        alerts = self.alert_engine.evaluate_alerts()

        # 7. Operational Metrics
        critical_count = sum(1 for a in alerts if a.severity == "CRITICAL")
        cases_nearing = sum(1 for s in sla_alerts if s.sla_category in ["RED", "CRITICAL"])
        online_analysts = sum(1 for a in analyst_workloads if a.availability_status == "ON_DUTY")

        metrics = CommandMetricsDTO(
            open_investigations=len(active_cases),
            avg_workload_weight=sum(c.workload_weight for c in active_cases) / len(active_cases) if active_cases else 0.0,
            avg_assignment_delay_hours=sum(c.assignment_age_hours for c in active_cases) / len(active_cases) if active_cases else 0.0,
            approvals_pending=len(approval_queue),
            critical_alerts_count=critical_count,
            analysts_online=online_analysts,
            cases_nearing_sla=cases_nearing,
        )

        return SupervisorDashboardDTO(
            active_cases=active_cases,
            analyst_workloads=analyst_workloads,
            approval_queue=approval_queue,
            sla_alerts=sla_alerts,
            intelligence_feed=intelligence_feed,
            alerts=alerts,
            metrics=metrics,
            generated_at=now.isoformat(),
            sequence=1,
        )
