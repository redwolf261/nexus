"""Approval Workflow Templates (Phase 8.4 Deliverable 5).

Defines canonical workflow stage templates for all 10 approval types supported by NEXUS.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.approval.contracts import (
    ApprovalStage,
    ApprovalStageStatus,
    ApprovalType,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalTemplates:
    """Factory creating standardized ApprovalStage pipelines for all 10 approval types."""

    @staticmethod
    def get_template_stages(
        approval_type: ApprovalType | str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[ApprovalStage]:
        app_type = ApprovalType(approval_type) if isinstance(approval_type, str) else approval_type
        meta = metadata or {}

        if app_type == ApprovalType.SEARCH_WARRANT:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Supervisor Judicial Authorization",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                )
            ]

        elif app_type == ApprovalType.ARREST_WARRANT:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Supervisor Initial Review",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                ),
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=2,
                    stage_name="ACP Final Warrant Sign-off",
                    required_role="acp",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                ),
            ]

        elif app_type == ApprovalType.EVIDENCE_COLLECTION:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Forensic Evidence Approval",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                )
            ]

        elif app_type == ApprovalType.SURVEILLANCE_REQUEST:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Supervisor Operational Review",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                ),
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=2,
                    stage_name="ACP Technical Surveillance Authorization",
                    required_role="acp",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                ),
            ]

        elif app_type == ApprovalType.INVESTIGATION_CLOSURE:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Case Review & Findings Verification",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                ),
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=2,
                    stage_name="ACP Final Case Closure Sign-off",
                    required_role="acp",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                ),
            ]

        elif app_type == ApprovalType.COLD_CASE_ARCHIVAL:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Supervisor Archival Assessment",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                )
            ]

        elif app_type == ApprovalType.CASE_REOPENING:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="ACP Case Reopening Authorization",
                    required_role="acp",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                )
            ]

        elif app_type == ApprovalType.CROSS_DISTRICT_INVESTIGATION:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="ACP Inter-district Coordination",
                    required_role="acp",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                )
            ]

        elif app_type == ApprovalType.BUDGET_RESOURCE_REQUEST:
            amount = meta.get("amount", 0)
            if amount > 500000:
                return [
                    ApprovalStage(
                        stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                        stage_order=1,
                        stage_name="ACP Resource Audit",
                        required_role="acp",
                        min_approvers=1,
                        status=ApprovalStageStatus.PENDING,
                    ),
                    ApprovalStage(
                        stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                        stage_order=2,
                        stage_name="DCP High-value Budget Sign-off",
                        required_role="dcp",
                        min_approvers=1,
                        status=ApprovalStageStatus.PENDING,
                    ),
                ]
            else:
                return [
                    ApprovalStage(
                        stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                        stage_order=1,
                        stage_name="ACP Resource Allocation",
                        required_role="acp",
                        min_approvers=1,
                        status=ApprovalStageStatus.PENDING,
                    )
                ]

        elif app_type == ApprovalType.EMERGENCY_OPERATIONAL_APPROVAL:
            return [
                ApprovalStage(
                    stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                    stage_order=1,
                    stage_name="Emergency Operational Authorization",
                    required_role="supervisor",
                    min_approvers=1,
                    status=ApprovalStageStatus.PENDING,
                )
            ]

        # Default fallback template
        return [
            ApprovalStage(
                stage_id=f"stg_{uuid.uuid4().hex[:8]}",
                stage_order=1,
                stage_name="Supervisor Review",
                required_role="supervisor",
                min_approvers=1,
                status=ApprovalStageStatus.PENDING,
            )
        ]
