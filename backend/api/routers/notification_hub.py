"""Notification Hub REST API Router (Phase 8.5 Milestone 2 Deliverable 7).

Exposes REST endpoints for Inbox management, Threads, Digests, Reminders, Bulk Actions,
State toggles (Pin/Star/Archive), Search, and Communication Analytics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_current_user
from backend.db.schema import User
from backend.notification.analytics import CommunicationAnalyticsEngine
from backend.notification.digest_engine import DigestEngine, DigestType
from backend.notification.inbox_service import InboxService
from backend.notification.notification_service import NotificationService
from backend.notification.reminder_engine import ReminderEngine
from backend.notification.thread_engine import ThreadEngine

router = APIRouter(prefix="/api/notification-hub", tags=["Notification Hub & Analytics"])

_notification_service = NotificationService()
_inbox_service = InboxService(service=_notification_service)
_digest_engine = DigestEngine(service=_notification_service)
_reminder_engine = ReminderEngine(service=_notification_service)
_thread_engine = ThreadEngine(service=_notification_service)
_analytics_engine = CommunicationAnalyticsEngine(service=_notification_service)


def get_notification_service() -> NotificationService:
    return _notification_service


def get_inbox_service() -> InboxService:
    return _inbox_service


def get_digest_engine() -> DigestEngine:
    return _digest_engine


def get_reminder_engine() -> ReminderEngine:
    return _reminder_engine


def get_thread_engine() -> ThreadEngine:
    return _thread_engine


def get_analytics_engine() -> CommunicationAnalyticsEngine:
    return _analytics_engine


# Request Schemas
class GenerateDigestRequest(BaseModel):
    digest_type: str = Field("MORNING_DIGEST", description="MORNING_DIGEST, EVENING_DIGEST, SHIFT_DIGEST, DAILY_SUMMARY, WEEKLY_SUMMARY, SUPERVISOR_DIGEST, ACP_DIGEST, DCP_DIGEST")


class PinRequest(BaseModel):
    notification_id: str = Field(..., max_length=100)
    is_pinned: bool = True


class StarRequest(BaseModel):
    notification_id: str = Field(..., max_length=100)
    is_starred: bool = True


class ArchiveRequest(BaseModel):
    notification_id: str = Field(..., max_length=100)
    is_archived: bool = True


class BulkActionRequest(BaseModel):
    action: str = Field(..., description="ACKNOWLEDGE, DISMISS, ARCHIVE")
    notification_ids: List[str] = Field(..., min_length=1)


class ScheduleReminderRequest(BaseModel):
    notification_id: str = Field(..., max_length=100)


@router.get("/inbox")
def get_inbox(
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    """Queries operational inbox with filtering, sorting, pinning, and category counters."""
    return service.get_inbox(
        recipient_id=current_user.username,
        category=category,
        priority=priority,
        search_query=search,
        include_archived=include_archived,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.get("/search")
def search_inbox(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    """Searches notifications in operational inbox."""
    return service.search(recipient_id=current_user.username, query=q, limit=limit)


@router.get("/thread/{id}")
def get_thread(
    id: str,
    entity_type: str = Query("CASE", description="CASE, APPROVAL, TASK, ESCALATION, ASSIGNMENT"),
    cursor: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    engine: ThreadEngine = Depends(get_thread_engine),
):
    """Queries notification conversation thread for an operational entity."""
    thread = engine.get_thread(
        entity_type=entity_type,
        entity_id=id,
        recipient_id=current_user.username,
        cursor=cursor,
        limit=limit,
    )
    return thread.to_dict()


@router.get("/digests")
def list_digests(
    current_user: User = Depends(get_current_user),
    engine: DigestEngine = Depends(get_digest_engine),
):
    """Generates default digest content for current user."""
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    digest = engine.generate_digest(
        digest_type=DigestType.MORNING_DIGEST,
        recipient_id=current_user.username,
        recipient_role=role_str,
    )
    return {
        "digests": [digest.to_dict()],
    }


@router.post("/digest/generate")
def generate_digest(
    body: GenerateDigestRequest,
    current_user: User = Depends(get_current_user),
    engine: DigestEngine = Depends(get_digest_engine),
):
    """Generates a specific deterministic digest."""
    try:
        dtype = DigestType(body.digest_type.upper())
        role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        digest = engine.generate_digest(
            digest_type=dtype,
            recipient_id=current_user.username,
            recipient_role=role_str,
        )
        return digest.to_dict()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/pin")
def pin_notification(
    body: PinRequest,
    current_user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    """Pins or unpins a notification in inbox."""
    success = service.pin(body.notification_id, is_pinned=body.is_pinned)
    return {"notification_id": body.notification_id, "is_pinned": success}


@router.post("/star")
def star_notification(
    body: StarRequest,
    current_user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    """Stars or unstars a notification in inbox."""
    success = service.star(body.notification_id, is_starred=body.is_starred)
    return {"notification_id": body.notification_id, "is_starred": success}


@router.post("/archive")
def archive_notification(
    body: ArchiveRequest,
    current_user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    """Archives or unarchives a notification."""
    success = service.archive(body.notification_id, is_archived=body.is_archived)
    return {"notification_id": body.notification_id, "is_archived": success}


@router.post("/bulk")
def execute_bulk_action(
    body: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    """Executes bulk operations (ACKNOWLEDGE, DISMISS, ARCHIVE) on multiple notifications."""
    action_upper = body.action.upper()
    if action_upper == "ACKNOWLEDGE":
        count = service.bulk_acknowledge(body.notification_ids, actor_id=current_user.username)
    elif action_upper == "DISMISS":
        count = service.bulk_dismiss(body.notification_ids, actor_id=current_user.username)
    elif action_upper == "ARCHIVE":
        count = service.bulk_archive(body.notification_ids, is_archived=True)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported bulk action '{body.action}'")

    return {"action": action_upper, "processed_count": count}


@router.get("/analytics")
def get_communication_analytics(
    current_user: User = Depends(get_current_user),
    engine: CommunicationAnalyticsEngine = Depends(get_analytics_engine),
):
    """Computes deterministic communication analytics report."""
    report = engine.generate_analytics()
    return report.to_dict()


@router.get("/reminders")
def list_reminders(
    current_user: User = Depends(get_current_user),
    engine: ReminderEngine = Depends(get_reminder_engine),
):
    """Queries scheduled reminder records."""
    recs = engine.list_reminders(recipient_id=current_user.username)
    return {
        "reminders": [r.to_dict() for r in recs],
    }


@router.post("/reminder")
def schedule_reminder(
    body: ScheduleReminderRequest,
    current_user: User = Depends(get_current_user),
    notif_service: NotificationService = Depends(get_notification_service),
    engine: ReminderEngine = Depends(get_reminder_engine),
):
    """Schedules an escalating reminder for a notification."""
    agg = notif_service.repository.get_by_id(body.notification_id)
    if not agg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{body.notification_id}' not found")

    rec = engine.schedule_reminder(agg, recipient_id=current_user.username)
    if not rec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reminder suppressed or max reminders reached")

    return rec.to_dict()
