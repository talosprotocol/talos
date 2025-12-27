"""
Audit Plane for Talos Protocol (Phase 3).

Enterprise-grade audit aggregation and storage.
Protocol usable without it - this is an optional enhancement.
"""

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from collections import deque


logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    AUTHORIZATION = "AUTHORIZATION"
    DENIAL = "DENIAL"
    REVOCATION = "REVOCATION"
    DELEGATION = "DELEGATION"
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"


@dataclass
class AuditEvent:
    """
    Single audit event for the audit plane.
    
    Per PROTOCOL.md Section 5: Audit events are signed and include
    capability_hash, request_hash, response_hash for tamper detection.
    """
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    agent_id: str
    tool: str
    method: str
    capability_id: Optional[str]
    capability_hash: Optional[str]
    request_hash: Optional[str]
    response_hash: Optional[str]
    result_code: str  # ALLOWED, DENIED, etc.
    denial_reason: Optional[str] = None
    latency_us: int = 0
    session_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "tool": self.tool,
            "method": self.method,
            "capability_id": self.capability_id,
            "capability_hash": self.capability_hash,
            "request_hash": self.request_hash,
            "response_hash": self.response_hash,
            "result_code": self.result_code,
            "denial_reason": self.denial_reason,
            "latency_us": self.latency_us,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEvent":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_id=data["agent_id"],
            tool=data["tool"],
            method=data["method"],
            capability_id=data.get("capability_id"),
            capability_hash=data.get("capability_hash"),
            request_hash=data.get("request_hash"),
            response_hash=data.get("response_hash"),
            result_code=data["result_code"],
            denial_reason=data.get("denial_reason"),
            latency_us=data.get("latency_us", 0),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {}),
        )


class AuditStore:
    """
    Abstract interface for audit event storage.
    
    Implementations can use:
    - In-memory (for testing)
    - SQLite/LMDB (for local persistence)
    - Remote service (for enterprise)
    """
    
    def append(self, event: AuditEvent) -> None:
        """Append an audit event."""
        raise NotImplementedError

    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        raise NotImplementedError

    def count(self) -> int:
        """Return total number of events."""
        raise NotImplementedError


class InMemoryAuditStore(AuditStore):
    """In-memory audit store for testing and development."""

    def __init__(self, max_events: int = 10000):
        self._events: deque[AuditEvent] = deque(maxlen=max_events)

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)

    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        results = []
        for event in self._events:
            if agent_id and event.agent_id != agent_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if after and event.timestamp <= after:
                continue
            if before and event.timestamp >= before:
                continue
            results.append(event)
            if len(results) >= limit:
                break
        return results

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()


class AuditAggregator:
    """
    Aggregates audit events from multiple sources.
    
    Provides:
    - Event collection from CapabilityManager
    - Storage to AuditStore
    - Export to various formats
    - Query interface
    """

    def __init__(self, store: AuditStore | None = None):
        self._store = store or InMemoryAuditStore()
        self._event_count = 0

    def record_authorization(
        self,
        agent_id: str,
        tool: str,
        method: str,
        capability_id: Optional[str],
        allowed: bool,
        denial_reason: Optional[str] = None,
        latency_us: int = 0,
        capability_hash: Optional[str] = None,
        request_hash: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditEvent:
        """Record an authorization event."""
        import secrets
        
        event = AuditEvent(
            event_id=f"aud_{secrets.token_hex(12)}",
            event_type=AuditEventType.AUTHORIZATION if allowed else AuditEventType.DENIAL,
            timestamp=datetime.now(timezone.utc),
            agent_id=agent_id,
            tool=tool,
            method=method,
            capability_id=capability_id,
            capability_hash=capability_hash,
            request_hash=request_hash,
            response_hash=None,  # Filled in after response
            result_code="ALLOWED" if allowed else "DENIED",
            denial_reason=denial_reason,
            latency_us=latency_us,
            session_id=session_id,
        )
        
        self._store.append(event)
        self._event_count += 1
        logger.debug(f"Recorded audit event: {event.event_id}")
        
        return event

    def record_revocation(
        self,
        agent_id: str,
        capability_id: str,
        reason: str,
    ) -> AuditEvent:
        """Record a capability revocation."""
        import secrets
        
        event = AuditEvent(
            event_id=f"aud_{secrets.token_hex(12)}",
            event_type=AuditEventType.REVOCATION,
            timestamp=datetime.now(timezone.utc),
            agent_id=agent_id,
            tool="",
            method="",
            capability_id=capability_id,
            capability_hash=None,
            request_hash=None,
            response_hash=None,
            result_code="REVOKED",
            denial_reason=reason,
        )
        
        self._store.append(event)
        self._event_count += 1
        logger.info(f"Recorded revocation: {capability_id}")
        
        return event

    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events."""
        return self._store.query(
            agent_id=agent_id,
            event_type=event_type,
            after=after,
            before=before,
            limit=limit,
        )

    def export_json(self, events: list[AuditEvent] | None = None) -> str:
        """Export events to JSON."""
        if events is None:
            events = self.query(limit=10000)
        return json.dumps([e.to_dict() for e in events], indent=2)

    def export_csv(self, events: list[AuditEvent] | None = None) -> str:
        """Export events to CSV."""
        if events is None:
            events = self.query(limit=10000)
        
        if not events:
            return ""
        
        headers = ["event_id", "event_type", "timestamp", "agent_id", "tool", 
                   "method", "result_code", "denial_reason", "latency_us"]
        lines = [",".join(headers)]
        
        for e in events:
            row = [
                e.event_id,
                e.event_type.value,
                e.timestamp.isoformat(),
                e.agent_id,
                e.tool,
                e.method,
                e.result_code,
                e.denial_reason or "",
                str(e.latency_us),
            ]
            lines.append(",".join(row))
        
        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get aggregator statistics."""
        total = self._store.count()
        denials = len(self.query(event_type=AuditEventType.DENIAL, limit=10000))
        
        return {
            "total_events": total,
            "denial_count": denials,
            "approval_rate": (total - denials) / total if total > 0 else 1.0,
        }
