import pytest
import uuid
import os
from datetime import datetime, timezone
from tga.domain.models import ExecutionState, ArtifactType
from tga.tools.server import authorize, log, recover, store

@pytest.fixture(autouse=True)
def setup_teardown():
    # Use a fresh test database for each test
    db_path = "test_tga.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ["TGA_DB_PATH"] = db_path
    yield
    if os.path.exists(db_path):
        os.remove(db_path)

def test_authorize_cold_path():
    principal_id = str(uuid.uuid4())
    result = authorize.fn(
        principal_id=principal_id,
        tool_server="github",
        tool_name="create-issue",
        args={"title": "Test"},
        capability_token="valid-token"
    )
    assert "tool_call" in result
    assert result["tool_call"]["call"]["tool_name"] == "create-issue"
    assert result["tool_call"]["session_id"] is not None

def test_log_and_hash_chain():
    tid = str(uuid.uuid4())
    pid = str(uuid.uuid4())
    kid = str(uuid.uuid4())
    
    # 1. Log first entry
    res1 = log.fn(
        trace_id=tid,
        principal_id=pid,
        seq=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifact_type="tool_call",
        artifact_data={"secret": "password123"},
        idempotency_key=kid,
        prev_entry_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    assert "entry" in res1
    assert res1["entry"]["artifact_data"]["secret"] == "[REDACTED]"
    
    # 2. Log second entry with correct hash chain
    kid2 = str(uuid.uuid4())
    res2 = log.fn(
        trace_id=tid,
        principal_id=pid,
        seq=2,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifact_type="tool_effect",
        artifact_data={"status": "ok"},
        idempotency_key=kid2,
        prev_entry_digest=res1["entry"]["entry_digest"]
    )
    assert "entry" in res2
    
    # 3. Verify chain
    rec = recover.fn(trace_id=tid)
    assert rec["chain_valid"] is True
    assert rec["entry_count"] == 2

def test_hash_chain_tamper_detection():
    tid = str(uuid.uuid4())
    pid = str(uuid.uuid4())
    
    # 1. Log entry
    res1 = log.fn(
        trace_id=tid,
        principal_id=pid,
        seq=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifact_type="tool_call",
        artifact_data={"data": "foo"},
        idempotency_key=str(uuid.uuid4()),
        prev_entry_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    
    # 2. Try to log next entry with WRONG prev_digest
    res2 = log.fn(
        trace_id=tid,
        principal_id=pid,
        seq=2,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifact_type="tool_effect",
        artifact_data={"data": "bar"},
        idempotency_key=str(uuid.uuid4()),
        prev_entry_digest="WRONG_DIGEST"
    )
    
    assert "error" in res2
    assert res2["error"]["code"] == "TGA_HASH_CHAIN_BROKEN"
