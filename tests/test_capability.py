"""
Tests for Capability Token System.
"""

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
)


@pytest.fixture
def keypair():
    """Generate test keypair."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def manager(keypair):
    """Create capability manager."""
    private_key, public_key = keypair
    return CapabilityManager(
        issuer_id="did:talos:issuer",
        private_key=private_key,
        public_key=public_key,
    )


class TestCapability:
    """Tests for Capability class."""

    def test_capability_creation(self):
        """Test basic capability creation."""
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/read",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert cap.id.startswith("cap_")
        assert cap.issuer == "did:talos:issuer"
        assert cap.subject == "did:talos:subject"
        assert cap.scope == "tools/read"
        assert cap.version == 1
        assert cap.delegatable is False

    def test_capability_is_expired(self):
        """Test expiry detection."""
        # Not expired
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/read",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert cap.is_expired() is False

        # Expired
        cap2 = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/read",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert cap2.is_expired() is True

    def test_scope_coverage_exact(self):
        """Test exact scope match."""
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/filesystem/read",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert cap.covers_scope("tools/filesystem/read") is True
        assert cap.covers_scope("tools/filesystem/write") is False

    def test_scope_coverage_hierarchical(self):
        """Test hierarchical scope matching."""
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/filesystem",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Broader scope covers more specific
        assert cap.covers_scope("tools/filesystem/read") is True
        assert cap.covers_scope("tools/filesystem/write") is True
        assert cap.covers_scope("tools/filesystem/nested/deep") is True

        # Cannot cover different branch
        assert cap.covers_scope("tools/database/read") is False

    def test_scope_coverage_no_broader(self):
        """Test that narrow scope doesn't cover broader."""
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/filesystem/read",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Narrow cannot cover broad
        assert cap.covers_scope("tools/filesystem") is False
        assert cap.covers_scope("tools") is False

    def test_constraint_check_paths(self):
        """Test path constraint checking."""
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/filesystem/read",
            constraints={"paths": ["/data/*", "/tmp/*"]},
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert cap.check_constraints({"path": "/data/file.txt"}) is True
        assert cap.check_constraints({"path": "/tmp/temp.log"}) is True
        assert cap.check_constraints({"path": "/etc/passwd"}) is False

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        cap = Capability(
            issuer="did:talos:issuer",
            subject="did:talos:subject",
            scope="tools/read",
            constraints={"rate_limit": "100/hour"},
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            delegatable=True,
            signature=b"test_signature",
        )

        data = cap.to_dict()
        restored = Capability.from_dict(data)

        assert restored.id == cap.id
        assert restored.issuer == cap.issuer
        assert restored.subject == cap.subject
        assert restored.scope == cap.scope
        assert restored.constraints == cap.constraints
        assert restored.delegatable == cap.delegatable
        assert restored.signature == cap.signature


