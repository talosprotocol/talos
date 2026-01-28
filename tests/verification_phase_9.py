import unittest
import json
import tempfile
import asyncio
from typing import Dict, Any, List
from pathlib import Path

# Adjust path to find modules
import sys
import os
import logging
logging.basicConfig(level=logging.INFO)

cwd = os.getcwd()
mcp_src = os.path.join(cwd, "services/mcp-connector/src")
gateway_app = os.path.join(cwd, "services/ai-gateway")

sys.path.insert(0, mcp_src)
sys.path.insert(0, gateway_app)

print(f"DEBUG: sys.path[0:2] = {sys.path[:2]}")
print(f"DEBUG: mcp_src exists: {os.path.exists(mcp_src)}")
if os.path.exists(mcp_src):
    print(f"DEBUG: contents of mcp_src/talos_mcp: {os.listdir(os.path.join(mcp_src, 'talos_mcp'))}")
    if os.path.exists(os.path.join(mcp_src, 'talos_mcp/domain')):
         print(f"DEBUG: contents of mcp_src/talos_mcp/domain: {os.listdir(os.path.join(mcp_src, 'talos_mcp/domain'))}")

try:
    from talos_mcp.domain.tool_policy import ToolPolicyEngine, ToolPolicyError, ToolClass
    print("SUCCESS: Imported ToolPolicyEngine")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    # Try importing parent
    try:
        import talos_mcp
        print(f"INFO: talos_mcp imported from {talos_mcp.__file__}")
        import talos_mcp.domain
        print(f"INFO: talos_mcp.domain imported from {talos_mcp.domain.__file__}")
    except ImportError as e2:
        print(f"ERROR: Debug import failed: {e2}")
    raise

from app.domain.mcp.tool_guard import ToolGuard, GuardError

class TestPhase9Hardening(unittest.TestCase):
    
    def setUp(self):
        # Create a mock registry
        self.registry_data = {
            "registry_version": "1.0",
            "tools": [
                {
                    "tool_server": "server-a",
                    "tool_name": "read-tool",
                    "tool_class": "read",
                    "requires_idempotency_key": False
                },
                {
                    "tool_server": "server-a",
                    "tool_name": "write-tool",
                    "tool_class": "write",
                    "requires_idempotency_key": True
                },
                 {
                    "tool_server": "server-a",
                    "tool_name": "write-tool-no-idem",
                    "tool_class": "write",
                    "requires_idempotency_key": False
                }
            ]
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        json.dump(self.registry_data, self.temp_file)
        self.temp_file.close()
        
        self.policy_engine = ToolPolicyEngine(self.temp_file.name, env="prod")
        self.guard = ToolGuard(self.temp_file.name)

    def tearDown(self):
        os.remove(self.temp_file.name)

    def test_policy_engine_classification(self):
        # Test unknown tool (Prod)
        with self.assertRaises(ToolPolicyError) as cm:
            self.policy_engine.resolve_policy("server-a", "unknown-tool")
        self.assertEqual(cm.exception.code, "TOOL_UNCLASSIFIED_DENIED")
        
        # Test known tool
        policy = self.policy_engine.resolve_policy("server-a", "read-tool")
        self.assertEqual(policy.tool_class, ToolClass.READ)

    def test_class_vs_capability(self):
        write_policy = self.policy_engine.resolve_policy("server-a", "write-tool")
        read_policy = self.policy_engine.resolve_policy("server-a", "read-tool")
        
        # Capability: Read Only = True
        # Write Tool -> Should Fail
        with self.assertRaises(ToolPolicyError) as cm:
            self.policy_engine.validate_capability_match(write_policy, capability_read_only=True)
        self.assertEqual(cm.exception.code, "TOOL_CLASS_MISMATCH")
        
        # Read Tool -> Should Pass
        try:
            self.policy_engine.validate_capability_match(read_policy, capability_read_only=True)
        except ToolPolicyError:
            self.fail("Read tool should work with read-only capability")

    def test_idempotency_check_policy(self):
        policy = self.policy_engine.resolve_policy("server-a", "write-tool")
        
        # Missing Key -> Fail
        with self.assertRaises(ToolPolicyError) as cm:
            self.policy_engine.validate_idempotency_key(policy, None)
        self.assertEqual(cm.exception.code, "IDEMPOTENCY_KEY_REQUIRED")
        
        # Present Key -> Pass
        try:
            self.policy_engine.validate_idempotency_key(policy, "key-123")
        except ToolPolicyError:
            self.fail("Should pass with key")

    def test_registry_completeness(self):
        advertised = [
            {"server": "server-a", "tool": "read-tool"},
            {"server": "server-a", "tool": "unknown-tool"}
        ]
        missing = self.policy_engine.verify_registry_completeness(advertised)
        self.assertIn("server-a:unknown-tool", missing)
        self.assertNotIn("server-a:read-tool", missing)

    async def async_test_guard(self):
        # Test Guard which mimics Policy Engine logic but independent implementation
        
        # 1. Unclassified
        with self.assertRaises(GuardError):
            await self.guard.validate_call("server-a", "unknown", False, None, None, {}, "req-1")
            
        # 2. Write with Read-Only Cap
        with self.assertRaises(GuardError) as cm:
            await self.guard.validate_call("server-a", "write-tool", True, "key", None, {}, "req-1")
        self.assertIn("CAPABILITY_MISMATCH", cm.exception.code)
        
        # 3. Idempotency Missing
        with self.assertRaises(GuardError) as cm:
            await self.guard.validate_call("server-a", "write-tool", False, None, None, {}, "req-1")
        self.assertIn("IDEMPOTENCY_MISSING", cm.exception.code)

    def test_guard_async_wrapper(self):
        asyncio.run(self.async_test_guard())

if __name__ == '__main__':
    unittest.main()
