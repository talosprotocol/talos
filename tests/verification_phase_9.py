"""Verification Phase 9: Hardening Tests."""

import asyncio
import json
import logging
import os
import sys
import tempfile
import unittest

# Import Guard early to avoid circular imports if needed, but per lint it
# should be top
# However, mcp_src needs to be in path first.
# We will do sys.path insertions first, then imports.

logging.basicConfig(level=logging.INFO)

cwd = os.getcwd()
mcp_src = os.path.join(cwd, "services/mcp-connector/src")
gateway_app = os.path.join(cwd, "services/ai-gateway")

sys.path.insert(0, mcp_src)
sys.path.insert(0, gateway_app)

# Use explicit imports after path modification
try:
    from talos_mcp.domain.tool_policy import (
        ToolClass,
        ToolPolicyEngine,
        ToolPolicyError,
    )
except ImportError:
    # Fallback for checking if we can import via different path or mock for
    # linting. This block is mainly to satisfy runtime import.
    class ToolPolicyEngine:
        def __init__(self, *_args, **_kwargs):
            """Initialize the mock engine."""

        def resolve_policy(self, *_args, **_kwargs):
            """Resolve a policy for a tool."""
            return None

        def validate_capability_match(self, *_args, **_kwargs):
            """Validate tool capabilities."""

        def validate_idempotency_key(self, *_args, **_kwargs):
            """Validate idempotency key requirements."""

        def verify_registry_completeness(self, *_args, **_kwargs):
            """Verify registry completeness (mock)."""
            return []

    class ToolPolicyError(Exception):
        """Mock Policy Error."""

        code = "UNKNOWN"

    class ToolClass:
        """Mock Tool Class."""

        READ = "read"
        WRITE = "write"


# pylint: disable=wrong-import-position
from domain.mcp.tool_guard import (  # noqa: E402,E501; pylint: disable=import-error; type: ignore
    GuardError,
    ToolGuard,
)


class TestPhase9Hardening(unittest.TestCase):
    """Test suite for Phase 9 hardening."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock registry
        self.registry_data = {
            "registry_version": "1.0",
            "tools": [
                {
                    "tool_server": "server-a",
                    "tool_name": "read-tool",
                    "tool_class": "read",
                    "requires_idempotency_key": False,
                },
                {
                    "tool_server": "server-a",
                    "tool_name": "write-tool",
                    "tool_class": "write",
                    "requires_idempotency_key": True,
                },
                {
                    "tool_server": "server-a",
                    "tool_name": "write-tool-no-idem",
                    "tool_class": "write",
                    "requires_idempotency_key": False,
                },
            ],
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        json.dump(self.registry_data, self.temp_file)
        self.temp_file.close()

        self.policy_engine = ToolPolicyEngine(self.temp_file.name, env="prod")
        self.guard = ToolGuard(self.temp_file.name)

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        os.remove(self.temp_file.name)

    def test_policy_engine_classification(self) -> None:
        """Test policy engine tool classification."""
        # Test unknown tool (Prod)
        with self.assertRaises(ToolPolicyError) as cm:
            self.policy_engine.resolve_policy("server-a", "unknown-tool")
        self.assertEqual(cm.exception.code, "TOOL_UNCLASSIFIED_DENIED")

        # Test known tool
        policy = self.policy_engine.resolve_policy("server-a", "read-tool")
        self.assertIsNotNone(policy)
        self.assertEqual(policy.tool_class, ToolClass.READ)

    def test_class_vs_capability(self) -> None:
        """Test tool class validation against capabilities."""
        write_policy = self.policy_engine.resolve_policy(
            "server-a", "write-tool"
        )
        read_policy = self.policy_engine.resolve_policy(
            "server-a", "read-tool"
        )
        self.assertIsNotNone(write_policy)
        self.assertIsNotNone(read_policy)

        # Capability: Read Only = True
        # Write Tool -> Should Fail
        self.assertIsNotNone(write_policy)
        with self.assertRaises(ToolPolicyError) as cm:
            self.policy_engine.validate_capability_match(
                write_policy, capability_read_only=True
            )
        self.assertEqual(cm.exception.code, "TOOL_CLASS_MISMATCH")

        # Read Tool -> Should Pass
        self.assertIsNotNone(read_policy)
        try:
            self.policy_engine.validate_capability_match(
                read_policy, capability_read_only=True
            )
        except ToolPolicyError:
            self.fail("Read tool should work with read-only capability")

    def test_idempotency_check_policy(self) -> None:
        """Test idempotency key policy enforcement."""
        policy = self.policy_engine.resolve_policy("server-a", "write-tool")
        self.assertIsNotNone(policy)

        self.assertIsNotNone(policy)
        # Missing Key -> Fail
        with self.assertRaises(ToolPolicyError) as cm:
            self.policy_engine.validate_idempotency_key(policy, None)
        self.assertEqual(cm.exception.code, "IDEMPOTENCY_KEY_REQUIRED")

        # Present Key -> Pass
        try:
            self.policy_engine.validate_idempotency_key(policy, "key-123")
        except ToolPolicyError:
            self.fail("Should pass with key")

    def test_registry_completeness(self) -> None:
        """Test registry completeness verification."""
        advertised = [
            {"server": "server-a", "tool": "read-tool"},
            {"server": "server-a", "tool": "unknown-tool"},
        ]
        missing = self.policy_engine.verify_registry_completeness(advertised)
        self.assertIn("server-a:unknown-tool", missing)
        self.assertNotIn("server-a:read-tool", missing)

    async def async_test_guard(self) -> None:
        """Test ToolGuard async validation."""
        # Test Guard which mimics Policy Engine logic but independent
        # implementation

        # 1. Unclassified
        with self.assertRaises(GuardError):
            await self.guard.validate_call(
                "server-a", "unknown", False, None, {}, None, {}, "req-1"
            )

        # 2. Write with Read-Only Cap
        with self.assertRaises(GuardError) as cm:
            await self.guard.validate_call(
                "server-a",
                "write-tool",
                True,
                "key",
                {},
                None,
                {},
                "req-1",
            )
        self.assertIn("CAPABILITY_MISMATCH", cm.exception.code)

        # 3. Idempotency Missing
        with self.assertRaises(GuardError) as cm:
            await self.guard.validate_call(
                "server-a", "write-tool", False, None, {}, None, {}, "req-1"
            )
        self.assertIn("IDEMPOTENCY_MISSING", cm.exception.code)

    def test_guard_async_wrapper(self) -> None:
        """Run async tests."""
        asyncio.run(self.async_test_guard())


if __name__ == "__main__":
    unittest.main()
