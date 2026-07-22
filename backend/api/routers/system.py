from fastapi import APIRouter
from backend.api.routers.ws import manager
import psutil
import os

router = APIRouter(prefix="/api/system", tags=["System"])

from backend.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    """Returns observability metrics for the event-driven platform."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    ws_metrics = {channel: len(clients) for channel, clients in manager.active_connections.items()}
    total_clients = sum(ws_metrics.values())
    
    from sqlalchemy import func
    from backend.db.schema import BackgroundJob, EventRecord
    
    job_stats = db.query(BackgroundJob.state, func.count(BackgroundJob.id)).group_by(BackgroundJob.state).all()
    jobs_summary = {state: count for state, count in job_stats}
    
    events_count = db.query(func.count(EventRecord.event_id)).scalar()

    return {
        "status": "operational",
        "memory_mb": round(memory_info.rss / (1024 * 1024), 2),
        "events": {
            "total_events": events_count
        },
        "websockets": {
            "total_connected_clients": total_clients,
            "channels": ws_metrics
        },
        "background_jobs": jobs_summary
    }
