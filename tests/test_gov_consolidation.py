import pytest
import asyncio
from app.domain.tga.runtime import TgaRuntime, ExecutionPlan
from app.domain.tga.state_store import get_state_store
from talos_governance_agent.domain.models import ExecutionStateEnum

@pytest.mark.asyncio
async def test_gov_consolidation_runtime_bridge():
    """Verify that Gateway TGA Runtime correctly delegates to standalone library."""
    store = get_state_store()
    runtime = TgaRuntime(store=store)
    
    # Trace ID must be a valid UUIDv7 for strict validation in standalone
    trace_id = "018e9999-9999-7999-8999-999999999999"
    plan_id = "018e9999-9999-7999-8999-999999999998"
    
    plan = ExecutionPlan(
        trace_id=trace_id,
        plan_id=plan_id,
        tool_server="mcp-test",
        tool_name="test-tool",
        tool_args={"arg": 1},
        action_request={"implicit": True}
    )
    
    # Since we didn't provide capability_jws, it will skip the first step in our bridge
    # but still record the effect via standalone.record_tool_effect.
    # For this to work, we need to manually put the state into EXECUTING
    # to simulate a transition that happened elsewhere (or via authorize_tool_call).
    
    from talos_governance_agent.domain.models import ExecutionLogEntry, ArtifactType
    
    # Genesis
    entry1 = ExecutionLogEntry(
        trace_id=trace_id,
        principal_id=trace_id,
        sequence_number=1,
        prev_entry_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        entry_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ts="2026-01-01T00:00:00.000Z",
        from_state=ExecutionStateEnum.PENDING,
        to_state=ExecutionStateEnum.PENDING,
        artifact_type=ArtifactType.ACTION_REQUEST,
        artifact_id=plan_id,
        artifact_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    entry1.entry_digest = entry1.compute_digest()
    await store.append_log_entry(entry1)
    
    # Authorized
    entry2 = ExecutionLogEntry(
        trace_id=trace_id,
        principal_id=trace_id,
        sequence_number=2,
        prev_entry_digest=entry1.entry_digest,
        entry_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ts="2026-01-01T00:00:00.001Z",
        from_state=ExecutionStateEnum.PENDING,
        to_state=ExecutionStateEnum.AUTHORIZED,
        artifact_type=ArtifactType.SUPERVISOR_DECISION,
        artifact_id="dec-1",
        artifact_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    entry2.entry_digest = entry2.compute_digest()
    await store.append_log_entry(entry2)
    
    # Executing
    entry3 = ExecutionLogEntry(
        trace_id=trace_id,
        principal_id=trace_id,
        sequence_number=3,
        prev_entry_digest=entry2.entry_digest,
        entry_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ts="2026-01-01T00:00:00.002Z",
        from_state=ExecutionStateEnum.AUTHORIZED,
        to_state=ExecutionStateEnum.EXECUTING,
        artifact_type=ArtifactType.TOOL_CALL,
        artifact_id="tc-1",
        artifact_digest="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    entry3.entry_digest = entry3.compute_digest()
    await store.append_log_entry(entry3)
    
    # Now run execute_plan - it should transition to COMPLETED
    result = await runtime.execute_plan(plan)
    
    assert result.final_state == ExecutionStateEnum.COMPLETED
    assert result.trace_id == trace_id
    
    # Verify log in store has 4 entries
    entries = await store.list_log_entries(trace_id)
    assert len(entries) == 4
    assert entries[-1].artifact_type == ArtifactType.TOOL_EFFECT
