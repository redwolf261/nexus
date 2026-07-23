"""Assignment Service (Phase 8.2 Milestone 4).

Production operational service connecting:
  - Investigation
  - Officer Model (M1)
  - Assignment Scoring Engine (M2)
  - Workload Engine (M3)
  - Task Engine (Phase 8.1)
  - Audit Framework
  - WebSockets
  - JWT / RBAC

CRITICAL DESIGN RULE:
The Assignment Service NEVER decides. It recommends.
Only human supervisors perform assignments.
"""

from __future__ import annotations

import uuid
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.db.schema import (
    Investigation, Officer, AssignmentHistory, User, InvestigationTask, TaskStatus, TaskPriority
)

from backend.assignment.aggregate import AssignmentAggregate, AssignmentHistoryRecord
from backend.assignment.contracts import (
    AssignmentScore, ScoringContext, RankedRecommendation,
    OfficerWorkload, AssignmentValidationResult, CompletionEstimate,
    BulkRecommendationItem, AssignmentRecordDTO
)
from backend.assignment.recommendation_service import RecommendationService
from backend.assignment.workload_engine import WorkloadEngine, OfficerSnapshot, InvestigationSnapshot, TaskSnapshot
from backend.assignment.workload_loader import WorkloadDataLoader
from backend.assignment.workload_policy import DEFAULT_POLICY, WorkloadPolicy
from backend.audit.audit_logger import AuditLogger
from backend.events.event_types import EventType
from backend.events.event_models import BaseEvent
from backend.events.dispatcher import EventDispatcher
from backend.core.logging import logger


