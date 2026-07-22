"""Audit logging for task engine operations.

Wraps AuditLog schema to provide a clean .log() interface for the TaskEngine.
All state changes are recorded atomically with the transaction.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.schema import AuditLog


class AuditLogger:
    """Audit trail writer for operational events."""

    def __init__(self, session: Session):
        self.session = session

    def log(
        self,
        user_id: Optional[str] = None,
        action: str = "",
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log an audit event.

        Args:
            user_id: User performing the action
            action: Action type (e.g., TASK_ASSIGNED, TASK_COMPLETED)
            target_id: Entity being acted on (e.g., task ID, investigation ID)
            details: Optional structured metadata (stored as separate audit fields)

        Returns:
            Created AuditLog entry

        Note:
            The entry is added to the session and flushed but not committed.
            Caller is responsible for commit (allows atomicity with state changes).
        """
        entry = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            target_id=target_id,
            status="SUCCESS"  # Default; caller can override if needed
        )
        self.session.add(entry)
        self.session.flush()  # Make it visible but don't commit yet
        return entry
