"""Operational Alert Engine (Phase 8.3 Milestone 1).

Pure rule-based operational alert engine. Evaluates strict deterministic rules
across officers, tasks, investigations, and approval queues.
Zero AI / ML.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from sqlalchemy.orm import Session

from backend.db.schema import (
    Investigation, Officer, InvestigationTask, AssignmentEscalation,
    AssignmentDecisionHistory, SLAState, TaskStatus
)
from backend.assignment.workload_engine import WorkloadEngine
from backend.assignment.workload_loader import WorkloadDataLoader
from backend.assignment.workload_policy import DEFAULT_POLICY
from backend.command_center.contracts import OperationalAlertItem


class OperationalAlertEngine:
    """Deterministic Operational Alert Engine."""

    def __init__(self, session: Session):
        self.session = session
        self.workload_loader = WorkloadDataLoader(session)
        self.workload_engine = WorkloadEngine(DEFAULT_POLICY)

    def evaluate_alerts(self) -> List[OperationalAlertItem]:
        """Evaluate all operational alert rules and return ordered alert list."""
        alerts: List[OperationalAlertItem] = []
        now = datetime.utcnow()

        # Rule 1: Analyst Capacity Overload & Burnout Threshold
        officers = self.session.query(Officer).filter(Officer.availability_status != "INACTIVE").all()
        off_ids = [o.officer_id for o in officers]
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


                        if cap.capacity_used >= 1.0:
                            alerts.append(OperationalAlertItem(
                                alert_id=f"ALT-CAP-{off.officer_id}-{int(now.timestamp())}",
                                severity="CRITICAL" if cap.capacity_used >= 1.5 else "WARNING",
                                rule_code="ANALYST_OVERLOAD",
                                message=f"Officer '{off.name_en}' ({off.officer_id}) is at {cap.capacity_used * 100.0:.1f}% capacity.",

                                target_id=off.officer_id,
                                timestamp=now.isoformat(),
                            ))

                        if burnout.score >= 75.0:
                            alerts.append(OperationalAlertItem(
                                alert_id=f"ALT-BURN-{off.officer_id}-{int(now.timestamp())}",
                                severity="CRITICAL",
                                rule_code="BURNOUT_THRESHOLD_EXCEEDED",
                                message=f"Burnout risk critical for '{off.name_en}': Score {burnout.score:.1f}/100.",
                                target_id=off.officer_id,
                                timestamp=now.isoformat(),
                            ))

            except Exception:
                pass

        # Rule 2: Unassigned Critical Priority Cases
        unassigned_critical = self.session.query(Investigation).filter(
            Investigation.assigned_officer == None,
            Investigation.priority == "CRITICAL",
            Investigation.status == "OPEN"
        ).all()
        for inv in unassigned_critical:
            alerts.append(OperationalAlertItem(
                alert_id=f"ALT-UNASSIGNED-{inv.id}",
                severity="CRITICAL",
                rule_code="CRITICAL_CASE_UNASSIGNED",
                message=f"CRITICAL investigation '{inv.id}' ({inv.title}) remains unassigned.",
                target_id=inv.id,
                timestamp=now.isoformat(),
            ))

        # Rule 3: Stale Pending Escalation Approvals (> 4 hours)
        four_hours_ago = now - timedelta(hours=4)
        stale_escalations = self.session.query(AssignmentEscalation).filter(
            AssignmentEscalation.status == "PENDING",
            AssignmentEscalation.created_at <= four_hours_ago
        ).all()
        for esc in stale_escalations:
            alerts.append(OperationalAlertItem(
                alert_id=f"ALT-STALE-ESC-{esc.id}",
                severity="WARNING",
                rule_code="APPROVAL_STALE",
                message=f"Escalation approval '{esc.id}' for investigation '{esc.investigation_id}' pending > 4 hours.",
                target_id=esc.id,
                timestamp=now.isoformat(),
            ))

        # Rule 4: Officers Off Duty or on Leave holding active cases
        unavailable_officers = self.session.query(Officer).filter(
            Officer.availability_status.in_(["OFF_DUTY", "LEAVE", "SUSPENDED"]),
            Officer.current_case_count > 0
        ).all()
        for off in unavailable_officers:
            alerts.append(OperationalAlertItem(
                alert_id=f"ALT-OFFICER-UNAVAIL-{off.officer_id}",
                severity="CRITICAL" if off.availability_status == "SUSPENDED" else "WARNING",
                rule_code="OFFICER_OFF_DUTY_WITH_CASES",
                message=f"Officer '{off.name_en}' is {off.availability_status} but holds {off.current_case_count} active cases.",
                target_id=off.officer_id,
                timestamp=now.isoformat(),
            ))

        # Sort alerts: CRITICAL first, then WARNING, INFO
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 99))
        return alerts
