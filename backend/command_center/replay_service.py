"""WebSocket Reconnect Sequence Replay Service (Phase 8.3 Milestone 2).

Maintains a circular buffer of recent patches (ReplayWindow) per district and replays
missed events in exact monotonic sequence order upon WebSocket reconnection.
"""

from __future__ import annotations

import threading
from typing import List, Dict, Optional, Tuple

from backend.command_center.contracts import DashboardPatchDTO, ReplayResponseDTO
from backend.core.logging import logger


class ReplayService:
    """Thread-safe circular buffer for storing and replaying recent sequence patches."""

    _WINDOW_SIZE = 1000  # Retain last 1,000 sequence patches
    _replay_buffer: Dict[str, List[DashboardPatchDTO]] = {}
    _lock = threading.Lock()

    @classmethod
    def record_patch(cls, district_id: Optional[str], patch: DashboardPatchDTO):
        """Append a patch to the district's circular replay buffer."""
        key = district_id or "ALL"
        with cls._lock:
            buf = cls._replay_buffer.setdefault(key, [])
            buf.append(patch)
            if len(buf) > cls._WINDOW_SIZE:
                cls._replay_buffer[key] = buf[-cls._WINDOW_SIZE:]

    @classmethod
    def compute_replay(
        cls,
        client_last_sequence: int,
        district_id: Optional[str] = None
    ) -> ReplayResponseDTO:
        """Compute missed patches for a reconnecting client."""
        key = district_id or "ALL"
        with cls._lock:
            buf = cls._replay_buffer.get(key, [])
            current_seq = buf[-1].sequence if buf else client_last_sequence

            missed = [p for p in buf if p.sequence > client_last_sequence]

            # Detect sequence gap if buffer doesn't contain client's sequence and buffer has items
            is_gap = False
            if buf and client_last_sequence > 0:
                oldest_seq = buf[0].sequence
                if client_last_sequence < oldest_seq - 1:
                    is_gap = True

        logger.info(f"Replay request for sequence {client_last_sequence}: {len(missed)} missed patches (Gap: {is_gap})")
        return ReplayResponseDTO(
            client_last_sequence=client_last_sequence,
            current_sequence=current_seq,
            missed_patches=missed,
            is_gap_detected=is_gap,
        )
