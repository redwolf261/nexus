from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any, Optional
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from backend.core.logging import logger
from backend.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        # We group connections by topic/channel for PubSub
        # active_connections: dict[channel_name, list[WebSocket]]
        self.active_connections: Dict[str, List[WebSocket]] = {
            "dashboard": [],
            "alerts": [],
            "intelligence": [],
        }
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str, user_id: str = None):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
            
        logger.info(f"WS Client connected to {channel}. Total clients: {len(self.active_connections[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str, user_id: str = None):
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                
        logger.info(f"WS Client disconnected from {channel}.")

    async def disconnect_user(self, user_id: str):
        if user_id in self.user_connections:
            websockets = list(self.user_connections[user_id])
            for ws in websockets:
                try:
                    await ws.close(code=1008)
                except Exception:
                    pass
            self.user_connections[user_id] = []
            logger.info(f"Forcefully disconnected all WS connections for user {user_id}")

    async def broadcast(self, channel: str, message: dict):
        """Send message to all connected clients on a specific channel."""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to client on {channel}: {str(e)}")
                    disconnected.append(connection)
            
            # Clean up dropped connections
            for d in disconnected:
                self.disconnect(d, channel)

manager = ConnectionManager()

async def log_intelligence_event(
    db: Session,
    workspace_id: str,
    event_type: str,
    entity_id: Optional[str],
    confidence_score: Optional[float],
    explanation_json: Dict[str, Any],
    analyst_id: Optional[str] = None,
) -> str:
    """Log intelligence event to audit trail and return event_id."""
    from backend.db.schema import IntelligenceEventLog

    event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
    event = IntelligenceEventLog(
        event_id=event_id,
        workspace_id=workspace_id,
        event_type=event_type,
        entity_id=entity_id,
        confidence_score=confidence_score,
        explanation_json=explanation_json,
        analyst_id=analyst_id,
    )
    db.add(event)
    db.commit()
    return event_id

async def replay_recent_intelligence_events(
    db: Session,
    workspace_id: str,
    minutes: int = 5,
) -> List[Dict[str, Any]]:
    """Retrieve recent intelligence events for replay on reconnection."""
    from backend.db.schema import IntelligenceEventLog

    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    events = db.query(IntelligenceEventLog).filter(
        IntelligenceEventLog.workspace_id == workspace_id,
        IntelligenceEventLog.shown_at >= cutoff,
    ).order_by(IntelligenceEventLog.shown_at).all()

    return [
        {
            "type": "REPLAY",
            "event_id": e.event_id,
            "event_type": e.event_type,
            "entity_id": e.entity_id,
            "confidence_score": e.confidence_score,
            "shown_at": e.shown_at.isoformat(),
            "explanation": e.explanation_json,
        }
        for e in events
    ]

from backend.auth.deps import get_ws_current_user

@router.websocket("/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    last_sequence: int = None,
    db: Session = Depends(get_db)
):
    user = await get_ws_current_user(websocket, db)
    if not user:
        return # WebSocket already closed in get_ws_current_user

    await manager.connect(websocket, channel, user.id)

    # CRITICAL FIX #2: Replay recent intelligence events on reconnection
    if channel.startswith("workspace_"):
        workspace_id = channel.replace("workspace_", "")
        try:
            replayed_events = await replay_recent_intelligence_events(db, workspace_id, minutes=5)
            for event in replayed_events:
                await websocket.send_json(event)
            if replayed_events:
                logger.info(f"Replayed {len(replayed_events)} intelligence events to {user.id} for workspace {workspace_id}")
        except Exception as e:
            logger.warning(f"Failed to replay intelligence events: {str(e)}")

    # Offline recovery: push missing events
    if last_sequence is not None and channel.startswith("case_"):
        case_id = channel.replace("case_", "")
        from backend.db.schema import EventRecord
        missing_events = db.query(EventRecord).filter(
            EventRecord.case_id == case_id,
            EventRecord.sequence > last_sequence
        ).order_by(EventRecord.sequence.asc()).all()
        
        for record in missing_events:
            try:
                # The payload is stored as JSON string or dict depending on dialect, let's make sure it's dict
                payload = json.loads(record.payload) if isinstance(record.payload, str) else record.payload
                event_dict = {
                    "event_id": record.event_id,
                    "event_type": record.event_type,
                    "timestamp": record.timestamp.isoformat(),
                    "payload": payload,
                    "user_id": record.user_id,
                    "case_id": record.case_id,
                    "sequence": record.sequence
                }
                await websocket.send_json(event_dict)
            except Exception as e:
                logger.error(f"Failed to send missing event {record.event_id}: {e}")
    try:
        token = websocket.cookies.get("access_token")
        if not token:
            auth = websocket.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ")[1]
                
        while True:
            # Client heartbeat loop
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            
            # Periodically re-verify token expiration during heartbeat
            from backend.auth.security import decode_access_token
            if not decode_access_token(token):
                logger.warning(f"WS Client token expired, closing connection for {channel}")
                await websocket.close(code=1008)
                break
                
            if data == "ping":
                await websocket.send_text("pong")
    except asyncio.TimeoutError:
        # Re-verify token even if no message received
        from backend.auth.security import decode_access_token
        if not decode_access_token(token):
            await websocket.close(code=1008)
        manager.disconnect(websocket, channel, user.id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel, user.id)
    except Exception as e:
        manager.disconnect(websocket, channel, user.id)
