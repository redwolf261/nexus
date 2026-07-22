from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from backend.events.event_types import EventType

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    payload: Dict[str, Any]
    user_id: Optional[str] = "SYSTEM"
    case_id: Optional[str] = None
    sequence: Optional[int] = None
