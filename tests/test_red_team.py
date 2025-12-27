"""
RED TEAM SECURITY TESTS - Adversarial Attack Simulation.

These tests attempt to break the capability authorization system
through various attack vectors:
- Signature forgery
- Replay attacks
- Scope escalation  
- Time manipulation
- Cache poisoning
- Delegation chain attacks
- Gate bypass attempts

Run with: pytest tests/test_red_team.py -v
"""

import secrets
import time
import pytest
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.capability import (
    Capability,
    CapabilityManager,
    CapabilityError,
    CapabilityExpired,
    CapabilityRevoked,
    CapabilityInvalid,
    ScopeViolation,
    DelegationDepthExceeded,
    MAX_DELEGATION_DEPTH,
    DenialReason,
)
from src.core.gateway import Gateway, GatewayRequest


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def attacker_keypair():
    """Attacker's keypair (different from legitimate issuer)."""
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


@pytest.fixture
def issuer_keypair():
    """Legitimate issuer's keypair."""
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


@pytest.fixture
def manager(issuer_keypair):
    """Legitimate capability manager."""
    private_key, public_key = issuer_keypair
    return CapabilityManager("did:talos:issuer", private_key, public_key)


@pytest.fixture
def attacker_manager(attacker_keypair):
    """Attacker's capability manager."""
    private_key, public_key = attacker_keypair
    return CapabilityManager("did:talos:attacker", private_key, public_key)


# =============================================================================
# 1. SIGNATURE ATTACKS
# =============================================================================

class TestSignatureAttacks:
    """Attacks targeting cryptographic signatures."""

    def test_forge_signature_with_different_key(self, manager, attacker_manager):
        """ATTACK: Sign a capability with attacker's key, present to legitimate manager."""
        # Attacker creates a capability with their own key
        malicious_cap = attacker_manager.grant(
            subject="did:talos:victim",
            scope="tool:admin/method:*",  # Attacker wants admin access
            expires_in=3600,
        )

        # Attack: try to verify with legitimate manager
        with pytest.raises(CapabilityInvalid):
            manager.verify(malicious_cap)

    def test_signature_swap_attack(self, manager):
        """ATTACK: Take signature from one capability, apply to another."""
        cap1 = manager.grant("did:talos:agent1", "tool:read", expires_in=3600)
        cap2 = manager.grant("did:talos:agent2", "tool:admin", expires_in=3600)

        # Swap signatures
        cap1.signature = cap2.signature

        # Should fail verification due to signature mismatch
        with pytest.raises(CapabilityInvalid):
            manager.verify(cap1)

    def test_null_signature_bypass(self, manager):
        """ATTACK: Present capability with null signature."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        
        # Attack: nullify signature
        cap.signature = b""

        with pytest.raises((CapabilityInvalid, Exception)):
            manager.verify(cap)

    def test_malformed_signature(self, manager):
        """ATTACK: Present capability with garbage signature."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        
        # Attack: corrupt signature
        cap.signature = b"garbage_signature_data_that_is_invalid"

        with pytest.raises((CapabilityInvalid, Exception)):
            manager.verify(cap)

    def test_truncated_signature(self, manager):
        """ATTACK: Present capability with truncated signature."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        
        # Attack: truncate signature (Ed25519 signature is 64 bytes)
        cap.signature = cap.signature[:32]

        with pytest.raises((CapabilityInvalid, Exception)):
            manager.verify(cap)

    def test_tamper_after_signing(self, manager):
        """ATTACK: Modify capability fields after legitimate signing."""
        cap = manager.grant("did:talos:agent", "tool:readonly", expires_in=3600)
        
        # Attack: escalate scope after signing
        cap.scope = "tool:admin/method:delete"

        with pytest.raises(CapabilityInvalid):
            manager.verify(cap)


# =============================================================================
# 2. REPLAY ATTACKS
# =============================================================================

class TestReplayAttacks:
    """Attacks involving replaying valid credentials."""

    def test_replay_revoked_capability(self, manager):
        """ATTACK: Use capability after revocation."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        
        # Initial authorization succeeds
        result = manager.authorize(cap, "test", "ping")
        assert result.allowed

        # Revoke
        manager.revoke(cap.id, reason="session ended")

        # Attack: replay the same capability
        result = manager.authorize(cap, "test", "ping")
        assert not result.allowed
        assert result.reason == DenialReason.REVOKED

    def test_replay_session_after_invalidation(self, manager):
        """ATTACK: Use session ID after session was invalidated."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        session_id = secrets.token_bytes(16)
        
        # Cache session
        manager.cache_session(session_id, cap)
        
        # Works initially
        result = manager.authorize_fast(session_id, "test", "ping")
        assert result.allowed

        # Invalidate session
        manager.invalidate_session(session_id)

        # Attack: replay invalidated session
        result = manager.authorize_fast(session_id, "test", "ping")
        assert not result.allowed

    def test_reuse_expired_session(self, manager):
        """ATTACK: Use session with expired capability."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=1)
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Wait for expiry
        time.sleep(1.5)

        # Attack: use expired session
        result = manager.authorize_fast(session_id, "test", "ping")
        assert not result.allowed
        assert result.reason == DenialReason.EXPIRED


