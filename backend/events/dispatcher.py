import asyncio
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session


try:
    from fastapi import BackgroundTasks
except ImportError:
    BackgroundTasks = None

try:
    from backend.api.routers.ws import manager
except ImportError:
    manager = None

from backend.events.event_models import BaseEvent
from backend.db.schema import EventRecord
from backend.core.logging import logger


# Import worker tasks
from backend.workers.intelligence_worker import process_intelligence_event

class EventDispatcher:
    @staticmethod
    def publish_sync(event: BaseEvent, db: Session) -> Optional[EventRecord]:
        """Synchronous event publisher for DB persistence and audit stream."""
        logger.info(f"Publishing sync event: {event.event_type} (Case: {event.case_id})")
        try:
            seq = None
            if event.case_id:
                from backend.db.schema import Investigation
                inv = db.query(Investigation).filter_by(id=event.case_id).first()
                if inv:
                    inv.last_sequence = (inv.last_sequence or 0) + 1
                    seq = inv.last_sequence
                    event.sequence = seq

            record = EventRecord(
                event_id=event.event_id,
                timestamp=event.timestamp,
                event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                payload=json.dumps(event.payload) if isinstance(event.payload, dict) else str(event.payload),
                user_id=event.user_id,
                case_id=event.case_id,
                sequence=seq,
            )

            db.add(record)
            db.flush()

            # Automatic Immutable Audit Ledger Ingestion
            try:
                from backend.audit.event_subscriber import AuditEventSubscriber
                AuditEventSubscriber.consume_event(event, db)
            except Exception as audit_err:
                logger.error(f"Audit ledger ingestion error: {str(audit_err)}")

            # Real-time Compliance Evaluation
            try:
                from backend.compliance.event_listener import ComplianceEventListener
                ComplianceEventListener.consume_event(event, db)
            except Exception as comp_err:
                logger.error(f"Compliance event listener error: {str(comp_err)}")

            return record
        except Exception as e:
            logger.error(f"Failed to persist sync event {event.event_id}: {str(e)}", exc_info=True)
            return None


    @staticmethod
    async def publish(event: BaseEvent, db: Session, background_tasks: BackgroundTasks = None):

        """
        Core pub/sub mechanism.
        1. Write to DB (Append-only log)
        2. Broadcast to WebSockets
        3. Trigger background workers
        """
        logger.info(f"Publishing event: {event.event_type} (Case: {event.case_id})")

        # 1. Write to DB Audit Stream
        try:
            # Assign monotonic sequence if case_id
            seq = None
            if event.case_id:
                from backend.db.schema import Investigation
                inv = db.query(Investigation).with_for_update().filter_by(id=event.case_id).first()
                if inv:
                    inv.last_sequence += 1
                    seq = inv.last_sequence
                    event.sequence = seq
            
            record = EventRecord(
                event_id=event.event_id,
                timestamp=event.timestamp,
                event_type=event.event_type.value,
                payload=json.dumps(event.payload),
                user_id=event.user_id,
                case_id=event.case_id,
                sequence=seq
            )
            db.add(record)
            db.commit()

            # Automatic Immutable Audit Ledger Ingestion
            try:
                from backend.audit.event_subscriber import AuditEventSubscriber
                AuditEventSubscriber.consume_event(event, db)
                db.commit()
            except Exception as audit_err:
                logger.error(f"Audit ledger ingestion error in async publish: {str(audit_err)}")

        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {str(e)}")
            db.rollback()
            return # Do not broadcast if persistence fails

        # 2. Broadcast via WebSocket (Fire and forget)
        event_dict = event.model_dump()
        event_dict["timestamp"] = event.timestamp.isoformat()
        
        # Route to case-specific channel if case_id exists
        if event.case_id:
            await manager.broadcast(f"case_{event.case_id}", event_dict)
            
        # Also route to a global 'intelligence' or 'dashboard' feed if necessary
        # We can route everything to the global feed for simplicity in this MVP
        await manager.broadcast("global_feed", event_dict)

        # 3. Trigger Workers reliably via BackgroundJob
        from backend.workers.job_runner import JobRunner
        
        # Don't pass db here because it's from the router and we want a fresh transaction for the job insert,
        # or we CAN pass db so the job insert is atomic with the mutation!
        # Yes, let's insert the Job in the same session, but wait, this is after db.commit() in dispatcher.
        # But we already did db.commit() above for the EventRecord.
        # Actually, let's just do it directly.
        JobRunner.submit_job(db, "process_intelligence_event", event_dict)
