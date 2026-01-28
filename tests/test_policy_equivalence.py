
import unittest
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

# Add sources to path
root = Path.cwd()
sys.path.insert(0, str(root / "services/ai-gateway"))
sys.path.insert(0, str(root / "services/mcp-connector/src"))

from app.domain.mcp.tool_guard import ToolGuard, GuardPolicy, ToolClass as GatewayToolClass
from talos_mcp.domain.tool_policy import ToolPolicyEngine, ToolPolicy, ToolClass as ConnectorToolClass, ToolPolicyError

class TestPolicyEquivalence(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Initialize ToolGuard (Gateway)
        self.guard = ToolGuard("")
        self.guard._policies = {
            ("srv", "read_tool"): GuardPolicy(
                tool_server="srv", tool_name="read_tool", 
                tool_class=GatewayToolClass.READ, 
                requires_idempotency_key=False,
                read_replay_safe=True
            ),
            ("srv", "write_tool"): GuardPolicy(
                tool_server="srv", tool_name="write_tool", 
                tool_class=GatewayToolClass.WRITE, 
                requires_idempotency_key=True,
                read_replay_safe=False
            )
        }
        
        # Initialize ToolPolicyEngine (Connector) - Set to Prod to trigger denials for unclassified
        self.policy_engine = ToolPolicyEngine(env="prod")
        self.policy_engine.registry = {
            ("srv", "read_tool"): ToolPolicy(
                tool_name="read_tool",
                tool_class=ConnectorToolClass.READ,
                is_document_op=False,
                requires_idempotency_key=False,
                read_replay_safe=True,
                document_spec=None
            ),
            ("srv", "write_tool"): ToolPolicy(
                tool_name="write_tool",
                tool_class=ConnectorToolClass.WRITE,
                is_document_op=False,
                requires_idempotency_key=True,
                read_replay_safe=False,
                document_spec=None
            )
        }

    def connector_validate(self, server_id: str, tool_name: str, read_only: bool, idempotency_key: str = None):
        """Helper to simulate full connector validation flow."""
        policy = self.policy_engine.resolve_policy(server_id, tool_name)
        if not policy:
            raise ToolPolicyError("Unclassified", "UNCLASSIFIED")
        
        self.policy_engine.validate_capability_match(policy, read_only)
        self.policy_engine.validate_idempotency_key(policy, idempotency_key)
        return policy

    async def test_read_tool_equivalence(self):
        # Gateway
        g_policy = await self.guard.validate_call("srv", "read_tool", True, None, {}, None, {}, "req-1")
        # Connector
        c_policy = self.connector_validate("srv", "read_tool", True)
        
        self.assertEqual(g_policy.tool_class.value, c_policy.tool_class.value)
        self.assertTrue(g_policy.read_replay_safe)

    async def test_write_tool_denial_on_readonly_capability(self):
        # Capability: Read-Only, Tool: Write -> DENY
        
        # Gateway
        from app.domain.mcp.tool_guard import GuardError
        with self.assertRaises(GuardError) as gm:
             await self.guard.validate_call("srv", "write_tool", True, None, {}, None, {}, "req-2")
        self.assertEqual(gm.exception.code, "CAPABILITY_MISMATCH")
            
        # Connector
        with self.assertRaises(ToolPolicyError) as cm:
            self.connector_validate("srv", "write_tool", True)
        self.assertEqual(cm.exception.code, "TOOL_CLASS_MISMATCH")

    async def test_write_tool_idempotency_requirement_equivalence(self):
        # Idempotency Missing -> DENY
        
        # Gateway
        from app.domain.mcp.tool_guard import GuardError
        with self.assertRaises(GuardError) as gm:
            await self.guard.validate_call("srv", "write_tool", False, None, {}, None, {}, "req-3")
        self.assertEqual(gm.exception.code, "IDEMPOTENCY_MISSING")
            
        # Connector
        with self.assertRaises(ToolPolicyError) as cm:
            self.connector_validate("srv", "write_tool", False, None)
        self.assertEqual(cm.exception.code, "IDEMPOTENCY_KEY_REQUIRED")

    async def test_unclassified_denial_equivalence(self):
        # Server: Unknown -> DENY
        
        # Gateway
        from app.domain.mcp.tool_guard import GuardError
        with self.assertRaises(GuardError) as gm:
            await self.guard.validate_call("srv", "unknown_tool", False, "key", {}, None, {}, "req-4")
        self.assertEqual(gm.exception.code, "UNCLASSIFIED")
            
        # Connector
        with self.assertRaises(ToolPolicyError) as cm:
            self.connector_validate("srv", "unknown_tool", False, "key")
        # ToolPolicyEngine raises TOOL_UNCLASSIFIED_DENIED in prod
        self.assertEqual(cm.exception.code, "TOOL_UNCLASSIFIED_DENIED")

if __name__ == "__main__":
    unittest.main()
