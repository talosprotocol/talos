import sys
import os
import pytest

# Ensure app is importable for runtime
sys.path.append(os.path.join(os.path.dirname(__file__), "../services/ai-gateway"))

from app.domain.mcp.tool_guard import ToolGuard, GuardPolicy, ToolClass  # type: ignore

# Mock policies
SAFE_POLICY = GuardPolicy(
    tool_server="srv", tool_name="safe_tool", tool_class=ToolClass.READ, 
    requires_idempotency_key=False, read_replay_safe=True
)
UNSAFE_POLICY = GuardPolicy(
    tool_server="srv", tool_name="unsafe_tool", tool_class=ToolClass.READ, 
    requires_idempotency_key=False, read_replay_safe=False
)

@pytest.mark.asyncio
async def test_guard_enforces_safety_headers():
    """Verify ToolGuard policy propagates safety flags."""
    guard = ToolGuard("")
    guard._policies = {
        ("srv", "safe_tool"): SAFE_POLICY,
        ("srv", "unsafe_tool"): UNSAFE_POLICY
    }
    
    # Test Safe Tool
    policy = await guard.validate_call(
        "srv", "safe_tool", False, None, {}, None, {}, "req-1"
    )
    assert policy.read_replay_safe is True

    # Test Unsafe Tool
    policy = await guard.validate_call(
        "srv", "unsafe_tool", False, None, {}, None, {}, "req-2"
    )
    assert policy.read_replay_safe is False

# Note: Full integration test logic requiring FastAPI Request/Response context 
# would be placed in `tests/integration/test_gateway_safety.py`.
# This unit test confirms the Domain Logic is correct.