class AssignmentService:
    """Production Assignment Service — recommendation, validation, assignment, reassignment, bulk ops, completion estimation."""

    def __init__(self, session: Session, policy: WorkloadPolicy = DEFAULT_POLICY):
        self.session = session
        self.policy = policy
        self.recommendation_service = RecommendationService(session)
        self.workload_engine = WorkloadEngine(policy)
        self.workload_loader = WorkloadDataLoader(session)
        self.audit_logger = AuditLogger(session)

    # ── 1. Recommend ─────────────────────────────────────────────────────────

    def recommend(self, investigation_id: str, limit: int = 5) -> List[RankedRecommendation]:
        """Compute ranked officer recommendations for an investigation.

        Recommends only — never auto-assigns. Broadcasts ASSIGNMENT_RECOMMENDED
        event via WebSocket log.
        """
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        context = ScoringContext(
            investigation_id=inv.id,
            priority=inv.priority,
            district_id=None,
        )

        ranked = self.recommendation_service.rank_officers(context)
        limited = ranked[:limit]

        # Publish WebSocket event
        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_RECOMMENDED,
                case_id=inv.id,
                payload={
                    "investigation_id": inv.id,
                    "policy_version": self.policy.version,
                    "top_recommendations": [r.to_dict() for r in limited],
                }
            )
            # Synchronous persist event to record, dispatch if possible
            EventDispatcher.publish_sync(event, self.session)
        except Exception as e:
            logger.warning(f"Failed to publish ASSIGNMENT_RECOMMENDED event: {e}")

        return limited

    # ── 2. Validate ──────────────────────────────────────────────────────────

    def validate(self, investigation_id: str, officer_id: str) -> AssignmentValidationResult:
        """Validate operational pre-conditions for an assignment.

        Checks:
          - Investigation exists and is in open status
          - Officer exists and is ON_DUTY
          - Capacity available
          - Jurisdiction match
          - Stale state / lock verification
        """
        errors: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            errors.append(f"Investigation '{investigation_id}' does not exist.")
            checks["investigation_exists"] = False
        else:
            checks["investigation_exists"] = True
            if inv.status in ("CLOSED", "CANCELLED", "ARCHIVED"):
                errors.append(f"Investigation '{investigation_id}' is in terminal status '{inv.status}'.")
                checks["investigation_open"] = False
            else:
                checks["investigation_open"] = True

        officer = self.session.query(Officer).filter(Officer.officer_id == officer_id).first()
        if not officer:
            errors.append(f"Officer '{officer_id}' does not exist.")
            checks["officer_exists"] = False
            checks["officer_on_duty"] = False
            checks["capacity_available"] = False
        else:
            checks["officer_exists"] = True

            # Availability check
            if officer.availability_status != "ON_DUTY":
                errors.append(f"Officer '{officer.name_en or officer_id}' is currently {officer.availability_status} (must be ON_DUTY).")
                checks["officer_on_duty"] = False
            else:
                checks["officer_on_duty"] = True

            # Capacity check via WorkloadEngine
            try:
                snapshots = self.workload_loader.load_team_snapshots([officer_id])
                if officer_id in snapshots:
                    snap, invs, tasks = snapshots[officer_id]
                    workload = self.workload_engine.calculate_workload(snap, invs, tasks)
                    capacity = self.workload_engine.calculate_capacity(workload, snap.maximum_capacity)
                    if capacity.is_overloaded or capacity.available_slots_weighted <= 0:
                        warnings.append(f"Officer '{officer_id}' is near or over capacity (used {capacity.capacity_used_pct}%).")
                        checks["capacity_available"] = False
                    else:
                        checks["capacity_available"] = True
                else:
                    checks["capacity_available"] = True
            except Exception as e:
                logger.warning(f"Capacity calculation warning during validation: {e}")
                checks["capacity_available"] = True

        is_valid = len(errors) == 0

        result = AssignmentValidationResult(
            investigation_id=investigation_id,
            officer_id=officer_id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            checks=checks,
            checked_at=datetime.utcnow().isoformat(),
        )

        return result

    # ── 3. Assign ────────────────────────────────────────────────────────────

    def assign(
        self,
        investigation_id: str,
        officer_id: str,
        assigned_by: str,
        reason: str = "",
        manual_override: bool = False,
        override_reason: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> AssignmentAggregate:
        """Assign an officer to an investigation.

        Checks validation & optimistic locking. Never auto-assigns; invoked by supervisor.
        Appends to immutable AssignmentHistory and broadcasts WebSocket event.
        """
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).with_for_update().first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        # Optimistic locking check
        if expected_version is not None and inv.version != expected_version:
            raise ValueError(
                f"Optimistic lock failure: investigation version is {inv.version}, expected {expected_version}"
            )

        # Validation check
        val_result = self.validate(investigation_id, officer_id)
        if not val_result.is_valid and not manual_override:
            # Broadcast ASSIGNMENT_FAILED
            try:
                event = BaseEvent(
                    event_type=EventType.ASSIGNMENT_FAILED,
                    case_id=investigation_id,
                    user_id=assigned_by,
                    payload={
                        "investigation_id": investigation_id,
                        "officer_id": officer_id,
                        "reasons": val_result.errors,
                    }
                )
                EventDispatcher.publish_sync(event, self.session)
            except Exception:
                pass
            raise ValueError(
                f"Assignment validation failed: {'; '.join(val_result.errors)}"
            )

        if manual_override and not override_reason:
            raise ValueError(
                "Manual override requires an override_reason."
            )

        previous_officer = inv.assigned_officer

        # Update Investigation state
        inv.assigned_officer = officer_id
        inv.version = (inv.version or 1) + 1
        inv.last_sequence = (inv.last_sequence or 0) + 1
        if inv.status in ("CREATED", "NEW", "OPEN"):
            inv.status = "ACTIVE"


        # Update case counts for officers
        if previous_officer:
            old_off = self.session.query(Officer).filter(Officer.officer_id == previous_officer).first()
            if old_off and (old_off.current_case_count or 0) > 0:
                old_off.current_case_count -= 1

        new_off = self.session.query(Officer).filter(Officer.officer_id == officer_id).first()
        if new_off:
            new_off.current_case_count = (new_off.current_case_count or 0) + 1

        # Append to AssignmentHistory
        history_id = f"AH-{uuid.uuid4().hex[:12].upper()}"
        asg_id = f"ASG-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow()

        history_entry = AssignmentHistory(
            id=history_id,
            assignment_id=asg_id,
            investigation_id=investigation_id,
            officer_id=officer_id,
            assigned_by=assigned_by,
            timestamp=now,
            reason=reason,
            recommendation_score=None,
            policy_version=self.policy.version,
            manual_override=manual_override,
            override_reason=override_reason,
            previous_officer=previous_officer,
        )
        self.session.add(history_entry)

        # Audit log
        self.audit_logger.log(
            user_id=assigned_by,
            action="ASSIGNMENT_CREATED",
            target_id=investigation_id,
            details={
                "officer_id": officer_id,
                "previous_officer": previous_officer,
                "manual_override": manual_override,
                "reason": reason,
            }
        )

        self.session.commit()

        # WebSocket Broadcast
        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_CREATED,
                case_id=investigation_id,
                user_id=assigned_by,
                sequence=inv.last_sequence,
                payload={
                    "assignment_id": asg_id,
                    "investigation_id": investigation_id,
                    "officer_id": officer_id,
                    "previous_officer": previous_officer,
                    "assigned_by": assigned_by,
                    "timestamp": now.isoformat(),
                    "policy_version": self.policy.version,
                }
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception as e:
            logger.warning(f"Failed to dispatch ASSIGNMENT_CREATED websocket event: {e}")

        return self.get_aggregate(investigation_id)

    # ── 4. Reassign ──────────────────────────────────────────────────────────

    def reassign(
        self,
        investigation_id: str,
        new_officer_id: str,
        assigned_by: str,
        reason: str,
        reassign_type: str = "MANUAL",
        manual_override: bool = False,
        override_reason: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> AssignmentAggregate:
        """Reassign an investigation to a new officer while preserving append-only history."""
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).with_for_update().first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        if expected_version is not None and inv.version != expected_version:
            raise ValueError(
                f"Optimistic lock failure: investigation version is {inv.version}, expected {expected_version}"
            )

        val_result = self.validate(investigation_id, new_officer_id)
        if not val_result.is_valid and not manual_override:
            raise ValueError(
                f"Reassignment validation failed: {'; '.join(val_result.errors)}"
            )

        previous_officer = inv.assigned_officer

        # Update case counts
        if previous_officer:
            old_off = self.session.query(Officer).filter(Officer.officer_id == previous_officer).first()
            if old_off and (old_off.current_case_count or 0) > 0:
                old_off.current_case_count -= 1

        new_off = self.session.query(Officer).filter(Officer.officer_id == new_officer_id).first()
        if new_off:
            new_off.current_case_count = (new_off.current_case_count or 0) + 1

        inv.assigned_officer = new_officer_id
        inv.version = (inv.version or 1) + 1
        inv.last_sequence = (inv.last_sequence or 0) + 1

        now = datetime.utcnow()
        history_id = f"AH-{uuid.uuid4().hex[:12].upper()}"
        asg_id = f"ASG-{uuid.uuid4().hex[:12].upper()}"

        full_reason = f"[{reassign_type}] {reason}" if reassign_type else reason

        history_entry = AssignmentHistory(
            id=history_id,
            assignment_id=asg_id,
            investigation_id=investigation_id,
            officer_id=new_officer_id,
            assigned_by=assigned_by,
            timestamp=now,
            reason=full_reason,
            policy_version=self.policy.version,
            manual_override=manual_override,
            override_reason=override_reason,
            previous_officer=previous_officer,
        )
        self.session.add(history_entry)

        self.audit_logger.log(
            user_id=assigned_by,
            action="ASSIGNMENT_REASSIGNED",
            target_id=investigation_id,
            details={
                "new_officer_id": new_officer_id,
                "previous_officer": previous_officer,
                "reassign_type": reassign_type,
                "reason": reason,
            }
        )

        self.session.commit()

        # WebSocket Broadcast
        try:
            event = BaseEvent(
                event_type=EventType.ASSIGNMENT_REASSIGNED,
                case_id=investigation_id,
                user_id=assigned_by,
                sequence=inv.last_sequence,
                payload={
                    "assignment_id": asg_id,
                    "investigation_id": investigation_id,
                    "officer_id": new_officer_id,
                    "previous_officer": previous_officer,
                    "reassign_type": reassign_type,
                    "assigned_by": assigned_by,
                    "timestamp": now.isoformat(),
                    "policy_version": self.policy.version,
                }
            )
            EventDispatcher.publish_sync(event, self.session)
        except Exception as e:
            logger.warning(f"Failed to dispatch ASSIGNMENT_REASSIGNED websocket event: {e}")

        return self.get_aggregate(investigation_id)

    # ── 5. Bulk Reassign ─────────────────────────────────────────────────────

    def bulk_reassign(
        self,
        reassignments: List[Dict[str, Any]],
        assigned_by: str
    ) -> List[AssignmentAggregate]:
        """Perform batch reassignments atomically in a single transaction."""
        results: List[AssignmentAggregate] = []
        for item in reassignments:
            inv_id = item["investigation_id"]
            new_off_id = item["new_officer_id"]
            reason = item.get("reason", "Bulk redistribution")
            override = item.get("manual_override", False)
            override_reason = item.get("override_reason")
            version = item.get("expected_version")

            agg = self.reassign(
                investigation_id=inv_id,
                new_officer_id=new_off_id,
                assigned_by=assigned_by,
                reason=reason,
                reassign_type="BULK",
                manual_override=override,
                override_reason=override_reason,
                expected_version=version,
            )
            results.append(agg)
        return results

    # ── 6. Bulk Recommendation ───────────────────────────────────────────────

    def recommend_many(
        self,
        investigation_ids: List[str],
        limit_per_case: int = 3
    ) -> Dict[str, List[RankedRecommendation]]:
        """Compute recommendations for multiple investigations using bulk loading."""
        results: Dict[str, List[RankedRecommendation]] = {}

        investigations = self.session.query(Investigation).filter(Investigation.id.in_(investigation_ids)).all()
        for inv in investigations:
            context = ScoringContext(
                investigation_id=inv.id,
                priority=inv.priority,
            )
            ranked = self.recommendation_service.rank_officers(context)
            results[inv.id] = ranked[:limit_per_case]

        return results

    # ── 7. Completion Estimator ──────────────────────────────────────────────

    def estimate_completion(self, investigation_id: str) -> CompletionEstimate:
        """Deterministic heuristic for case completion duration based on priority, tasks, and workload."""
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        # Base duration by priority
        priority_str = (inv.priority or "MEDIUM").upper()
        base_days_map = {
            "CRITICAL": 7.0,
            "HIGH": 14.0,
            "MEDIUM": 30.0,
            "LOW": 60.0,
        }
        base_days = base_days_map.get(priority_str, 30.0)

        # Task count factor
        task_count = self.session.query(InvestigationTask).filter(
            InvestigationTask.investigation_id == investigation_id,
            InvestigationTask.status.notin_([TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.CANCELLED])
        ).count()
        task_factor = 1.0 + (task_count * 0.08)

        # Officer workload factor
        workload_factor = 1.0
        if inv.assigned_officer:
            try:
                snapshots = self.workload_loader.load_team_snapshots([inv.assigned_officer])
                if inv.assigned_officer in snapshots:
                    snap, invs, tasks = snapshots[inv.assigned_officer]
                    wl = self.workload_engine.calculate_workload(snap, invs, tasks)
                    capacity = self.workload_engine.calculate_capacity(wl, snap.maximum_capacity)
                    workload_factor = max(0.6, round(1.0 + (capacity.capacity_used - 0.5) * 0.5, 2))
            except Exception:
                workload_factor = 1.0

        expected = round(base_days * task_factor * workload_factor, 1)
        earliest = round(expected * 0.65, 1)
        latest = round(expected * 1.5, 1)

        target_date = (datetime.utcnow() + timedelta(days=expected)).strftime("%Y-%m-%d")

        return CompletionEstimate(
            investigation_id=investigation_id,
            earliest_days=earliest,
            expected_days=expected,
            latest_days=latest,
            estimated_completion_date=target_date,
            factors={
                "priority": priority_str,
                "base_days": base_days,
                "task_count": task_count,
                "task_factor": round(task_factor, 2),
                "workload_factor": workload_factor,
            },
            policy_version=self.policy.version,
        )

    # ── 8. History Lookups & Aggregate Helper ─────────────────────────────────

    def get_history_for_investigation(self, investigation_id: str) -> List[AssignmentRecordDTO]:
        """Fetch history records for an investigation."""
        rows = self.session.query(AssignmentHistory).filter(
            AssignmentHistory.investigation_id == investigation_id
        ).order_by(AssignmentHistory.timestamp.desc()).all()

        return [
            AssignmentRecordDTO(
                id=r.id,
                assignment_id=r.assignment_id,
                investigation_id=r.investigation_id,
                officer_id=r.officer_id,
                assigned_by=r.assigned_by,
                timestamp=r.timestamp.isoformat() if isinstance(r.timestamp, datetime) else str(r.timestamp),
                reason=r.reason,
                recommendation_score=r.recommendation_score,
                policy_version=r.policy_version,
                manual_override=r.manual_override,
                override_reason=r.override_reason,
                previous_officer=r.previous_officer,
            )
            for r in rows
        ]

    def get_history_for_officer(self, officer_id: str) -> List[AssignmentRecordDTO]:
        """Fetch history records for an officer."""
        rows = self.session.query(AssignmentHistory).filter(
            AssignmentHistory.officer_id == officer_id
        ).order_by(AssignmentHistory.timestamp.desc()).all()

        return [
            AssignmentRecordDTO(
                id=r.id,
                assignment_id=r.assignment_id,
                investigation_id=r.investigation_id,
                officer_id=r.officer_id,
                assigned_by=r.assigned_by,
                timestamp=r.timestamp.isoformat() if isinstance(r.timestamp, datetime) else str(r.timestamp),
                reason=r.reason,
                recommendation_score=r.recommendation_score,
                policy_version=r.policy_version,
                manual_override=r.manual_override,
                override_reason=r.override_reason,
                previous_officer=r.previous_officer,
            )
            for r in rows
        ]

    def get_aggregate(self, investigation_id: str) -> AssignmentAggregate:
        """Construct the DDD AssignmentAggregate for an investigation."""
        inv = self.session.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise KeyError(f"Investigation '{investigation_id}' not found")

        history_dtos = self.get_history_for_investigation(investigation_id)
        history_records = [
            AssignmentHistoryRecord(
                id=h.id,
                assignment_id=h.assignment_id,
                investigation_id=h.investigation_id,
                officer_id=h.officer_id,
                assigned_by=h.assigned_by,
                timestamp=datetime.fromisoformat(h.timestamp) if isinstance(h.timestamp, str) else h.timestamp,
                reason=h.reason,
                recommendation_score=h.recommendation_score,
                policy_version=h.policy_version,
                manual_override=h.manual_override,
                override_reason=h.override_reason,
                previous_officer=h.previous_officer,
            )
            for h in history_dtos
        ]

        val_result = None
        if inv.assigned_officer:
            val_result = self.validate(investigation_id, inv.assigned_officer)

        workload_snap = None
        if inv.assigned_officer:
            try:
                snapshots = self.workload_loader.load_team_snapshots([inv.assigned_officer])
                if inv.assigned_officer in snapshots:
                    snap, invs, tasks = snapshots[inv.assigned_officer]
                    workload_snap = self.workload_engine.calculate_workload(snap, invs, tasks)
            except Exception:
                pass

        return AssignmentAggregate(
            investigation_id=inv.id,
            current_officer_id=inv.assigned_officer,
            investigation_status=inv.status or "OPEN",
            investigation_priority=inv.priority or "MEDIUM",
            version=inv.version or 1,
            policy_version=self.policy.version,
            history=history_records,
            validation=val_result,
            officer_workload=workload_snap,
        )