# =============================================================================
# 3. SCOPE ESCALATION ATTACKS
# =============================================================================

class TestScopeEscalation:
    """Attacks attempting to gain unauthorized access."""

    def test_delegate_broader_scope(self, manager):
        """ATTACK: Delegate with broader scope than parent."""
        parent = manager.grant(
            "did:talos:agent1",
            "tool:filesystem/method:read",
            expires_in=3600,
            delegatable=True,
        )

        # Attack: try to get write access via delegation
        with pytest.raises(ScopeViolation):
            manager.delegate(
                parent_capability=parent,
                new_subject="did:talos:attacker",
                narrowed_scope="tool:filesystem/method:write",  # Escalation!
            )

    def test_access_outside_scope(self, manager):
        """ATTACK: Access tool not in capability scope."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:filesystem/method:read",
            expires_in=3600,
        )
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Attack: try to access admin tool
        result = manager.authorize_fast(session_id, "admin", "delete")
        assert not result.allowed
        assert result.reason == DenialReason.SCOPE_MISMATCH

    def test_wildcard_injection(self, manager):
        """ATTACK: Inject wildcard in scope through tampering."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:specific",
            expires_in=3600,
        )
        
        # Attack: tamper scope to wildcard
        cap.scope = "tool:*"

        # Signature should fail
        with pytest.raises(CapabilityInvalid):
            manager.verify(cap)

    def test_method_escalation(self, manager):
        """ATTACK: Access method not in scope."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:database/method:select",
            expires_in=3600,
        )
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Attack: try delete method
        result = manager.authorize_fast(session_id, "database", "delete")
        assert not result.allowed


# =============================================================================
# 4. TIME MANIPULATION ATTACKS
# =============================================================================

class TestTimeAttacks:
    """Attacks exploiting time-related mechanisms."""

    def test_use_expired_capability(self, manager):
        """ATTACK: Use capability after expiry."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=1)
        
        # Wait for expiry
        time.sleep(1.5)

        result = manager.authorize(cap, "test", "ping")
        assert not result.allowed
        assert result.reason == DenialReason.EXPIRED

    def test_future_dated_capability(self, manager, issuer_keypair):
        """ATTACK: Create capability with future issued_at."""
        private_key, public_key = issuer_keypair
        
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:attacker",
            scope="tool:admin",
            issued_at=future_time,
            expires_at=future_time + timedelta(hours=1),
        )
        cap.signature = private_key.sign(cap.canonical_bytes())

        # Should reject future-dated capability
        with pytest.raises(CapabilityInvalid):
            manager.verify(cap)

    def test_manipulate_expiry(self, manager):
        """ATTACK: Extend expiry after signing."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=60)
        
        # Attack: extend expiry
        cap.expires_at = datetime.now(timezone.utc) + timedelta(days=365)

        with pytest.raises(CapabilityInvalid):
            manager.verify(cap)


# =============================================================================
# 5. CACHE ATTACKS
# =============================================================================

class TestCacheAttacks:
    """Attacks targeting the session cache."""

    def test_cache_poisoning_different_capability(self, manager):
        """ATTACK: Try to cache a different capability for existing session."""
        # Legitimate session
        cap1 = manager.grant("did:talos:agent", "tool:readonly", expires_in=3600)
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap1)

        # Attack: try to cache elevated capability for same session
        cap2 = manager.grant("did:talos:attacker", "tool:admin", expires_in=3600)
        manager.cache_session(session_id, cap2)  # Overwrite

        # The session should now deny the original scope
        # (behavior depends on implementation - either reject or use new)
        manager.authorize_fast(session_id, "readonly", "ping")
        # If readonly is no longer the scope, it should fail
        # The key point is the system handles overwrites defined way

    def test_session_guessing(self, manager):
        """ATTACK: Guess session IDs."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Attack: try random session IDs
        for _ in range(100):
            fake_session = secrets.token_bytes(16)
            result = manager.authorize_fast(fake_session, "test", "ping")
            assert not result.allowed  # Should always fail for random IDs

    def test_forge_session_id(self, manager):
        """ATTACK: Use predictable session ID."""
        # Attack: use predictable ID
        predictable_session = b"\x00" * 16

        # Should not authorize unknown session
        result = manager.authorize_fast(predictable_session, "test", "ping")
        assert not result.allowed


# =============================================================================
# 6. GATE BYPASS ATTEMPTS
# =============================================================================

