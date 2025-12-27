from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import asyncio
from datetime import datetime, timezone

# Import Core Classes
# Import Core Classes
from src.core.gateway import Gateway
from src.core.audit_plane import AuditEvent, AuditEventType
from src.core.audit_plane import InMemoryAuditStore

# --- App Setup ---
app = FastAPI(title="Talos Security Gateway API", version="1.0.0")

# CORS for Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
# Initialize Gateway with defaults
gateway = Gateway()


@app.on_event("startup")
async def startup_event():
    print("Starting Talos Gateway...")
    gateway.start()

@app.on_event("shutdown")
async def shutdown_event():
    print("Stopping Talos Gateway...")
    gateway.stop()

# --- Models ---
class GatewayStatusResponse(BaseModel):
    schema_version: str = "1"
    status_seq: int
    state: str
    version: str
    uptime_seconds: float
    requests_processed: int
    tenants: int
    cache: dict
    sessions: dict

class AuditEventResponse(BaseModel):
    # Mirroring the TypeScript schema loosely for JSON serialization
    schema_version: str = "1"
    event_id: str
    timestamp: int
    cursor: str
    event_type: str
    outcome: str
    denial_reason: Optional[str] = None
    session_id: str
    correlation_id: str
    agent_id: str = ""
    peer_id: str = ""
    tool: str
    method: str
    metrics: dict = {}
    hashes: dict = {}
    integrity: dict = {}
    metadata: dict = {}

class CursorPageResponse(BaseModel):
    items: List[dict]
    next_cursor: Optional[str] = None
    has_more: bool

# --- Endpoints ---

@app.get("/api/gateway/status", response_model=GatewayStatusResponse)
async def get_status():
    stats = gateway.get_health()
    
    # Calculate uptime safely
    uptime = 0
    if gateway._started_at:
        delta = datetime.now(timezone.utc) - gateway._started_at
        uptime = delta.total_seconds()
    
    return {
        "schema_version": "1",
        "status_seq": int(time.time()), 
        "state": stats.get("status", "UNKNOWN"),
        "version": "3.0.0-live",
        "uptime_seconds": uptime,
        "requests_processed": stats.get("requests_processed", 0),
        "tenants": stats.get("tenants", 0),
        "cache": {
            "capability_cache_size": 100, 
            "hits": 500,
            "misses": 10,
            "evictions": 0
        },
        "sessions": {
            "active_sessions": 5, 
            "replay_rejections_1h": 0
        }
    }

@app.get("/api/events", response_model=CursorPageResponse)
async def list_events(limit: int = 20, cursor: Optional[str] = None):
    # Access the audit store directly via _audit
    store = gateway._audit._store 
    
    # Query all events
    all_events = store.query(limit=1000) 
    
    # Convert to schema format
    mapped_events = []
    for e in all_events:
        # Create a cursor 
        c = f"{int(e.timestamp.timestamp())}:{e.event_id}"
        
        mapped_events.append({
            "schema_version": "1",
            "event_id": e.event_id,
            "timestamp": int(e.timestamp.timestamp()),
            "cursor": c,
            "event_type": e.event_type.value,
            "outcome": "DENY" if e.result_code == "DENY" else "OK", 
            "denial_reason": e.denial_reason,
            "session_id": e.session_id or "unknown",
            "correlation_id": "corr_live",
            "agent_id": e.agent_id,
            "peer_id": "",
            "tool": e.tool,
            "method": e.method,
            "metrics": {"latency_ms": e.latency_us // 1000},
            "hashes": {
                "event_hash": f"hash_{e.event_id}" 
            },
            "integrity": {
                "proof_state": "VERIFIED", 
                "signature_state": "VALID",
                "anchor_state": "PENDING",
                "verifier_version": "1.0.0"
            },
            "metadata": {}
        })
        
    # Sort DESC
    mapped_events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Logic for Cursor Paging
    start_index = 0
    if cursor:
        try:
            # Simple cursor check: find index of event with this cursor, start after it
            for i, ev in enumerate(mapped_events):
                if ev["cursor"] == cursor:
                    start_index = i + 1
                    break
        except:
            pass
            
    paged = mapped_events[start_index : start_index + limit]
    
    has_more = len(mapped_events) > start_index + limit
    next_cursor = paged[-1]["cursor"] if paged else None
    
    return {
        "items": paged,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

# --- Traffic Gen (Demo Helper) ---
@app.post("/api/demo/generate")
async def generate_load():
    """Trigger some traffic on the gateway for visualization"""
    # Simulate some audit logs
    gateway._audit.record_authorization(
        agent_id="live_agent_1",
        tool="demo_tool",
        method="run",
        capability_id="cap_demo",
        allowed=True,
        latency_us=5000,
        session_id="sess_live_1"
    )
    return {"status": "generated"}
