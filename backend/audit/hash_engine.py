import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

GENESIS_HASH = "0" * 64

class HashEngine:
    @staticmethod
    def canonical_json(data: Optional[Any]) -> str:
        if data is None:
            return ""
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return json.dumps(parsed, sort_keys=True, separators=(',', ':'))
            except Exception:
                return data
        if isinstance(data, (dict, list)):
            return json.dumps(data, sort_keys=True, separators=(',', ':'))
        return str(data)

    @classmethod
    def compute_hash(
        cls,
        prev_hash: str,
        sequence: int,
        timestamp: datetime,
        event_type: str,
        event_category: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_version: int = 1,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        payload_str: Optional[str] = None,
        previous_state_str: Optional[str] = None,
        new_state_str: Optional[str] = None,
    ) -> str:
        """
        Computes deterministic SHA-256 hash for an audit ledger entry.
        """
        ts_iso = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        payload_canon = cls.canonical_json(payload_str)
        prev_canon = cls.canonical_json(previous_state_str)
        new_canon = cls.canonical_json(new_state_str)

        raw_content = "|".join([
            str(prev_hash),
            str(sequence),
            ts_iso,
            str(event_type),
            str(event_category),
            str(entity_type or ""),
            str(entity_id or ""),
            str(entity_version),
            str(actor_id or ""),
            str(correlation_id or ""),
            str(request_id or ""),
            payload_canon,
            prev_canon,
            new_canon
        ])

        return hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

    @classmethod
    def verify_entry_hash(cls, record: Any) -> bool:
        expected_hash = cls.compute_hash(
            prev_hash=record.prev_hash,
            sequence=record.sequence,
            timestamp=record.timestamp,
            event_type=record.event_type,
            event_category=record.event_category,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            entity_version=record.entity_version,
            actor_id=record.actor_id,
            correlation_id=record.correlation_id,
            request_id=record.request_id,
            payload_str=record.payload,
            previous_state_str=record.previous_state,
            new_state_str=record.new_state
        )
        return expected_hash == record.hash
