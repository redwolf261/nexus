import asyncio
from backend.events.event_models import BaseEvent
from backend.events.event_types import EventType
from backend.database import SessionLocal
from backend.core.logging import logger

async def process_intelligence_event(event: BaseEvent):
    """
    Background worker that listens for specific operations (like a new case or entity attached)
    and runs the heavy intelligence engines asynchronously.
    """
    if event.event_type not in [EventType.ENTITY_ATTACHED, EventType.NEW_CASE]:
        return

    logger.info(f"[Worker] Processing intelligence for event {event.event_id} ({event.event_type})")
    
    # We must use a separate database session for background tasks
    db = SessionLocal()
    try:
        case_id = event.case_id or event.payload.get("investigation_id")
        if not case_id:
            return

        # 1. Recalculate Risk
        from backend.intelligence.scoring import IntelligenceScoring
        scoring = IntelligenceScoring(db)
        risk = scoring.calculate_case_risk(case_id)
        
        # 2. Trigger Overlap check
        from backend.intelligence.entity_resolution import EntityResolutionEngine
        from backend.repositories.investigations_repo import InvestigationsRepository
        er = EntityResolutionEngine(db)
        inv_repo = InvestigationsRepository(db)
        
        entities = inv_repo.get_entities(case_id)
        target_ents = [{"entity_id": e.entity_id, "entity_type": e.entity_type} for e in entities]
        overlaps = er.get_cross_case_overlaps(target_ents)
        
        # We would then publish a new event. To avoid circular imports, 
        # we'll import the dispatcher locally inside the async function.
        from backend.events.dispatcher import EventDispatcher
        
        # Publish Risk Updated Event
        risk_event = BaseEvent(
            event_type=EventType.RISK_SCORE_CHANGED,
            payload={"risk_metrics": risk},
            case_id=case_id
        )
        await EventDispatcher.publish(risk_event, db)
        
        # Publish Overlap Discovered Event if applicable
        valid_overlaps = [o for o in overlaps if o["investigation_id"] != case_id]
        if valid_overlaps:
            from backend.db.schema import EventRecord
            import json
            existing_events = db.query(EventRecord).filter(
                EventRecord.case_id == case_id,
                EventRecord.event_type == EventType.INTELLIGENCE_DISCOVERED.value
            ).all()
            
            is_duplicate = False
            for record in existing_events:
                rec_payload = json.loads(record.payload) if isinstance(record.payload, str) else record.payload
                if rec_payload.get("type") == "CROSS_CASE_OVERLAP" and rec_payload.get("overlaps") == valid_overlaps:
                    is_duplicate = True
                    # Just update timestamp on the record to bring it to top if requested (but here we just skip duplicate)
                    break
            
            if not is_duplicate:
                overlap_event = BaseEvent(
                    event_type=EventType.INTELLIGENCE_DISCOVERED,
                    payload={"type": "CROSS_CASE_OVERLAP", "overlaps": valid_overlaps},
                    case_id=case_id
                )
                await EventDispatcher.publish(overlap_event, db)
            
    except Exception as e:
        logger.error(f"[Worker] Intelligence processing failed: {str(e)}")
    finally:
        db.close()
