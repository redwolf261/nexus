"""Workload counter reconciliation (Phase 8.2, Milestone 1).

The Officer.current_case_count / current_task_count columns are a denormalized
cache for fast capacity checks. The database (FIR + InvestigationTask rows) is
the source of truth. Drift is inevitable (crashes, missed hooks, manual edits),
so this service detects and corrects it, and records every correction to
`officer_workload_reconciliation` for observability.

Exposed operations:
  - reconcile_officer_workload(officer_id): fix one officer, return corrections
  - reconcile_all_workloads(): fix the whole fleet, return an aggregate report

The assignment engine must never assume the cache is exact — this is the safety
net that keeps it close enough, and the audit trail that proves it.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from backend.db.schema import Officer, OfficerWorkloadReconciliation
from backend.assignment.officer_repository import OfficerRepository


class ReconciliationService:
    """Detects and corrects drift between cached counters and DB truth."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = OfficerRepository(session)

    def reconcile_officer_workload(self, officer_id: str) -> Dict[str, Any]:
        """Reconcile one officer's cached counters against source-of-truth counts.

        Returns a report:
            {
              "officer_id": str,
              "corrections": [ {field, cached, actual}, ... ],
              "mismatch_count": int,
            }

        Writes an OfficerWorkloadReconciliation row per mismatched field and
        updates the cached counters. Caller commits.
        """
        officer = self.repo.get_officer(officer_id)
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        actual_cases = self.repo.count_open_cases_from_source(officer_id)
        actual_tasks = self.repo.count_active_tasks_from_source(officer_id)

        cached_cases = officer.current_case_count or 0
        cached_tasks = officer.current_task_count or 0

        corrections: List[Dict[str, Any]] = []

        if cached_cases != actual_cases:
            corrections.append({
                "field": "current_case_count",
                "cached": cached_cases,
                "actual": actual_cases,
            })
            self._record(officer_id, "current_case_count", cached_cases, actual_cases)

        if cached_tasks != actual_tasks:
            corrections.append({
                "field": "current_task_count",
                "cached": cached_tasks,
                "actual": actual_tasks,
            })
            self._record(officer_id, "current_task_count", cached_tasks, actual_tasks)

        # Apply corrections (hard-set to truth).
        if corrections:
            officer.current_case_count = actual_cases
            officer.current_task_count = actual_tasks
            self.session.flush()

        return {
            "officer_id": officer_id,
            "corrections": corrections,
            "mismatch_count": len(corrections),
        }

    def reconcile_all_workloads(self, batch_limit: Optional[int] = None) -> Dict[str, Any]:
        """Reconcile every officer. Returns an aggregate report.

        {
          "officers_checked": int,
          "officers_corrected": int,
          "total_corrections": int,
          "reconciled_at": iso8601 str,
          "details": [ per-officer reports with mismatch_count > 0 ],
        }
        """
        officers = self.repo.list_officers(limit=batch_limit)
        officers_corrected = 0
        total_corrections = 0
        details: List[Dict[str, Any]] = []

        for officer in officers:
            report = self.reconcile_officer_workload(officer.officer_id)
            if report["mismatch_count"] > 0:
                officers_corrected += 1
                total_corrections += report["mismatch_count"]
                details.append(report)

        return {
            "officers_checked": len(officers),
            "officers_corrected": officers_corrected,
            "total_corrections": total_corrections,
            "reconciled_at": datetime.utcnow().isoformat(),
            "details": details,
        }

    def get_reconciliation_history(
        self, officer_id: Optional[str] = None, limit: int = 100
    ) -> List[OfficerWorkloadReconciliation]:
        """Recent reconciliation corrections (optionally filtered by officer)."""
        q = self.session.query(OfficerWorkloadReconciliation)
        if officer_id:
            q = q.filter_by(officer_id=officer_id)
        return q.order_by(
            OfficerWorkloadReconciliation.reconciled_at.desc()
        ).limit(limit).all()

    # ── internals ─────────────────────────────────────────────────────────────
    def _record(
        self, officer_id: str, field: str, cached_value: int, actual_value: int
    ) -> None:
        row = OfficerWorkloadReconciliation(
            officer_id=officer_id,
            field=field,
            cached_value=cached_value,
            actual_value=actual_value,
            correction_applied=True,
            reconciled_at=datetime.utcnow(),
        )
        self.session.add(row)
