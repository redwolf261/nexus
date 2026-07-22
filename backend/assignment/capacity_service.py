"""Officer capacity policy service (Phase 8.2, Milestone 1).

Answers the hard capacity questions the assignment engine (M2+) relies on:
  - can_assign_case(officer, priority): is this officer eligible for a new case?
  - get_capacity_details(officer): full explainable snapshot
  - get_workload_summary(officer): counts + utilization + burnout risk
  - list_capacity_violations(): officers currently over their maximum

Every rejection is explainable (RejectionReason with a machine code + message),
satisfying Deliverable 7 ("Return explainable rejection"). This service reads
policy; it does not mutate officers.

Capacity rules (Deliverable 7):
    reject when:
      - capacity exceeded (current_case_count >= maximum_capacity)
      - availability is non-assignable (OFF_DUTY / BREAK / LEAVE / TRAINING / SUSPENDED)
      - FIELD status and requested priority is not CRITICAL (policy)
      - required skill missing            (when required_skill given)
      - required certification missing/expired (when required_cert_skill given)
"""

from __future__ import annotations

from typing import List, Optional
from datetime import date

from sqlalchemy.orm import Session

from backend.db.schema import (
    Officer, SkillCode, TaskPriority, BurnoutRisk, AvailabilityStatus,
)
from backend.assignment.officer_repository import OfficerRepository
from backend.assignment.availability import (
    NON_ASSIGNABLE_STATUSES, CRITICAL_ONLY_STATUSES,
)
from backend.assignment.contracts import (
    CapacityDetails, CapacityViolation, RejectionReason, WorkloadSummary,
)


# Burnout thresholds on utilization (current_case_count / maximum_capacity).
_BURNOUT_THRESHOLDS = (
    (1.0, BurnoutRisk.CRITICAL),   # at/over capacity
    (0.85, BurnoutRisk.HIGH),
    (0.6, BurnoutRisk.MEDIUM),
    (0.0, BurnoutRisk.LOW),
)


class OfficerCapacityService:
    """Read-only capacity + workload policy over officer data."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = OfficerRepository(session)

    # ── Utilization / burnout ────────────────────────────────────────────────
    @staticmethod
    def _utilization(case_count: int, max_capacity: int) -> float:
        if not max_capacity or max_capacity <= 0:
            # No declared capacity: treat any load as fully utilized, none as free.
            return 1.0 if case_count > 0 else 0.0
        return case_count / max_capacity

    @staticmethod
    def _burnout_risk(utilization: float) -> BurnoutRisk:
        for threshold, risk in _BURNOUT_THRESHOLDS:
            if utilization >= threshold:
                return risk
        return BurnoutRisk.LOW

    def get_workload_summary(self, officer_id: str) -> WorkloadSummary:
        """Workload snapshot using cached counters (fast path)."""
        officer = self.repo.get_officer(officer_id)
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        cases = officer.current_case_count or 0
        tasks = officer.current_task_count or 0
        max_cap = officer.maximum_capacity or 0
        util = self._utilization(cases, max_cap)
        return WorkloadSummary(
            officer_id=officer_id,
            current_case_count=cases,
            current_task_count=tasks,
            maximum_capacity=max_cap,
            utilization=util,
            burnout_risk=self._burnout_risk(util).value,
        )

    # ── Capacity checks ──────────────────────────────────────────────────────
    def get_capacity_details(
        self,
        officer_id: str,
        priority: Optional[TaskPriority] = None,
        required_skill: Optional[SkillCode] = None,
        required_cert_skill: Optional[SkillCode] = None,
        as_of: Optional[date] = None,
    ) -> CapacityDetails:
        """Compute an explainable capacity snapshot for one officer.

        `assignable` is True only when there are zero rejections.
        """
        officer = self.repo.get_officer(officer_id)
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        cases = officer.current_case_count or 0
        max_cap = officer.maximum_capacity or 0
        status = officer.availability_status or AvailabilityStatus.ON_DUTY.value
        available_slots = max(0, max_cap - cases)
        util = self._utilization(cases, max_cap)

        rejections: List[RejectionReason] = []

        # 1. Availability
        if status in NON_ASSIGNABLE_STATUSES:
            rejections.append(RejectionReason(
                code="UNAVAILABLE",
                message=f"Officer is {status} and cannot receive new assignments",
            ))
        elif status in CRITICAL_ONLY_STATUSES:
            # FIELD officers only take CRITICAL cases (policy).
            if priority is not None and priority != TaskPriority.CRITICAL:
                rejections.append(RejectionReason(
                    code="FIELD_CRITICAL_ONLY",
                    message=(
                        f"Officer is on FIELD duty and may only take CRITICAL "
                        f"assignments (requested: {priority.value})"
                    ),
                ))

        # 2. Capacity
        if max_cap > 0 and cases >= max_cap:
            rejections.append(RejectionReason(
                code="CAPACITY_EXCEEDED",
                message=f"Officer at capacity ({cases}/{max_cap} cases)",
            ))

        # 3. Required skill
        if required_skill is not None:
            held = {sk.skill_code for sk in self.repo.get_skills(officer_id)}
            if required_skill not in held:
                rejections.append(RejectionReason(
                    code="MISSING_SKILL",
                    message=f"Officer lacks required skill {required_skill.value}",
                ))

        # 4. Required certification (mandatory → reject if missing/expired)
        if required_cert_skill is not None:
            valid_certs = self.repo.get_valid_certifications(officer_id, as_of=as_of)
            has_valid = any(c.skill_code == required_cert_skill for c in valid_certs)
            if not has_valid:
                rejections.append(RejectionReason(
                    code="MISSING_CERTIFICATION",
                    message=(
                        f"Officer lacks a valid (unexpired) certification for "
                        f"{required_cert_skill.value}"
                    ),
                ))

        return CapacityDetails(
            officer_id=officer_id,
            availability_status=status,
            current_case_count=cases,
            maximum_capacity=max_cap,
            available_slots=available_slots,
            utilization=util,
            assignable=len(rejections) == 0,
            rejections=rejections,
        )

    def can_assign_case(
        self,
        officer_id: str,
        priority: Optional[TaskPriority] = None,
        required_skill: Optional[SkillCode] = None,
        required_cert_skill: Optional[SkillCode] = None,
        as_of: Optional[date] = None,
    ) -> bool:
        """Boolean convenience wrapper over get_capacity_details()."""
        return self.get_capacity_details(
            officer_id, priority=priority, required_skill=required_skill,
            required_cert_skill=required_cert_skill, as_of=as_of,
        ).assignable

    # ── Fleet-wide ───────────────────────────────────────────────────────────
    def list_capacity_violations(self) -> List[CapacityViolation]:
        """All officers whose case load exceeds their maximum capacity.

        Uses a single query rather than per-officer iteration so it scales to a
        large fleet (Deliverable acceptance: 1,000 officers).
        """
        officers = self.session.query(Officer).filter(
            Officer.maximum_capacity.isnot(None),
            Officer.maximum_capacity > 0,
            Officer.current_case_count > Officer.maximum_capacity,
        ).all()
        return [
            CapacityViolation(
                officer_id=o.officer_id,
                current_case_count=o.current_case_count or 0,
                maximum_capacity=o.maximum_capacity or 0,
                over_by=(o.current_case_count or 0) - (o.maximum_capacity or 0),
            )
            for o in officers
        ]