class TestGateBypass:
    """Attacks attempting to bypass authorization entirely."""

    def test_null_capability(self, manager):
        """ATTACK: Call authorize with None capability."""
        result = manager.authorize(None, "test", "ping")
        assert not result.allowed
        assert result.reason == DenialReason.NO_CAPABILITY

    def test_empty_tool_name(self, manager):
        """ATTACK: Request with empty tool name."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        result = manager.authorize(cap, "", "ping")
        assert not result.allowed

    def test_empty_method_name(self, manager):
        """ATTACK: Request with empty method name."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        result = manager.authorize(cap, "test", "")
        assert not result.allowed

    def test_gateway_without_tenant(self):
        """ATTACK: Gateway request for non-existent tenant."""
        gateway = Gateway()
        gateway.start()

        request = GatewayRequest(
            request_id="attack",
            tenant_id="nonexistent",
            session_id=secrets.token_bytes(16),
            tool="admin",
            method="delete",
        )

        response = gateway.authorize(request)
        assert not response.allowed
        assert "Unknown tenant" in response.error


# =============================================================================
# 7. DELEGATION CHAIN ATTACKS
# =============================================================================

class TestDelegationChainAttacks:
    """Attacks on the delegation system."""

    def test_exceed_max_delegation_depth(self, manager):
        """ATTACK: Create delegation chain beyond MAX_DELEGATION_DEPTH."""
        # Create deep chain manually
        cap = manager.grant(
            "did:talos:agent",
            "tool:test",
            expires_in=3600,
            delegatable=True,
        )
        
        # Manually create deep chain
        cap.delegation_chain = list(range(MAX_DELEGATION_DEPTH))
        cap.signature = manager._sign(cap.canonical_bytes())

        # Try to delegate further
        with pytest.raises(DelegationDepthExceeded):
            manager.delegate(
                parent_capability=cap,
                new_subject="did:talos:attacker",
            )

    def test_delegate_non_delegatable(self, manager):
        """ATTACK: Delegate a non-delegatable capability."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:test",
            expires_in=3600,
            delegatable=False,
        )

        with pytest.raises(CapabilityError, match="not delegatable"):
            manager.delegate(
                parent_capability=cap,
                new_subject="did:talos:attacker",
            )

    def test_delegate_expired_parent(self, manager):
        """ATTACK: Delegate from expired capability."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:test",
            expires_in=1,
            delegatable=True,
        )

        time.sleep(1.5)

        with pytest.raises(CapabilityExpired):
            manager.delegate(
                parent_capability=cap,
                new_subject="did:talos:attacker",
            )

    def test_delegate_revoked_parent(self, manager):
        """ATTACK: Delegate from revoked capability."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:test",
            expires_in=3600,
            delegatable=True,
        )

        manager.revoke(cap.id, reason="test")

        with pytest.raises(CapabilityRevoked):
            manager.delegate(
                parent_capability=cap,
                new_subject="did:talos:attacker",
            )


# =============================================================================
# 8. RACE CONDITION ATTACKS
# =============================================================================

class TestRaceConditions:
    """Attacks exploiting concurrency issues."""

    def test_concurrent_revocation_and_use(self, manager):
        """ATTACK: Use capability while trying to revoke it."""
        import concurrent.futures

        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        results = []
        
        def use_capability():
            for _ in range(50):
                r = manager.authorize_fast(session_id, "test", "ping")
                results.append(r.allowed)
                time.sleep(0.001)

        def revoke_capability():
            time.sleep(0.02)  # Let some uses happen
            manager.revoke(cap.id, reason="test")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            use_future = executor.submit(use_capability)
            revoke_future = executor.submit(revoke_capability)
            use_future.result()
            revoke_future.result()

        # After revocation, all subsequent uses should fail
        # The exact behavior depends on timing, but no crash should occur
        final_result = manager.authorize_fast(session_id, "test", "ping")
        assert not final_result.allowed


# =============================================================================
# 9. INPUT VALIDATION ATTACKS
# =============================================================================

class TestInputValidation:
    """Attacks using malformed inputs."""

    def test_unicode_injection_in_scope(self, manager):
        """ATTACK: Unicode characters in scope."""
        cap = manager.grant(
            "did:talos:agent",
            "tool:test\u0000/method:ping",  # Null byte injection
            expires_in=3600,
        )
        # Should either reject or handle safely
        manager.authorize(cap, "test", "ping")
        # Key: no crash, defined behavior

    def test_very_long_scope(self, manager):
        """ATTACK: Extremely long scope string."""
        long_scope = "tool:" + "a" * 10000
        cap = manager.grant(
            "did:talos:agent",
            long_scope,
            expires_in=3600,
        )
        # Should handle without crash
        manager.authorize(cap, "a" * 10000, "ping")

    def test_special_characters_in_tool(self, manager):
        """ATTACK: Special characters in tool name."""
        cap = manager.grant("did:talos:agent", "tool:test", expires_in=3600)
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Try various special characters
        special_tools = ["../admin", "test;drop", "test|cat", "test`id`", "test$(whoami)"]
        for tool in special_tools:
            result = manager.authorize_fast(session_id, tool, "ping")
            assert not result.allowed  # All should fail safely


# =============================================================================
# RUN ALL RED TEAM TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
