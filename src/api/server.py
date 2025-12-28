from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time
import base64
from datetime import datetime, timezone

# Import Core Classes
from src.core.gateway import Gateway
from src.core.audit_plane import AuditAggregator
from src.core.blockchain import Blockchain
from src.core.audit_blockchain_adapter import BlockchainAuditStore
from pathlib import Path
import os

# --- App Setup ---
app = FastAPI(title="Talos Security Gateway API", version="3.1.0")

# CORS for Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
# Initialize Gateway with persistent blockchain
try:
    # Use standard shared path
    DATA_DIR = Path.home() / ".talos"
    BLOCKCHAIN_PATH = DATA_DIR / "blockchain.json"
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if BLOCKCHAIN_PATH.exists():
        print(f"Loading blockchain from {BLOCKCHAIN_PATH}...")
        blockchain = Blockchain.load(BLOCKCHAIN_PATH)
        # Verify and set params
        blockchain.persistence_path = str(BLOCKCHAIN_PATH)
        blockchain.auto_save = True
    else:
        print(f"Initializing new blockchain at {BLOCKCHAIN_PATH}...")
        blockchain = Blockchain(persistence_path=str(BLOCKCHAIN_PATH), auto_save=True)
        # Force save genesis
        blockchain.save(BLOCKCHAIN_PATH)
        
    audit_store = BlockchainAuditStore(blockchain)
    audit_aggregator = AuditAggregator(store=audit_store)
    gateway = Gateway(audit_aggregator=audit_aggregator)
    
except Exception as e:
    print(f"CRITICAL: Failed to initialize persistent storage: {e}")
    print("Falling back to ephemeral...")
    gateway = Gateway()

@app.on_event("startup")
async def startup_event():
    print("Starting Talos Gateway...")
    gateway.start()

@app.on_event("shutdown")
async def shutdown_event():
    print("Stopping Talos Gateway...")
    gateway.stop()

# --- v3.1 Models ---

class GatewayStatusResponse(BaseModel):
    schema_version: str = "1"
    status_seq: int  # Monotonic sequence
    state: str
    version: str
    uptime_seconds: float
    requests_processed: int
    tenants: int
    cache: Dict[str, int]
    sessions: Dict[str, int]

class IntegrityBlock(BaseModel):
    proof_state: str = "VERIFIED" # 'VERIFIED' | 'UNVERIFIED' | 'FAILED' | 'MISSING_INPUTS'
    signature_state: str = "VALID" # 'VALID' | 'INVALID' | 'NOT_PRESENT'
    anchor_state: str = "PENDING" # 'NOT_ENABLED' | 'PENDING' | 'ANCHORED' | 'ANCHOR_FAILED'
    verifier_version: str = "1.0.0"
    failure_reason: Optional[str] = None # 'MISSING_INPUTS' | 'MISSING_EVENT_HASH' | ...

class AuditEventHashBlock(BaseModel):
    capability_hash: Optional[str] = None
    request_hash: Optional[str] = None
    response_hash: Optional[str] = None
    event_hash: Optional[str] = None # Required for Proof

class AuditEventResponse(BaseModel):
    # Strict v3.1 Schema
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
    metrics: Dict[str, Any] = {}
    hashes: AuditEventHashBlock
    integrity: IntegrityBlock
    metadata: Dict[str, Any] = {} 

class CursorPageResponse(BaseModel):
    items: List[AuditEventResponse]
    next_cursor: Optional[str] = None
    has_more: bool

# --- Helpers ---

def encode_cursor(timestamp: int, event_id: str) -> str:
    # v3.1 Spec: Opaque Base64URL string (decodes to Timestamp:EventID)
    raw = f"{timestamp}:{event_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")

def decode_cursor(cursor: str) -> Optional[tuple[int, str]]:
    try:
        raw = base64.urlsafe_b64decode(cursor).decode("utf-8")
        parts = raw.split(":", 1)
        return int(parts[0]), parts[1]
    except Exception: # Fix bare except
        return None

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
        "status_seq": int(time.time()), # Monotonic enough for this demo
        "state": stats.get("status", "UNKNOWN"),
        "version": "3.1.0-live",
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
    
    # Query all events (in production this would be SQL with LIMIT)
    all_events = store.query(limit=1000) 
    
    mapped_events = []
    
    # Convert to v3.1 schema format
    for e in all_events:
        ts = int(e.timestamp.timestamp())
        c = encode_cursor(ts, e.event_id)
        
        # v3.1 Proof Simulation
        integrity = {
            "proof_state": "VERIFIED",
            "signature_state": "VALID",
            "anchor_state": "PENDING",
            "verifier_version": "1.0.0"
        }
        
        # In a real system, we'd verify the signature here
        # For demo, if it's a 'DENY', let's say it was validly signed but denied by policy
        
        mapped_events.append({
            "schema_version": "1",
            "event_id": e.event_id,
            "timestamp": ts,
            "cursor": c,
            "event_type": e.event_type.value,
            "outcome": "DENY" if e.result_code == "DENIED" else "OK", 
            "denial_reason": e.denial_reason, # Required if DENY, else None
            "session_id": e.session_id or "synthesized_sess_0",
            "correlation_id": "corr_live_" + e.event_id[:8],
            "agent_id": e.agent_id,
            "peer_id": "",
            "tool": e.tool,
            "method": e.method,
            "metrics": {"latency_ms": e.latency_us // 1000},
            "hashes": {
                "event_hash": f"sha256:{e.event_id}", # Simulated hash
                "request_hash": "sha256:...", 
            },
            "integrity": integrity,
            "metadata": {} # Redacted by default v3.1 policy
        })
        
    # Sort DESC (Newest First) as per v3.1
    mapped_events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Cursor Paging Logic
    start_index = 0
    if cursor:
        decoded = decode_cursor(cursor)
        if decoded:
            target_ts, target_id = decoded
            # Find the event with this cursor
            for i, ev in enumerate(mapped_events):
                if ev["timestamp"] == target_ts and ev["event_id"] == target_id:
                    start_index = i + 1
                    break
    
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
    import random
    
    # 90% success, 10% denial (matching spec's denial taxonomy)
    denial_reasons = [
        "NO_CAPABILITY", "EXPIRED", "REVOKED", "SCOPE_MISMATCH",
        "DELEGATION_INVALID", "UNKNOWN_TOOL", "REPLAY", 
        "SIGNATURE_INVALID", "INVALID_FRAME"
    ]
    
    tools = ["filesystem", "database", "network", "shell", "api"]
    methods = ["read", "write", "execute", "delete", "list"]
    
    allowed = random.random() > 0.10  # 90% success rate
    denial_reason = None if allowed else random.choice(denial_reasons)
    
    gateway._audit.record_authorization(
        agent_id=f"agent_{random.randint(1, 5)}",
        tool=random.choice(tools),
        method=random.choice(methods),
        capability_id=f"cap_{random.randint(1, 100)}",
        allowed=allowed,
        denial_reason=denial_reason,
        latency_us=random.randint(1000, 50000),
        session_id=f"sess_{random.randint(1, 10)}"
    )
    return {"status": "generated", "allowed": allowed, "denial_reason": denial_reason}

