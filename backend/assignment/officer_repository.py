"""Repository layer for officer capability and workload data (Phase 8.2, M1).

Data access only — no business rules. The capacity/availability *policy* lives
in OfficerCapacityService and AvailabilityStateManager. This layer:
  - reads/writes officer capability fields, skills, certifications, specializations
  - maintains denormalized workload counters atomically (with optimistic lock)
  - provides the DB-derived "truth" counts used by ReconciliationService

Counter philosophy: `current_case_count` / `current_task_count` on the Officer
row are a *cache*. The authoritative values are computed from FIR /
InvestigationTask rows via count_*_from_source(). The assignment engine must
never assume the cache is exact — it reconciles.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import uuid4
from datetime import datetime, date

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.schema import (
    Officer, OfficerSkill, OfficerSpecialization, OfficerCertification,
    SkillCode, Specialization, CertificationStatus,
    FIR, InvestigationTask, TaskStatus,
)


# Case statuses that count as "open" for workload purposes.
OPEN_CASE_STATUSES = ("Under Investigation", "Open")

# Task statuses that count as active workload (not terminal).
ACTIVE_TASK_STATUSES = (
    TaskStatus.CREATED, TaskStatus.ASSIGNED, TaskStatus.ACTIVE, TaskStatus.BLOCKED,
)


class OfficerRepository:
    """Data access for officer capability + workload."""

    def __init__(self, session: Session):
        self.session = session

    # ── Basic reads ──────────────────────────────────────────────────────────
    def get_officer(self, officer_id: str) -> Optional[Officer]:
        return self.session.query(Officer).filter_by(officer_id=officer_id).first()

    def list_officers(self, limit: Optional[int] = None) -> List[Officer]:
        q = self.session.query(Officer).order_by(Officer.officer_id)
        if limit:
            q = q.limit(limit)
        return q.all()

    # ── Capability: skills ───────────────────────────────────────────────────
    def add_skill(self, officer_id: str, skill: SkillCode, proficiency: int = 3) -> OfficerSkill:
        """Add or update a skill for an officer (idempotent on (officer, skill))."""
        existing = self.session.query(OfficerSkill).filter_by(
            officer_id=officer_id, skill_code=skill
        ).first()
        if existing:
            existing.proficiency = proficiency
            self.session.flush()
            return existing
        row = OfficerSkill(
            officer_id=officer_id,
            skill_code=skill,
            proficiency=proficiency,
            created_at=datetime.utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get_skills(self, officer_id: str) -> List[OfficerSkill]:
        return self.session.query(OfficerSkill).filter_by(officer_id=officer_id).all()

    def list_officers_by_skill(self, skill: SkillCode) -> List[Officer]:
        """All officers holding a given skill."""
        return (
            self.session.query(Officer)
            .join(OfficerSkill, OfficerSkill.officer_id == Officer.officer_id)
            .filter(OfficerSkill.skill_code == skill)
            .all()
        )

    # ── Capability: specializations ──────────────────────────────────────────
    def add_specialization(
        self, officer_id: str, spec: Specialization, is_primary: bool = False
    ) -> OfficerSpecialization:
        existing = self.session.query(OfficerSpecialization).filter_by(
            officer_id=officer_id, specialization=spec
        ).first()
        if existing:
            existing.is_primary = is_primary
            self.session.flush()
            return existing
        row = OfficerSpecialization(
            officer_id=officer_id,
            specialization=spec,
            is_primary=is_primary,
            created_at=datetime.utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get_specializations(self, officer_id: str) -> List[OfficerSpecialization]:
        return self.session.query(OfficerSpecialization).filter_by(
            officer_id=officer_id
        ).all()

    def list_officers_by_specialization(self, spec: Specialization) -> List[Officer]:
        return (
            self.session.query(Officer)
            .join(OfficerSpecialization,
                  OfficerSpecialization.officer_id == Officer.officer_id)
            .filter(OfficerSpecialization.specialization == spec)
            .all()
        )

    # ── Capability: certifications ───────────────────────────────────────────
    def add_certification(
        self,
        officer_id: str,
        name: str,
        skill_code: Optional[SkillCode] = None,
        certificate_number: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        issued_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        status: CertificationStatus = CertificationStatus.ACTIVE,
    ) -> OfficerCertification:
        row = OfficerCertification(
            id=str(uuid4()),
            officer_id=officer_id,
            name=name,
            skill_code=skill_code,
            certificate_number=certificate_number,
            issuing_authority=issuing_authority,
            issued_date=issued_date,
            expiry_date=expiry_date,
            status=status,
            created_at=datetime.utcnow(),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get_certifications(self, officer_id: str) -> List[OfficerCertification]:
        return self.session.query(OfficerCertification).filter_by(
            officer_id=officer_id
        ).all()

    def get_valid_certifications(
        self, officer_id: str, as_of: Optional[date] = None
    ) -> List[OfficerCertification]:
        """Return certifications that are ACTIVE and not past expiry.

        A cert is valid if status==ACTIVE and (expiry_date is None or >= as_of).
        This is the query the scoring/capacity layers use to decide mandatory-cert
        rejection vs preferred-cert penalty.
        """
        as_of = as_of or date.today()
        certs = self.session.query(OfficerCertification).filter_by(
            officer_id=officer_id, status=CertificationStatus.ACTIVE
        ).all()
        return [
            c for c in certs
            if c.expiry_date is None or c.expiry_date >= as_of
        ]

    def mark_expired_certifications(self, as_of: Optional[date] = None) -> int:
        """Flip ACTIVE certs whose expiry has passed to EXPIRED. Returns count.

        Idempotent maintenance job. Returns number of certs transitioned.
        """
        as_of = as_of or date.today()
        expired = self.session.query(OfficerCertification).filter(
            OfficerCertification.status == CertificationStatus.ACTIVE,
            OfficerCertification.expiry_date.isnot(None),
            OfficerCertification.expiry_date < as_of,
        ).all()
        for c in expired:
            c.status = CertificationStatus.EXPIRED
        self.session.flush()
        return len(expired)

    # ── Workload counters (denormalized cache) ───────────────────────────────
    def update_workload_counters(
        self, officer_id: str, case_delta: int = 0, task_delta: int = 0
    ) -> Officer:
        """Atomically adjust cached counters (never below zero).

        Called by assignment/task hooks. Uses the capability_version optimistic
        lock only implicitly (counters are commutative deltas, so we don't reject
        on version here — reconciliation is the safety net).
        """
        officer = self.get_officer(officer_id)
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")

        current_cases = officer.current_case_count or 0
        current_tasks = officer.current_task_count or 0
        officer.current_case_count = max(0, current_cases + case_delta)
        officer.current_task_count = max(0, current_tasks + task_delta)
        self.session.flush()
        return officer

    def set_workload_counters(
        self, officer_id: str, case_count: int, task_count: int
    ) -> Officer:
        """Hard-set counters (used by reconciliation to correct drift)."""
        officer = self.get_officer(officer_id)
        if not officer:
            raise ValueError(f"Officer {officer_id} not found")
        officer.current_case_count = max(0, case_count)
        officer.current_task_count = max(0, task_count)
        self.session.flush()
        return officer

    # ── Workload counters (DB-derived truth) ─────────────────────────────────
    def count_open_cases_from_source(self, officer_id: str) -> int:
        """Authoritative open-case count from FIR rows.

        Counts FIRs where this officer is the investigating officer and the case
        is in an open status.
        """
        return (
            self.session.query(func.count(FIR.fir_id))
            .filter(
                FIR.investigating_officer_id == officer_id,
                FIR.status.in_(OPEN_CASE_STATUSES),
            )
            .scalar()
        ) or 0

    def count_active_tasks_from_source(self, officer_id: str) -> int:
        """Authoritative active-task count from InvestigationTask rows."""
        return (
            self.session.query(func.count(InvestigationTask.id))
            .filter(
                InvestigationTask.assigned_officer_id == officer_id,
                InvestigationTask.status.in_(ACTIVE_TASK_STATUSES),
            )
            .scalar()
        ) or 0

    # ── Availability filters ─────────────────────────────────────────────────
    def list_available_officers(self) -> List[Officer]:
        """Officers whose availability permits new work.

        ON_DUTY and FIELD are eligible (FIELD may be restricted to critical
        cases by policy in the capacity service). BREAK/OFF_DUTY/LEAVE/TRAINING/
        SUSPENDED are excluded here.
        """
        return self.session.query(Officer).filter(
            Officer.availability_status.in_(("ON_DUTY", "FIELD"))
        ).all()
