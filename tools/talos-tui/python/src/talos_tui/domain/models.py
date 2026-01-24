from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional

class ViewModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

class VersionInfo(ViewModel):
    service_version: str = Field(alias="version")
    git_sha: str
    contracts_version: str = "1.0.0"
    api_version: str = "1.0.0"

class Health(ViewModel):
    status: str = "error"
    detail: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"

class MetricsSummary(ViewModel):
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    connected_peers: int = 0
    active_sessions: int = 0

class Peer(ViewModel):
    peer_id: str
    services: List[str] = Field(default_factory=list)

class Session(ViewModel):
    session_id: str
    peer_id: Optional[str] = None
    created_at: Optional[str] = None

class AuditEvent(ViewModel):
    id: str
    ts: str
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class AuditPage(ViewModel):
    items: List[AuditEvent] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False
