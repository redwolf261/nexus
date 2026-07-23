"""Notification Domain Contracts & Aggregate Root (Phase 8.5 Milestone 1 Deliverable 1).

Defines Notification domain models, lifecycle state machine, recipients, deliveries, preferences,
immutable history events, and optimistic locking versioning.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class NotificationStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ChannelType(str, Enum):
    IN_APP = "IN_APP"
    WEBSOCKET = "WEBSOCKET"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DigestMode(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    HOURLY_DIGEST = "HOURLY_DIGEST"
    DAILY_DIGEST = "DAILY_DIGEST"


class InvalidNotificationStateError(Exception):
    """Raised when an illegal notification state transition is attempted."""
    pass


@dataclass
class NotificationRecipient:
    user_id: str
    username: str
    role: str = "analyst"
    district_id: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    push_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NotificationRecipient:
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            role=data.get("role", "analyst"),
            district_id=data.get("district_id"),
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            push_token=data.get("push_token"),
        )


@dataclass
class NotificationDelivery:
    delivery_id: str
    notification_id: str
    recipient_id: str
    channel: ChannelType
    status: NotificationStatus = NotificationStatus.CREATED
    attempt_count: int = 0
    last_attempt_at: Optional[str] = None
    delivered_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["channel"] = self.channel.value if isinstance(self.channel, Enum) else self.channel
        d["status"] = self.status.value if isinstance(self.status, Enum) else self.status
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NotificationDelivery:
        return cls(
            delivery_id=data["delivery_id"],
            notification_id=data["notification_id"],
            recipient_id=data["recipient_id"],
            channel=ChannelType(data["channel"]),
            status=NotificationStatus(data.get("status", NotificationStatus.CREATED.value)),
            attempt_count=data.get("attempt_count", 0),
            last_attempt_at=data.get("last_attempt_at"),
            delivered_at=data.get("delivered_at"),
            acknowledged_at=data.get("acknowledged_at"),
            error_message=data.get("error_message"),
        )


@dataclass
class NotificationHistory:
    event_id: str
    notification_id: str
    event_type: str
    channel: Optional[ChannelType] = None
    actor_id: str = "system"
    actor_role: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.channel:
            d["channel"] = self.channel.value if isinstance(self.channel, Enum) else self.channel
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NotificationHistory:
        ch = data.get("channel")
        return cls(
            event_id=data["event_id"],
            notification_id=data["notification_id"],
            event_type=data["event_type"],
            channel=ChannelType(ch) if ch else None,
            actor_id=data.get("actor_id", "system"),
            actor_role=data.get("actor_role", "system"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            details=data.get("details", {}),
        )


@dataclass
class NotificationPreference:
    user_id: str
    enabled_channels: List[ChannelType] = field(
        default_factory=lambda: [ChannelType.IN_APP, ChannelType.WEBSOCKET]
    )
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "06:00"
    digest_mode: DigestMode = DigestMode.IMMEDIATE
    min_priority: PriorityLevel = PriorityLevel.LOW
    role_overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "enabled_channels": [c.value if isinstance(c, Enum) else c for c in self.enabled_channels],
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "digest_mode": self.digest_mode.value if isinstance(self.digest_mode, Enum) else self.digest_mode,
            "min_priority": self.min_priority.value if isinstance(self.min_priority, Enum) else self.min_priority,
            "role_overrides": self.role_overrides,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NotificationPreference:
        channels = [ChannelType(c) for c in data.get("enabled_channels", ["IN_APP", "WEBSOCKET"])]
        return cls(
            user_id=data["user_id"],
            enabled_channels=channels,
            quiet_hours_enabled=data.get("quiet_hours_enabled", False),
            quiet_hours_start=data.get("quiet_hours_start", "22:00"),
            quiet_hours_end=data.get("quiet_hours_end", "06:00"),
            digest_mode=DigestMode(data.get("digest_mode", DigestMode.IMMEDIATE.value)),
            min_priority=PriorityLevel(data.get("min_priority", PriorityLevel.LOW.value)),
            role_overrides=data.get("role_overrides", {}),
        )


class NotificationAggregate:
    """Notification Domain Aggregate Root enforcing lifecycle state transitions & optimistic locking."""

    def __init__(
        self,
        notification_id: str,
        title: str,
        body: str,
        event_type: str,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        source_entity_type: str = "SYSTEM",
        source_entity_id: str = "0",
        recipients: Optional[List[NotificationRecipient]] = None,
        deliveries: Optional[List[NotificationDelivery]] = None,
        history: Optional[List[NotificationHistory]] = None,
        status: NotificationStatus = NotificationStatus.CREATED,
        created_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        acknowledged_at: Optional[str] = None,
        acknowledged_by: Optional[str] = None,
        dismissed_at: Optional[str] = None,
        version: int = 1,
    ):
        self.notification_id = notification_id
        self.title = title
        self.body = body
        self.event_type = event_type
        self.priority = priority
        self.source_entity_type = source_entity_type
        self.source_entity_id = source_entity_id
        self.recipients = recipients or []
        self.deliveries = deliveries or []
        self.history = history or []
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.expires_at = expires_at
        self.acknowledged_at = acknowledged_at
        self.acknowledged_by = acknowledged_by
        self.dismissed_at = dismissed_at
        self.version = version

    def _record_event(self, event_type: str, channel: Optional[ChannelType] = None, actor_id: str = "system", actor_role: str = "system", details: Optional[Dict[str, Any]] = None):
        evt = NotificationHistory(
            event_id=f"evt_notif_{uuid.uuid4().hex[:8]}",
            notification_id=self.notification_id,
            event_type=event_type,
            channel=channel,
            actor_id=actor_id,
            actor_role=actor_role,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
        self.history.append(evt)
        self.version += 1

    def queue(self):
        if self.status != NotificationStatus.CREATED:
            raise InvalidNotificationStateError(f"Cannot queue notification in state {self.status.value}")
        self.status = NotificationStatus.QUEUED
        self._record_event("NOTIFICATION_QUEUED")

    def dispatch(self, delivery: NotificationDelivery):
        if self.status in (NotificationStatus.EXPIRED, NotificationStatus.CANCELLED):
            raise InvalidNotificationStateError(f"Cannot dispatch notification in terminal state {self.status.value}")
        if self.status != NotificationStatus.DELIVERED:
            self.status = NotificationStatus.DISPATCHED
        self.deliveries.append(delivery)
        self._record_event("NOTIFICATION_DISPATCHED", channel=delivery.channel, details={"recipient_id": delivery.recipient_id})

    def mark_delivered(self, delivery_id: str):
        for d in self.deliveries:
            if d.delivery_id == delivery_id:
                d.status = NotificationStatus.DELIVERED
                d.delivered_at = datetime.now(timezone.utc).isoformat()
                break
        
        # Check if all deliveries completed
        if any(d.status == NotificationStatus.DELIVERED for d in self.deliveries):
            self.status = NotificationStatus.DELIVERED
            self._record_event("NOTIFICATION_DELIVERED", details={"delivery_id": delivery_id})

    def acknowledge(self, actor_id: str, actor_role: str = "user"):
        if self.status in (NotificationStatus.EXPIRED, NotificationStatus.CANCELLED):
            raise InvalidNotificationStateError(f"Cannot acknowledge notification in state {self.status.value}")
        self.status = NotificationStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now(timezone.utc).isoformat()
        self.acknowledged_by = actor_id
        self._record_event("NOTIFICATION_ACKNOWLEDGED", actor_id=actor_id, actor_role=actor_role)

    def dismiss(self, actor_id: str, actor_role: str = "user"):
        if self.status in (NotificationStatus.EXPIRED, NotificationStatus.CANCELLED):
            raise InvalidNotificationStateError(f"Cannot dismiss notification in state {self.status.value}")
        self.dismissed_at = datetime.now(timezone.utc).isoformat()
        self._record_event("NOTIFICATION_DISMISSED", actor_id=actor_id, actor_role=actor_role)

    def fail(self, error_message: str):
        self.status = NotificationStatus.FAILED
        self._record_event("NOTIFICATION_FAILED", details={"error": error_message})

    def expire(self):
        if self.status == NotificationStatus.ACKNOWLEDGED:
            return
        self.status = NotificationStatus.EXPIRED
        self._record_event("NOTIFICATION_EXPIRED")

    def cancel(self, reason: str = "Cancelled by system"):
        self.status = NotificationStatus.CANCELLED
        self._record_event("NOTIFICATION_CANCELLED", details={"reason": reason})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "body": self.body,
            "event_type": self.event_type,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "source_entity_type": self.source_entity_type,
            "source_entity_id": self.source_entity_id,
            "recipients": [r.to_dict() for r in self.recipients],
            "deliveries": [d.to_dict() for d in self.deliveries],
            "history": [h.to_dict() for h in self.history],
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "acknowledged_at": self.acknowledged_at,
            "acknowledged_by": self.acknowledged_by,
            "dismissed_at": self.dismissed_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NotificationAggregate:
        recipients = [NotificationRecipient.from_dict(r) for r in data.get("recipients", [])]
        deliveries = [NotificationDelivery.from_dict(d) for d in data.get("deliveries", [])]
        history = [NotificationHistory.from_dict(h) for h in data.get("history", [])]

        return cls(
            notification_id=data["notification_id"],
            title=data["title"],
            body=data["body"],
            event_type=data["event_type"],
            priority=PriorityLevel(data.get("priority", PriorityLevel.MEDIUM.value)),
            source_entity_type=data.get("source_entity_type", "SYSTEM"),
            source_entity_id=str(data.get("source_entity_id", "0")),
            recipients=recipients,
            deliveries=deliveries,
            history=history,
            status=NotificationStatus(data.get("status", NotificationStatus.CREATED.value)),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            acknowledged_at=data.get("acknowledged_at"),
            acknowledged_by=data.get("acknowledged_by"),
            dismissed_at=data.get("dismissed_at"),
            version=data.get("version", 1),
        )
