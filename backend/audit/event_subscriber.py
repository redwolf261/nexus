import json
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.audit.service import AuditService
from backend.events.event_models import BaseEvent


class AuditEventSubscriber:
    @staticmethod
    def consume_event(event: Any, db: Session) -> None:
        """
        Consumes BaseEvent or generic event object and creates an immutable Audit Ledger record.
        """
        if not event:
            return

        event_type = getattr(event, "event_type", "SYSTEM_EVENT")
        if hasattr(event_type, "value"):
            event_type = event_type.value
        event_type = str(event_type)

        user_id = getattr(event, "user_id", None)
        case_id = getattr(event, "case_id", None)
        payload = getattr(event, "payload", {})

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {"raw": payload}
        elif not isinstance(payload, dict):
            payload = {"payload": str(payload)}

        # Extract entity type & id from payload or case_id
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")

        if not entity_type and case_id:
            entity_type = "Investigation"
            entity_id = case_id
        elif not entity_type and "task_id" in payload:
            entity_type = "Task"
            entity_id = payload.get("task_id")
        elif not entity_type and "approval_id" in payload:
            entity_type = "Approval"
            entity_id = payload.get("approval_id")

        correlation_id = payload.get("correlation_id") or getattr(event, "correlation_id", None)
        request_id = payload.get("request_id") or getattr(event, "request_id", None)
        session_id = payload.get("session_id") or getattr(event, "session_id", None)

        previous_state = payload.get("previous_state")
        new_state = payload.get("new_state")

        AuditService.log_event(
            db=db,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=user_id,
            correlation_id=correlation_id,
            request_id=request_id,
            session_id=session_id,
            previous_state=previous_state,
            new_state=new_state,
            payload=payload,
            timestamp=getattr(event, "timestamp", None)
        )
