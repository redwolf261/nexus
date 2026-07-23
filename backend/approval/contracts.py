"""Approval Domain Contracts and Aggregate Models (Phase 8.4).

Defines immutable data contracts, enums, stages, decisions, history, and the ApprovalAggregate
domain entity for the NEXUS Approval & Governance System.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalType(str, Enum):
    SEARCH_WARRANT = "SEARCH_WARRANT"
    ARREST_WARRANT = "ARREST_WARRANT"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    SURVEILLANCE_REQUEST = "SURVEILLANCE_REQUEST"
    INVESTIGATION_CLOSURE = "INVESTIGATION_CLOSURE"
    COLD_CASE_ARCHIVAL = "COLD_CASE_ARCHIVAL"
    CASE_REOPENING = "CASE_REOPENING"
    CROSS_DISTRICT_INVESTIGATION = "CROSS_DISTRICT_INVESTIGATION"
    BUDGET_RESOURCE_REQUEST = "BUDGET_RESOURCE_REQUEST"
    EMERGENCY_OPERATIONAL_APPROVAL = "EMERGENCY_OPERATIONAL_APPROVAL"


class ApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    ESCALATED = "ESCALATED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalStageStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"
    ESCALATED = "ESCALATED"


class ApprovalDecisionType(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_FOR_REVISION = "RETURN_FOR_REVISION"
    ESCALATE = "ESCALATE"


class OptimisticLockError(Exception):
    """Raised when an approval aggregate modification encounters a version conflict."""
    pass


class InvalidApprovalStateError(Exception):
    """Raised when an invalid state transition is requested."""
    pass


class ApprovalPolicyViolationError(Exception):
    """Raised when an approval action violates governance policy."""
    pass


@dataclass
class ApprovalStage:
    stage_id: str
    stage_order: int
    stage_name: str
    required_role: str
    min_approvers: int = 1
    approvers: List[str] = field(default_factory=list)
    status: ApprovalStageStatus = ApprovalStageStatus.PENDING
    approved_by: List[str] = field(default_factory=list)
    rejected_by: Optional[str] = None
    comments: Optional[str] = None
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_order": self.stage_order,
            "stage_name": self.stage_name,
            "required_role": str(self.required_role),
            "min_approvers": self.min_approvers,
            "approvers": list(self.approvers),
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "approved_by": list(self.approved_by),
            "rejected_by": self.rejected_by,
            "comments": self.comments,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApprovalStage:
        return cls(
            stage_id=data["stage_id"],
            stage_order=data["stage_order"],
            stage_name=data["stage_name"],
            required_role=data["required_role"],
            min_approvers=data.get("min_approvers", 1),
            approvers=data.get("approvers", []),
            status=ApprovalStageStatus(data.get("status", ApprovalStageStatus.PENDING.value)),
            approved_by=data.get("approved_by", []),
            rejected_by=data.get("rejected_by"),
            comments=data.get("comments"),
            created_at=data.get("created_at", _utc_now_iso()),
            updated_at=data.get("updated_at", _utc_now_iso()),
            completed_at=data.get("completed_at"),
        )


@dataclass(frozen=True)
class ApprovalDecision:
    decision_id: str
    approval_id: str
    stage_id: str
    approver_id: str
    approver_role: str
    action: str
    comments: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "approval_id": self.approval_id,
            "stage_id": self.stage_id,
            "approver_id": self.approver_id,
            "approver_role": str(self.approver_role),
            "action": self.action,
            "comments": self.comments,
            "conditions": dict(self.conditions),
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApprovalDecision:
        return cls(
            decision_id=data["decision_id"],
            approval_id=data["approval_id"],
            stage_id=data["stage_id"],
            approver_id=data["approver_id"],
            approver_role=data["approver_role"],
            action=data["action"],
            comments=data.get("comments", ""),
            conditions=data.get("conditions", {}),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", _utc_now_iso()),
        )


@dataclass(frozen=True)
class ApprovalHistory:
    history_id: str
    approval_id: str
    action: str
    previous_state: str
    new_state: str
    actor_id: str
    actor_role: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "approval_id": self.approval_id,
            "action": self.action,
            "previous_state": str(self.previous_state),
            "new_state": str(self.new_state),
            "actor_id": self.actor_id,
            "actor_role": str(self.actor_role),
            "details": dict(self.details),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApprovalHistory:
        return cls(
            history_id=data["history_id"],
            approval_id=data["approval_id"],
            action=data["action"],
            previous_state=data["previous_state"],
            new_state=data["new_state"],
            actor_id=data["actor_id"],
            actor_role=data["actor_role"],
            details=data.get("details", {}),
            timestamp=data.get("timestamp", _utc_now_iso()),
        )


class ApprovalAggregate:
    """Domain Aggregate Root for Approval Requests.
    
    Handles state machine transitions, optimistic locking via `version`,
    stage advancement, and immutable audit logs.
    """

    def __init__(
        self,
        approval_id: str,
        title: str,
        description: str,
        approval_type: ApprovalType | str,
        entity_type: str,
        entity_id: str,
        requester_id: str,
        requester_role: str,
        district_id: str = "DISTRICT_001",
        status: ApprovalStatus | str = ApprovalStatus.DRAFT,
        stages: Optional[List[ApprovalStage]] = None,
        current_stage_index: int = 0,
        decisions: Optional[List[ApprovalDecision]] = None,
        history: Optional[List[ApprovalHistory]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1,
    ) -> None:
        self.approval_id = approval_id
        self.title = title
        self.description = description
        self.approval_type = (
            ApprovalType(approval_type) if isinstance(approval_type, str) else approval_type
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.requester_id = requester_id
        self.requester_role = requester_role
        self.district_id = district_id
        self.status = (
            ApprovalStatus(status) if isinstance(status, str) else status
        )
        self.stages = stages or []
        self.current_stage_index = current_stage_index
        self.decisions = decisions or []
        self.history = history or []
        self.created_at = created_at or _utc_now_iso()
        self.updated_at = updated_at or _utc_now_iso()
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.version = version

    def record_history(self, action: str, previous_state: str, new_state: str, actor_id: str, actor_role: str, details: Optional[Dict[str, Any]] = None) -> ApprovalHistory:
        entry = ApprovalHistory(
            history_id=f"hist_{uuid.uuid4().hex[:12]}",
            approval_id=self.approval_id,
            action=action,
            previous_state=str(previous_state),
            new_state=str(new_state),
            actor_id=actor_id,
            actor_role=actor_role,
            details=details or {},
            timestamp=_utc_now_iso(),
        )
        self.history.append(entry)
        self.updated_at = entry.timestamp
        self.version += 1
        return entry

    def submit(self, actor_id: str, actor_role: str) -> None:
        if self.status not in (ApprovalStatus.DRAFT, ApprovalStatus.RETURNED):
            raise InvalidApprovalStateError(
                f"Cannot submit approval in state '{self.status.value}'"
            )
        prev_state = self.status.value
        if not self.stages:
            raise InvalidApprovalStateError("Cannot submit approval request without stages")

        self.status = ApprovalStatus.SUBMITTED
        self.current_stage_index = 0
        self.stages[0].status = ApprovalStageStatus.IN_PROGRESS
        self.stages[0].updated_at = _utc_now_iso()
        self.status = ApprovalStatus.UNDER_REVIEW

        self.record_history(
            action="SUBMIT",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id=actor_id,
            actor_role=actor_role,
            details={"current_stage": self.stages[0].stage_name},
        )

    def current_stage(self) -> Optional[ApprovalStage]:
        if 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

    def approve_stage(
        self,
        approver_id: str,
        approver_role: str,
        comments: str = "",
        conditions: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Approves the current stage. Returns True if entire workflow is approved."""
        if self.status != ApprovalStatus.UNDER_REVIEW:
            raise InvalidApprovalStateError(
                f"Cannot approve request in state '{self.status.value}'"
            )

        stage = self.current_stage()
        if not stage:
            raise InvalidApprovalStateError("No active stage to approve")

        if approver_id not in stage.approved_by:
            stage.approved_by.append(approver_id)

        decision = ApprovalDecision(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            approval_id=self.approval_id,
            stage_id=stage.stage_id,
            approver_id=approver_id,
            approver_role=approver_role,
            action=ApprovalDecisionType.APPROVE.value,
            comments=comments,
            conditions=conditions or {},
            timestamp=_utc_now_iso(),
        )
        self.decisions.append(decision)

        # Check if current stage min_approvers count is satisfied
        if len(stage.approved_by) >= stage.min_approvers:
            stage.status = ApprovalStageStatus.APPROVED
            stage.completed_at = _utc_now_iso()
            stage.comments = comments

            # Advance to next stage if available
            if self.current_stage_index + 1 < len(self.stages):
                prev_state = self.status.value
                self.current_stage_index += 1
                next_stage = self.stages[self.current_stage_index]
                next_stage.status = ApprovalStageStatus.IN_PROGRESS
                next_stage.updated_at = _utc_now_iso()

                self.record_history(
                    action="STAGE_APPROVED",
                    previous_state=prev_state,
                    new_state=self.status.value,
                    actor_id=approver_id,
                    actor_role=approver_role,
                    details={
                        "completed_stage": stage.stage_name,
                        "next_stage": next_stage.stage_name,
                        "comments": comments,
                    },
                )
                return False
            else:
                # All stages completed
                prev_state = self.status.value
                self.status = ApprovalStatus.APPROVED
                self.record_history(
                    action="WORKFLOW_APPROVED",
                    previous_state=prev_state,
                    new_state=self.status.value,
                    actor_id=approver_id,
                    actor_role=approver_role,
                    details={"completed_stage": stage.stage_name, "comments": comments},
                )
                return True
        else:
            self.record_history(
                action="APPROVER_SIGNED",
                previous_state=self.status.value,
                new_state=self.status.value,
                actor_id=approver_id,
                actor_role=approver_role,
                details={
                    "stage": stage.stage_name,
                    "approvers_count": len(stage.approved_by),
                    "min_required": stage.min_approvers,
                },
            )
            return False

    def reject(
        self,
        approver_id: str,
        approver_role: str,
        comments: str = "",
        conditions: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.status != ApprovalStatus.UNDER_REVIEW:
            raise InvalidApprovalStateError(
                f"Cannot reject request in state '{self.status.value}'"
            )

        stage = self.current_stage()
        if stage:
            stage.status = ApprovalStageStatus.REJECTED
            stage.rejected_by = approver_id
            stage.comments = comments
            stage.completed_at = _utc_now_iso()

        decision = ApprovalDecision(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            approval_id=self.approval_id,
            stage_id=stage.stage_id if stage else "unknown",
            approver_id=approver_id,
            approver_role=approver_role,
            action=ApprovalDecisionType.REJECT.value,
            comments=comments,
            conditions=conditions or {},
            timestamp=_utc_now_iso(),
        )
        self.decisions.append(decision)

        prev_state = self.status.value
        self.status = ApprovalStatus.REJECTED

        self.record_history(
            action="REJECT",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id=approver_id,
            actor_role=approver_role,
            details={"rejected_at_stage": stage.stage_name if stage else "N/A", "comments": comments},
        )

    def return_for_revision(self, approver_id: str, approver_role: str, comments: str = "") -> None:
        if self.status != ApprovalStatus.UNDER_REVIEW:
            raise InvalidApprovalStateError(
                f"Cannot return request for revision in state '{self.status.value}'"
            )

        stage = self.current_stage()
        if stage:
            stage.status = ApprovalStageStatus.PENDING
            stage.comments = comments

        decision = ApprovalDecision(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            approval_id=self.approval_id,
            stage_id=stage.stage_id if stage else "unknown",
            approver_id=approver_id,
            approver_role=approver_role,
            action=ApprovalDecisionType.RETURN_FOR_REVISION.value,
            comments=comments,
            timestamp=_utc_now_iso(),
        )
        self.decisions.append(decision)

        prev_state = self.status.value
        self.status = ApprovalStatus.RETURNED

        self.record_history(
            action="RETURN_FOR_REVISION",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id=approver_id,
            actor_role=approver_role,
            details={"returned_from_stage": stage.stage_name if stage else "N/A", "comments": comments},
        )

    def cancel(self, actor_id: str, actor_role: str, reason: str = "") -> None:
        if self.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED, ApprovalStatus.EXPIRED):
            raise InvalidApprovalStateError(
                f"Cannot cancel request in terminal state '{self.status.value}'"
            )

        prev_state = self.status.value
        self.status = ApprovalStatus.CANCELLED

        self.record_history(
            action="CANCEL",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id=actor_id,
            actor_role=actor_role,
            details={"reason": reason},
        )

    def expire(self, reason: str = "Approval timeout expired") -> None:
        if self.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED, ApprovalStatus.EXPIRED):
            return

        prev_state = self.status.value
        self.status = ApprovalStatus.EXPIRED

        self.record_history(
            action="EXPIRE",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id="SYSTEM",
            actor_role="SYSTEM",
            details={"reason": reason},
        )

    def escalate(self, actor_id: str, actor_role: str, reason: str = "", target_role: Optional[str] = None) -> None:
        if self.status != ApprovalStatus.UNDER_REVIEW:
            raise InvalidApprovalStateError(
                f"Cannot escalate request in state '{self.status.value}'"
            )

        stage = self.current_stage()
        if stage:
            stage.status = ApprovalStageStatus.ESCALATED
            if target_role:
                stage.required_role = target_role

        decision = ApprovalDecision(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            approval_id=self.approval_id,
            stage_id=stage.stage_id if stage else "unknown",
            approver_id=actor_id,
            approver_role=actor_role,
            action=ApprovalDecisionType.ESCALATE.value,
            comments=reason,
            timestamp=_utc_now_iso(),
        )
        self.decisions.append(decision)

        prev_state = self.status.value
        self.status = ApprovalStatus.ESCALATED

        self.record_history(
            action="ESCALATE",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id=actor_id,
            actor_role=actor_role,
            details={"reason": reason, "target_role": target_role},
        )

    def resubmit(self, actor_id: str, actor_role: str, updated_metadata: Optional[Dict[str, Any]] = None) -> None:
        if self.status not in (ApprovalStatus.RETURNED, ApprovalStatus.ESCALATED, ApprovalStatus.DRAFT):
            raise InvalidApprovalStateError(
                f"Cannot resubmit request in state '{self.status.value}'"
            )

        if updated_metadata:
            self.metadata.update(updated_metadata)

        prev_state = self.status.value
        self.status = ApprovalStatus.UNDER_REVIEW
        
        # Reset stages to pending except stage 0 in progress
        for i, stage in enumerate(self.stages):
            stage.approved_by = []
            stage.rejected_by = None
            stage.comments = None
            stage.completed_at = None
            if i == 0:
                stage.status = ApprovalStageStatus.IN_PROGRESS
            else:
                stage.status = ApprovalStageStatus.PENDING

        self.current_stage_index = 0

        self.record_history(
            action="RESUBMIT",
            previous_state=prev_state,
            new_state=self.status.value,
            actor_id=actor_id,
            actor_role=actor_role,
            details={"updated_metadata": updated_metadata or {}},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "title": self.title,
            "description": self.description,
            "approval_type": self.approval_type.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "requester_id": self.requester_id,
            "requester_role": self.requester_role,
            "district_id": self.district_id,
            "status": self.status.value,
            "stages": [s.to_dict() for s in self.stages],
            "current_stage_index": self.current_stage_index,
            "decisions": [d.to_dict() for d in self.decisions],
            "history": [h.to_dict() for h in self.history],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApprovalAggregate:
        return cls(
            approval_id=data["approval_id"],
            title=data["title"],
            description=data.get("description", ""),
            approval_type=data["approval_type"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            requester_id=data["requester_id"],
            requester_role=data["requester_role"],
            district_id=data.get("district_id", "DISTRICT_001"),
            status=data.get("status", ApprovalStatus.DRAFT.value),
            stages=[ApprovalStage.from_dict(s) for s in data.get("stages", [])],
            current_stage_index=data.get("current_stage_index", 0),
            decisions=[ApprovalDecision.from_dict(d) for d in data.get("decisions", [])],
            history=[ApprovalHistory.from_dict(h) for h in data.get("history", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
        )
