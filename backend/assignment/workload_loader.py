"""ORM-coupled data loader for the WorkloadEngine (Phase 8.2, Milestone 3).

WorkloadDataLoader is the thin adapter between the database and the pure
WorkloadEngine. Its only responsibility is to translate ORM rows into the
lightweight snapshot types that WorkloadEngine accepts.

Design contract:
    - All DB queries happen HERE, never inside WorkloadEngine.
    - Bulk-query paths are provided for team-wide operations to avoid
      O(n × queries) patterns at scale (1,000 officers).
    - No business logic lives here — only data shaping.
    - The session is passed in; this service does not own it.

Performance notes:
    load_team_snapshots() executes exactly 3 queries regardless of team size:
      1. Bulk officer rows
      2. Bulk investigations (filtered to those officers)
      3. Bulk tasks (filtered to those officers)
    This is the path to meet the < 300 ms workload / < 500 ms team-metrics targets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.schema import (
    Officer,
    Investigation,
    InvestigationTask,
    OfficerSkill,
    TaskStatus,
)
from backend.assignment.workload_engine import (
    OfficerSnapshot,
    InvestigationSnapshot,
    TaskSnapshot,
)


# ── Status sets ───────────────────────────────────────────────────────────────
# Investigations in these statuses ARE assigned to an officer and should be
# included in the query. We fetch all and let WorkloadPolicy filter weights.
# This ensures we don't miss newly-added statuses at the DB level.
_ALL_NON_DELETED_STATUSES: Tuple[str, ...] = (
    "Open",
    "Under Investigation",
    "Completed",
    "Closed",
    "Archived",
    "Cancelled",
    # Upper-case variants
    "OPEN",
    "UNDER_INVESTIGATION",
    "COMPLETED",
    "CLOSED",
    "ARCHIVED",
    "CANCELLED",
)


class WorkloadDataLoader:
    """Assembles WorkloadEngine input snapshots from the database.

    Usage::

        loader = WorkloadDataLoader(session)
        engine = WorkloadEngine(policy=DEFAULT_POLICY)

        snap = loader.load_officer_snapshot("OFF-001")
        invs = loader.load_investigations_for_officer("OFF-001")
        tasks = loader.load_tasks_for_officer("OFF-001")

        workload = engine.calculate_workload(snap, invs, tasks)

    For team-wide operations, use load_team_snapshots() to avoid N×3 queries.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── Single-officer loads ──────────────────────────────────────────────────

    def load_officer_snapshot(self, officer_id: str) -> OfficerSnapshot:
        """Load an OfficerSnapshot from the officers + officer_skills tables.

        Raises:
            ValueError: If the officer does not exist.
        """
        officer = (
            self.session.query(Officer)
            .filter_by(officer_id=officer_id)
            .first()
        )
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        skills = self._load_skills_for_officer(officer_id)

        return OfficerSnapshot(
            officer_id=officer.officer_id,
            district_id=officer.district_id,
            maximum_capacity=officer.maximum_capacity or 0,
            skills=frozenset(skills),
        )

    def load_investigations_for_officer(
        self, officer_id: str
    ) -> List[InvestigationSnapshot]:
        """Load all investigations assigned to this officer."""
        rows = (
            self.session.query(Investigation)
            .filter(Investigation.assigned_officer == officer_id)
            .all()
        )
        return [_inv_to_snapshot(row) for row in rows]

    def load_tasks_for_officer(self, officer_id: str) -> List[TaskSnapshot]:
        """Load all tasks assigned to this officer."""
        rows = (
            self.session.query(InvestigationTask)
            .filter(InvestigationTask.assigned_officer_id == officer_id)
            .all()
        )
        return [_task_to_snapshot(row) for row in rows]

    # ── Bulk team loads (performance path) ────────────────────────────────────

    def load_team_snapshots(
        self, officer_ids: List[str]
    ) -> Dict[str, Tuple[OfficerSnapshot, List[InvestigationSnapshot], List[TaskSnapshot]]]:
        """Bulk-load all data for a team of officers in 3 queries.

        Returns a dict keyed by officer_id. Officers not found in the DB are
        silently omitted (no partial failures).

        Performance: 3 queries total regardless of team size.
        """
        if not officer_ids:
            return {}

        # Query 1: Officers + skills (two sub-queries, still O(1) round-trips)
        officer_rows = (
            self.session.query(Officer)
            .filter(Officer.officer_id.in_(officer_ids))
            .all()
        )
        found_ids = [o.officer_id for o in officer_rows]

        # Query 2: Skills for all found officers (one join query)
        skill_rows = (
            self.session.query(OfficerSkill)
            .filter(OfficerSkill.officer_id.in_(found_ids))
            .all()
        )
        skills_by_officer: Dict[str, Set[str]] = {oid: set() for oid in found_ids}
        for sk in skill_rows:
            if sk.skill_code is not None:
                val = sk.skill_code.value if hasattr(sk.skill_code, "value") else str(sk.skill_code)
                skills_by_officer.setdefault(sk.officer_id, set()).add(val)

        # Query 3: Investigations for all found officers
        inv_rows = (
            self.session.query(Investigation)
            .filter(Investigation.assigned_officer.in_(found_ids))
            .all()
        )
        invs_by_officer: Dict[str, List[InvestigationSnapshot]] = {
            oid: [] for oid in found_ids
        }
        for inv in inv_rows:
            if inv.assigned_officer in invs_by_officer:
                invs_by_officer[inv.assigned_officer].append(_inv_to_snapshot(inv))

        # Query 4: Tasks for all found officers
        task_rows = (
            self.session.query(InvestigationTask)
            .filter(InvestigationTask.assigned_officer_id.in_(found_ids))
            .all()
        )
        tasks_by_officer: Dict[str, List[TaskSnapshot]] = {
            oid: [] for oid in found_ids
        }
        for task in task_rows:
            if task.assigned_officer_id in tasks_by_officer:
                tasks_by_officer[task.assigned_officer_id].append(
                    _task_to_snapshot(task)
                )

        # Assemble result
        result: Dict[str, Tuple[OfficerSnapshot, List[InvestigationSnapshot], List[TaskSnapshot]]] = {}
        for officer in officer_rows:
            oid = officer.officer_id
            snap = OfficerSnapshot(
                officer_id=oid,
                district_id=officer.district_id,
                maximum_capacity=officer.maximum_capacity or 0,
                skills=frozenset(skills_by_officer.get(oid, set())),
            )
            result[oid] = (
                snap,
                invs_by_officer.get(oid, []),
                tasks_by_officer.get(oid, []),
            )

        return result

    def load_overdue_counts(
        self,
        officer_id: str,
        as_of: Optional[datetime] = None,
    ) -> Tuple[int, int]:
        """Return (overdue_task_count, overdue_investigation_count) for one officer.

        A task is overdue if:  due_at < as_of AND status is non-terminal.
        An investigation is overdue if: due_date < as_of AND status is active.

        Args:
            officer_id: The officer to check.
            as_of:      Reference datetime (defaults to UTC now).

        Returns:
            Tuple (overdue_tasks, overdue_investigations).
        """
        as_of = as_of or datetime.now(timezone.utc).replace(tzinfo=None)

        # Non-terminal task statuses
        active_task_statuses = [
            TaskStatus.CREATED, TaskStatus.ASSIGNED,
            TaskStatus.ACTIVE, TaskStatus.BLOCKED,
        ]

        overdue_tasks = (
            self.session.query(func.count(InvestigationTask.id))
            .filter(
                InvestigationTask.assigned_officer_id == officer_id,
                InvestigationTask.status.in_(active_task_statuses),
                InvestigationTask.due_at.isnot(None),
                InvestigationTask.due_at < as_of,
            )
            .scalar()
        ) or 0

        # Investigations don't have a dedicated due_date in the current schema,
        # so we return 0 as the placeholder. M4/M5 can add a due_date column
        # and wire it here without changing the engine contract.
        overdue_investigations = 0

        return overdue_tasks, overdue_investigations

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_skills_for_officer(self, officer_id: str) -> Set[str]:
        rows = (
            self.session.query(OfficerSkill)
            .filter_by(officer_id=officer_id)
            .all()
        )
        result: Set[str] = set()
        for sk in rows:
            if sk.skill_code is not None:
                val = sk.skill_code.value if hasattr(sk.skill_code, "value") else str(sk.skill_code)
                result.add(val)
        return result


# ── Row → Snapshot converters (module-private) ─────────────────────────────────

def _inv_to_snapshot(inv: Investigation) -> InvestigationSnapshot:
    """Convert an ORM Investigation row to an InvestigationSnapshot."""
    return InvestigationSnapshot(
        investigation_id=inv.id,
        priority=inv.priority or "LOW",
        status=inv.status or "Open",
        assigned_officer_id=inv.assigned_officer,
        due_date=None,  # due_date not in current schema; placeholder for M4+
    )


def _task_to_snapshot(task: InvestigationTask) -> TaskSnapshot:
    """Convert an ORM InvestigationTask row to a TaskSnapshot."""
    status_val = task.status
    if hasattr(status_val, "value"):
        status_val = status_val.value
    return TaskSnapshot(
        task_id=task.id,
        investigation_id=task.investigation_id,
        status=str(status_val) if status_val else "CREATED",
        due_at=task.due_at,
    )
