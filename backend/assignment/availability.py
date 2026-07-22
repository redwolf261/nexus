"""Officer availability state machine (Phase 8.2, Milestone 1).

Enforces the strict transition graph from the Phase 8.2 spec and audits every
change to `officer_availability_logs`. Availability governs whether new work may
be assigned; the capacity service reads the *current* status, this manager owns
*changing* it.

Transition graph (ON_DUTY is the hub):

    ON_DUTY  <-> BREAK
    ON_DUTY  <-> FIELD
    ON_DUTY  <-> LEAVE
    ON_DUTY  <-> TRAINING
    ON_DUTY  <-> OFF_DUTY
    ON_DUTY   -> SUSPENDED
    SUSPENDED -> ON_DUTY        (admin/supervisor only)

Rules enforced here:
  - SUSPENDED cannot self-transition; only an admin/supervisor actor may lift it.
  - A transition not present in the graph is rejected with an explainable error.
  - LEAVE -> ON_DUTY may happen manually or via auto_expire_leave() on/after the
    scheduled leave_ends_on date.
  - Every accepted transition writes an OfficerAvailabilityLog row (who/when/why).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, date

from sqlalchemy.orm import Session

from backend.db.schema import (
    Officer, OfficerAvailabilityLog, AvailabilityStatus, Role, User,
)


# Allowed transitions: from_status -> set of reachable to_statuses.
_TRANSITIONS: Dict[str, Set[str]] = {
    AvailabilityStatus.ON_DUTY.value: {
        AvailabilityStatus.BREAK.value,
        AvailabilityStatus.FIELD.value,
        AvailabilityStatus.LEAVE.value,
        AvailabilityStatus.TRAINING.value,
        AvailabilityStatus.OFF_DUTY.value,
        AvailabilityStatus.SUSPENDED.value,
    },
    AvailabilityStatus.BREAK.value: {AvailabilityStatus.ON_DUTY.value},
    AvailabilityStatus.FIELD.value: {AvailabilityStatus.ON_DUTY.value},
    AvailabilityStatus.LEAVE.value: {AvailabilityStatus.ON_DUTY.value},
    AvailabilityStatus.TRAINING.value: {AvailabilityStatus.ON_DUTY.value},
    AvailabilityStatus.OFF_DUTY.value: {AvailabilityStatus.ON_DUTY.value},
    # SUSPENDED can only return to ON_DUTY, and only via admin/supervisor.
    AvailabilityStatus.SUSPENDED.value: {AvailabilityStatus.ON_DUTY.value},
}

# Transitions that require an elevated actor (admin or supervisor).
_PRIVILEGED_TRANSITIONS: Set[Tuple[str, str]] = {
    (AvailabilityStatus.SUSPENDED.value, AvailabilityStatus.ON_DUTY.value),
}

# Statuses that accept NO new assignments at all.
NON_ASSIGNABLE_STATUSES: Set[str] = {
    AvailabilityStatus.OFF_DUTY.value,
    AvailabilityStatus.BREAK.value,
    AvailabilityStatus.LEAVE.value,
    AvailabilityStatus.TRAINING.value,
    AvailabilityStatus.SUSPENDED.value,
}

# Statuses that accept only CRITICAL-priority assignments (policy).
CRITICAL_ONLY_STATUSES: Set[str] = {
    AvailabilityStatus.FIELD.value,
}


class AvailabilityTransitionError(ValueError):
    """Raised when a requested availability transition is not permitted."""


class AvailabilityStateManager:
    """Owns officer availability transitions and their audit trail."""

    def __init__(self, session: Session):
        self.session = session

    # ── Introspection ────────────────────────────────────────────────────────
    @staticmethod
    def get_state_machine_rules() -> Dict[str, List[str]]:
        """Return the transition graph as plain data (for docs/UI)."""
        return {frm: sorted(tos) for frm, tos in _TRANSITIONS.items()}

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        """Pure check: is `current -> target` in the graph? (ignores privilege)."""
        return target in _TRANSITIONS.get(current, set())

    @staticmethod
    def requires_privilege(current: str, target: str) -> bool:
        return (current, target) in _PRIVILEGED_TRANSITIONS

    # ── Transition ───────────────────────────────────────────────────────────
    def transition(
        self,
        officer_id: str,
        target_status: str,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[Role] = None,
    ) -> Officer:
        """Transition an officer to `target_status`, auditing the change.

        Args:
            officer_id: Officer to transition.
            target_status: Desired AvailabilityStatus value.
            reason: Free-text justification (recorded in audit).
            actor_id: User performing the change (recorded in audit).
            actor_role: Role of the actor — required for privileged transitions
                        (e.g., lifting SUSPENDED needs Admin or Supervisor).

        Returns:
            The updated Officer.

        Raises:
            ValueError: officer not found, or invalid target value.
            AvailabilityTransitionError: transition not allowed by the graph or
                actor lacks privilege for a privileged transition.
        """
        # Validate target is a real status value
        valid_values = {s.value for s in AvailabilityStatus}
        if target_status not in valid_values:
            raise ValueError(f"Unknown availability status: {target_status}")

        officer = self.session.query(Officer).filter_by(officer_id=officer_id).first()
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        current = officer.availability_status or AvailabilityStatus.ON_DUTY.value

        # No-op transition to the same state is rejected (nothing to audit).
        if current == target_status:
            raise AvailabilityTransitionError(
                f"Officer already in {current}; no transition needed"
            )

        if not self.can_transition(current, target_status):
            raise AvailabilityTransitionError(
                f"Illegal transition {current} -> {target_status}. "
                f"Allowed from {current}: {sorted(_TRANSITIONS.get(current, set()))}"
            )

        # Privilege check (e.g., SUSPENDED -> ON_DUTY needs admin/supervisor).
        if self.requires_privilege(current, target_status):
            if actor_role not in (Role.Admin, Role.Supervisor):
                raise AvailabilityTransitionError(
                    f"Transition {current} -> {target_status} requires "
                    f"Admin or Supervisor; actor role was {actor_role}"
                )

        # Apply + audit atomically (caller commits).
        officer.availability_status = target_status
        # Clear scheduled leave end when leaving LEAVE.
        if current == AvailabilityStatus.LEAVE.value:
            officer.leave_ends_on = None

        log = OfficerAvailabilityLog(
            officer_id=officer_id,
            from_status=current,
            to_status=target_status,
            reason=reason,
            actor_id=actor_id,
            created_at=datetime.utcnow(),
        )
        self.session.add(log)
        self.session.flush()
        return officer

    def schedule_leave(
        self,
        officer_id: str,
        ends_on: date,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> Officer:
        """Put an officer on LEAVE with a scheduled return date."""
        officer = self.transition(
            officer_id,
            AvailabilityStatus.LEAVE.value,
            reason=reason,
            actor_id=actor_id,
        )
        officer.leave_ends_on = ends_on
        self.session.flush()
        return officer

    def auto_expire_leave(self, as_of: Optional[date] = None) -> List[str]:
        """Return officers from LEAVE to ON_DUTY when their leave has ended.

        Called by a scheduled job. Returns the list of officer_ids transitioned.
        Each auto-return is audited with actor_id='SYSTEM'.
        """
        as_of = as_of or date.today()
        due = self.session.query(Officer).filter(
            Officer.availability_status == AvailabilityStatus.LEAVE.value,
            Officer.leave_ends_on.isnot(None),
            Officer.leave_ends_on <= as_of,
        ).all()

        transitioned: List[str] = []
        for officer in due:
            self.transition(
                officer.officer_id,
                AvailabilityStatus.ON_DUTY.value,
                reason=f"Scheduled leave ended ({officer.leave_ends_on})",
                actor_id="SYSTEM",
            )
            transitioned.append(officer.officer_id)
        return transitioned

    def get_history(self, officer_id: str) -> List[OfficerAvailabilityLog]:
        """Full availability transition history for an officer (chronological)."""
        return self.session.query(OfficerAvailabilityLog).filter_by(
            officer_id=officer_id
        ).order_by(OfficerAvailabilityLog.created_at).all()
