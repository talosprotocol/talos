from __future__ import annotations
import asyncio
import random
from typing import Sequence, Optional, Dict, Any, List
from datetime import datetime, timezone

from talos_tui.domain.models import Health, MetricsSummary, Peer, Session, VersionInfo, AuditPage, AuditEvent

class MockGatewayAdapter:
    async def get_version(self) -> VersionInfo:
        return VersionInfo(
            service_version="1.2.3-mock",
            git_sha="deadbeef",
            contracts_version="1.0.0",
            api_version="v1"
        )

    async def get_health(self) -> Health:
        return Health(ok=True, detail="Running in Mock Mode")

    async def get_metrics_summary(self) -> MetricsSummary:
        return MetricsSummary(
            latency_p50_ms=random.uniform(5.0, 50.0),
            latency_p95_ms=random.uniform(50.0, 150.0),
            connected_peers=random.randint(10, 50),
            active_sessions=random.randint(1, 10)
        )

    async def list_peers(self) -> Sequence[Peer]:
        return [Peer(peer_id=f"peer-{i}", services=["gateway"]) for i in range(5)]

    async def list_sessions(self) -> Sequence[Session]:
        return [Session(session_id=f"sess-{i}") for i in range(3)]

class MockAuditAdapter:
    async def get_version(self) -> VersionInfo:
        return VersionInfo(
            service_version="1.2.3-mock",
            git_sha="deadbeef",
            contracts_version="1.0.0",
            api_version="v1"
        )

    async def list_events(self, limit: int, before: Optional[str]) -> AuditPage:
        # Generate random events
        items = []
        count = random.randint(0, 5)
        for i in range(count):
            items.append(AuditEvent(
                id=f"evt-{random.randint(1000, 9999)}",
                ts=datetime.now(timezone.utc).isoformat(),
                event_type=random.choice(["login", "logout", "config_change", "key_rotation"]),
                payload={"mock": True, "value": random.randint(1, 100)}
            ))
        
        return AuditPage(
            items=items,
            next_cursor="mock_cursor",
            has_more=True
        )