class TestCapabilityManager:
    """Tests for CapabilityManager."""

    def test_grant_capability(self, manager):
        """Test granting a capability."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        assert cap.id.startswith("cap_")
        assert cap.issuer == "did:talos:issuer"
        assert cap.subject == "did:talos:agent"
        assert cap.scope == "tools/read"
        assert cap.signature is not None
        assert len(cap.signature) == 64  # Ed25519 signature size

    def test_grant_with_constraints(self, manager):
        """Test granting with constraints."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/filesystem/read",
            constraints={
                "paths": ["/data/*"],
                "rate_limit": "100/hour",
            },
            expires_in=3600,
        )

        assert cap.constraints["paths"] == ["/data/*"]
        assert cap.constraints["rate_limit"] == "100/hour"

    def test_verify_valid_capability(self, manager):
        """Test verifying a valid capability."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        assert manager.verify(cap) is True

    def test_verify_expired_capability(self, manager):
        """Test verifying expired capability raises."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=0,  # Expires immediately
        )

        # Wait a tiny bit to ensure expiry
        import time
        time.sleep(0.01)

        with pytest.raises(CapabilityExpired):
            manager.verify(cap)

    def test_verify_revoked_capability(self, manager):
        """Test verifying revoked capability raises."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        manager.revoke(cap.id, reason="security concern")

        with pytest.raises(CapabilityRevoked):
            manager.verify(cap)

    def test_verify_scope_coverage(self, manager):
        """Test scope verification."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/filesystem",
            expires_in=3600,
        )

        # Covered scope
        assert manager.verify(cap, requested_scope="tools/filesystem/read") is True

        # Not covered
        with pytest.raises(ScopeViolation):
            manager.verify(cap, requested_scope="tools/database/write")

    def test_verify_constraint_violation(self, manager):
        """Test constraint verification."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/filesystem/read",
            constraints={"paths": ["/data/*"]},
            expires_in=3600,
        )

        # Satisfies constraints
        assert manager.verify(cap, params={"path": "/data/file.txt"}) is True

        # Violates constraints
        with pytest.raises(ScopeViolation):
            manager.verify(cap, params={"path": "/etc/passwd"})

    def test_revoke_capability(self, manager):
        """Test capability revocation."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        assert manager.is_revoked(cap.id) is False

        manager.revoke(cap.id, "no longer needed")

        assert manager.is_revoked(cap.id) is True

    def test_delegate_capability(self, manager):
        """Test capability delegation."""
        parent = manager.grant(
            subject="did:talos:agent1",
            scope="tools/filesystem",
            expires_in=3600,
            delegatable=True,
        )

        child = manager.delegate(
            parent_capability=parent,
            new_subject="did:talos:agent2",
            narrowed_scope="tools/filesystem/read",
        )

        assert child.subject == "did:talos:agent2"
        assert child.scope == "tools/filesystem/read"
        assert child.delegation_chain == [parent.id]
        assert child.signature is not None

    def test_delegate_non_delegatable_fails(self, manager):
        """Test that non-delegatable capability cannot be delegated."""
        parent = manager.grant(
            subject="did:talos:agent1",
            scope="tools/read",
            expires_in=3600,
            delegatable=False,
        )

        with pytest.raises(CapabilityError):
            manager.delegate(
                parent_capability=parent,
                new_subject="did:talos:agent2",
            )

    def test_delegate_cannot_broaden_scope(self, manager):
        """Test that delegation cannot broaden scope."""
        parent = manager.grant(
            subject="did:talos:agent1",
            scope="tools/filesystem/read",
            expires_in=3600,
            delegatable=True,
        )

        with pytest.raises(ScopeViolation):
            manager.delegate(
                parent_capability=parent,
                new_subject="did:talos:agent2",
                narrowed_scope="tools/filesystem",  # Broader!
            )

    def test_delegate_expiry_capped(self, manager):
        """Test that delegated capability expiry is capped by parent."""
        parent = manager.grant(
            subject="did:talos:agent1",
            scope="tools/read",
            expires_in=60,  # 1 minute
            delegatable=True,
        )

        child = manager.delegate(
            parent_capability=parent,
            new_subject="did:talos:agent2",
            expires_in=3600,  # Request 1 hour
        )

        # Child should expire no later than parent
        assert child.expires_at <= parent.expires_at

    def test_list_issued(self, manager):
        """Test listing issued capabilities."""
        cap1 = manager.grant(subject="did:talos:a", scope="tools/1", expires_in=3600)
        cap2 = manager.grant(subject="did:talos:b", scope="tools/2", expires_in=3600)

        issued = manager.list_issued()
        assert len(issued) == 2
        assert cap1 in issued
        assert cap2 in issued

    def test_invalid_signature_fails(self, manager, keypair):
        """Test that tampered capability fails verification."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        # Tamper with scope
        cap.scope = "tools/admin"

        with pytest.raises(CapabilityInvalid):
            manager.verify(cap)


class TestAdversarialCapability:
    """Adversarial tests for security invariants per protocol spec."""

    @pytest.fixture
    def keypair(self):
        """Generate test keypair."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @pytest.fixture
    def manager(self, keypair):
        """Create capability manager."""
        private_key, public_key = keypair
        return CapabilityManager(
            issuer_id="did:talos:issuer",
            private_key=private_key,
            public_key=public_key,
        )

    def test_delegation_scope_widening_fails(self, manager):
        """
        Adversarial test: Attempt to delegate broader scope fails cryptographically.

        Per spec: Delegated capabilities may ONLY reduce scope, never expand it.
        """
        parent = manager.grant(
            subject="did:talos:agent1",
            scope="tool:filesystem/method:read",
            expires_in=3600,
            delegatable=True,
        )

        # Attempt to widen scope (should fail)
        with pytest.raises(ScopeViolation) as exc_info:
            manager.delegate(
                parent_capability=parent,
                new_subject="did:talos:attacker",
                narrowed_scope="tool:filesystem",  # Broader than parent!
            )

        assert "broader scope" in str(exc_info.value).lower()

    def test_signature_context_confusion_rejected(self, manager, keypair):
        """
        Adversarial test: Cross-protocol signature reuse rejected.

        A signature from one capability should not validate for another.
        """
        cap1 = manager.grant(
            subject="did:talos:agent",
            scope="tool:safe/method:read",
            expires_in=3600,
        )

        cap2 = manager.grant(
            subject="did:talos:agent",
            scope="tool:dangerous/method:write",
            expires_in=3600,
        )

        # Attempt to swap signatures (should fail verification)
        original_sig = cap1.signature
        cap1.signature = cap2.signature

        with pytest.raises(CapabilityInvalid):
            manager.verify(cap1)

        # Restore and verify original works
        cap1.signature = original_sig
        assert manager.verify(cap1) is True

    def test_capability_mid_session_expiry(self, manager):
        """
        Test behavior when capability expires during active session.

        Per spec: Sessions survive capability expiry, individual requests fail.
        """
        # Create capability that expires very soon
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tool:test/method:ping",
            expires_in=1,  # 1 second
        )

        # Verify works while valid
        assert manager.verify(cap, requested_scope="tool:test/method:ping") is True

        # Wait for expiry
        import time
        time.sleep(1.1)

        # Now verification should fail
        with pytest.raises(CapabilityExpired):
            manager.verify(cap, requested_scope="tool:test/method:ping")

    def test_revocation_overrides_validity(self, manager):
        """
        Test that revocation overrides validity even if TTL not expired.

        Per spec: Revocation overrides validity.
        """
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tool:test/method:ping",
            expires_in=3600,  # Valid for 1 hour
        )

        # Verify works before revocation
        assert manager.verify(cap) is True

        # Revoke the capability
        manager.revoke(cap.id, reason="compromised")

        # Now should fail even though TTL not expired
        with pytest.raises(CapabilityRevoked) as exc_info:
            manager.verify(cap)

        assert "revoked" in str(exc_info.value).lower()
        assert "compromised" in str(exc_info.value).lower()

    def test_tampered_delegation_chain_detected(self, manager):
        """
        Test that tampering with delegation chain is detected.

        Per spec: Delegation chain signatures must be verified.
        """
        parent = manager.grant(
            subject="did:talos:agent1",
            scope="tool:filesystem/method:read",
            expires_in=3600,
            delegatable=True,
        )

        child = manager.delegate(
            parent_capability=parent,
            new_subject="did:talos:agent2",
        )

        # Tamper with delegation chain
        child.delegation_chain = ["fake_parent_id"]

        # Verification should fail (signature mismatch)
        with pytest.raises(CapabilityInvalid):
            manager.verify(child)

