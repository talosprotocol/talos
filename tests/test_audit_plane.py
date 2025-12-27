"""
Tests for Audit Plane (Phase 3).
"""

from datetime import datetime, timezone

from src.core.audit_plane import (
    AuditEvent,
    AuditEventType,
    AuditAggregator,
    InMemoryAuditStore,
)


class TestAuditEvent:
    """Tests for AuditEvent dataclass."""

    def test_to_dict_roundtrip(self):
        """Test serialization and deserialization."""
        event = AuditEvent(
            event_id="aud_123",
            event_type=AuditEventType.AUTHORIZATION,
            timestamp=datetime.now(timezone.utc),
            agent_id="did:talos:agent",
            tool="filesystem",
            method="read",
            capability_id="cap_123",
            capability_hash="abc123",
            request_hash="def456",
            response_hash=None,
            result_code="ALLOWED",
            latency_us=42,
        )

        data = event.to_dict()
        restored = AuditEvent.from_dict(data)

        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type
        assert restored.agent_id == event.agent_id
        assert restored.result_code == event.result_code

    def test_to_json(self):
        """Test JSON serialization."""
        event = AuditEvent(
            event_id="aud_123",
            event_type=AuditEventType.DENIAL,
            timestamp=datetime.now(timezone.utc),
            agent_id="did:talos:agent",
            tool="admin",
            method="delete",
            capability_id=None,
            capability_hash=None,
            request_hash=None,
            response_hash=None,
            result_code="DENIED",
            denial_reason="NO_CAPABILITY",
        )

        json_str = event.to_json()
        assert "DENIED" in json_str
        assert "NO_CAPABILITY" in json_str


class TestInMemoryAuditStore:
    """Tests for in-memory audit store."""

    def test_append_and_query(self):
        """Test basic append and query."""
        store = InMemoryAuditStore()
        
        event = AuditEvent(
            event_id="aud_123",
            event_type=AuditEventType.AUTHORIZATION,
            timestamp=datetime.now(timezone.utc),
            agent_id="did:talos:agent1",
            tool="test",
            method="ping",
            capability_id="cap_1",
            capability_hash=None,
            request_hash=None,
            response_hash=None,
            result_code="ALLOWED",
        )
        
        store.append(event)
        
        results = store.query()
        assert len(results) == 1
        assert results[0].event_id == "aud_123"

    def test_query_by_agent(self):
        """Test filtering by agent_id."""
        store = InMemoryAuditStore()
        
        for i in range(5):
            store.append(AuditEvent(
                event_id=f"aud_{i}",
                event_type=AuditEventType.AUTHORIZATION,
                timestamp=datetime.now(timezone.utc),
                agent_id=f"agent{i % 2}",  # agent0 or agent1
                tool="test",
                method="ping",
                capability_id=None,
                capability_hash=None,
                request_hash=None,
                response_hash=None,
                result_code="ALLOWED",
            ))
        
        results = store.query(agent_id="agent0")
        assert len(results) == 3

    def test_max_events_limit(self):
        """Test that store respects max_events."""
        store = InMemoryAuditStore(max_events=10)
        
        for i in range(20):
            store.append(AuditEvent(
                event_id=f"aud_{i}",
                event_type=AuditEventType.AUTHORIZATION,
                timestamp=datetime.now(timezone.utc),
                agent_id="agent",
                tool="test",
                method="ping",
                capability_id=None,
                capability_hash=None,
                request_hash=None,
                response_hash=None,
                result_code="ALLOWED",
            ))
        
        assert store.count() == 10


class TestAuditAggregator:
    """Tests for AuditAggregator."""

    def test_record_authorization(self):
        """Test recording an authorization event."""
        agg = AuditAggregator()
        
        event = agg.record_authorization(
            agent_id="did:talos:agent",
            tool="filesystem",
            method="read",
            capability_id="cap_123",
            allowed=True,
            latency_us=42,
        )
        
        assert event.event_type == AuditEventType.AUTHORIZATION
        assert event.result_code == "ALLOWED"
        assert event.latency_us == 42

    def test_record_denial(self):
        """Test recording a denial event."""
        agg = AuditAggregator()
        
        event = agg.record_authorization(
            agent_id="did:talos:agent",
            tool="admin",
            method="delete",
            capability_id=None,
            allowed=False,
            denial_reason="SCOPE_MISMATCH",
        )
        
        assert event.event_type == AuditEventType.DENIAL
        assert event.result_code == "DENIED"
        assert event.denial_reason == "SCOPE_MISMATCH"

    def test_record_revocation(self):
        """Test recording a revocation event."""
        agg = AuditAggregator()
        
        event = agg.record_revocation(
            agent_id="did:talos:issuer",
            capability_id="cap_123",
            reason="session ended",
        )
        
        assert event.event_type == AuditEventType.REVOCATION
        assert event.result_code == "REVOKED"

    def test_export_json(self):
        """Test JSON export."""
        agg = AuditAggregator()
        
        agg.record_authorization("agent1", "tool1", "method1", "cap1", True)
        agg.record_authorization("agent2", "tool2", "method2", None, False, "EXPIRED")
        
        json_export = agg.export_json()
        
        assert "agent1" in json_export
        assert "agent2" in json_export
        assert "EXPIRED" in json_export

    def test_export_csv(self):
        """Test CSV export."""
        agg = AuditAggregator()
        
        agg.record_authorization("agent1", "tool1", "method1", "cap1", True)
        agg.record_authorization("agent2", "tool2", "method2", None, False)
        
        csv_export = agg.export_csv()
        
        lines = csv_export.strip().split("\n")
        assert len(lines) == 3  # Header + 2 events
        assert "event_id" in lines[0]  # Header
        assert "agent1" in lines[1]

    def test_get_stats(self):
        """Test statistics."""
        agg = AuditAggregator()
        
        # 3 allowed, 1 denied
        agg.record_authorization("agent", "tool", "method", "cap", True)
        agg.record_authorization("agent", "tool", "method", "cap", True)
        agg.record_authorization("agent", "tool", "method", "cap", True)
        agg.record_authorization("agent", "tool", "method", None, False)
        
        stats = agg.get_stats()
        
        assert stats["total_events"] == 4
        assert stats["denial_count"] == 1
        assert stats["approval_rate"] == 0.75
