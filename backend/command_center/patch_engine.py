"""Incremental Dashboard Patch Engine (Phase 8.3 Milestone 2).

Computes deterministic section-level deltas and builds DashboardPatchDTO payloads.
Avoids full dashboard rebuilds by computing updates for affected sections only.
"""

from __future__ import annotations

import time
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

from backend.command_center.contracts import DashboardPatchDTO, SupervisorDashboardDTO
from backend.core.logging import logger


@dataclass(frozen=True)
class DashboardDelta:
    """Represents changes to specific sections of the command dashboard."""
    target_sections: List[str]  # e.g. ["active_cases", "metrics", "workload"]
    delta_data: Dict[str, Any]
    timestamp: str


class PatchBuilder:
    """Builder for constructing DashboardPatchDTO objects with monotonic sequence tracking."""

    @staticmethod
    def build_patch(
        target_sections: List[str],
        delta_data: Dict[str, Any],
        sequence: int
    ) -> DashboardPatchDTO:
        """Construct a serializable DashboardPatchDTO in <10ms."""
        patch_id = f"PATCH-{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.utcnow().isoformat()

        return DashboardPatchDTO(
            patch_id=patch_id,
            target_sections=list(target_sections),
            delta_data=dict(delta_data),
            timestamp=now_iso,
            sequence=sequence,
        )


class DeltaComputer:
    """Computes section-level deltas between dashboard states."""

    @staticmethod
    def compute_section_delta(
        old_dto: Optional[SupervisorDashboardDTO],
        new_dto: SupervisorDashboardDTO,
        affected_sections: Optional[List[str]] = None
    ) -> DashboardDelta:
        """Compute delta data for specified target sections."""
        target_sections = affected_sections or ["active_cases", "analyst_workloads", "metrics"]
        delta_data: Dict[str, Any] = {}

        dto_dict = new_dto.to_dict()
        for sec in target_sections:
            if sec in dto_dict:
                delta_data[sec] = dto_dict[sec]

        return DashboardDelta(
            target_sections=target_sections,
            delta_data=delta_data,
            timestamp=datetime.utcnow().isoformat(),
        )
