from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.db.schema import EventRecord

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("/")
def get_events(case_id: str = None, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch the append-only audit stream, optionally filtered by case."""
    query = db.query(EventRecord)
    if case_id:
        query = query.filter_by(case_id=case_id)
        
    events = query.order_by(EventRecord.timestamp.asc()).limit(limit).all()
    
    return [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "payload": e.payload,
            "user_id": e.user_id,
            "case_id": e.case_id
        }
        for e in events
    ]
