"""
Tests for Capability Store.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Skip if lmdb not available
pytest.importorskip("lmdb")

from src.core.capability import CapabilityManager
from src.core.capability_store import CapabilityStore, RevocationEntry


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def store(temp_dir):
    """Create capability store."""
    return CapabilityStore(temp_dir)


@pytest.fixture
def manager():
    """Create capability manager."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return CapabilityManager(
        issuer_id="did:talos:issuer",
        private_key=private_key,
        public_key=public_key,
    )


class TestCapabilityStore:
    """Tests for CapabilityStore."""

    def test_save_and_get(self, store, manager):
        """Test basic save and retrieve."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        store.save(cap)
        retrieved = store.get(cap.id)

        assert retrieved is not None
        assert retrieved.id == cap.id
        assert retrieved.subject == cap.subject
        assert retrieved.scope == cap.scope

    def test_get_nonexistent(self, store):
        """Test getting nonexistent capability."""
        result = store.get("cap_nonexistent")
        assert result is None

    def test_delete(self, store, manager):
        """Test capability deletion."""
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tools/read",
            expires_in=3600,
        )

        store.save(cap)
        assert store.get(cap.id) is not None

        result = store.delete(cap.id)
        assert result is True
        assert store.get(cap.id) is None

    def test_delete_nonexistent(self, store):
        """Test deleting nonexistent capability."""
        result = store.delete("cap_nonexistent")
        assert result is False

    def test_revocation_save_and_get(self, store):
        """Test revocation entry storage."""
        entry = RevocationEntry(
            capability_id="cap_test123",
            revoked_at=datetime.now(timezone.utc),
            reason="security concern",
            revoked_by="did:talos:admin",
        )

        store.save_revocation(entry)
        retrieved = store.get_revocation("cap_test123")

        assert retrieved is not None
        assert retrieved.capability_id == "cap_test123"
        assert retrieved.reason == "security concern"

    def test_is_revoked(self, store):
        """Test revocation check."""
        assert store.is_revoked("cap_test") is False

        entry = RevocationEntry(
            capability_id="cap_test",
            revoked_at=datetime.now(timezone.utc),
            reason="test",
            revoked_by="did:talos:admin",
        )
        store.save_revocation(entry)

        assert store.is_revoked("cap_test") is True

    def test_list_by_subject(self, store, manager):
        """Test listing capabilities by subject."""
        cap1 = manager.grant(subject="did:talos:agent1", scope="tools/a", expires_in=3600)
        cap2 = manager.grant(subject="did:talos:agent1", scope="tools/b", expires_in=3600)
        cap3 = manager.grant(subject="did:talos:agent2", scope="tools/c", expires_in=3600)

        store.save(cap1)
        store.save(cap2)
        store.save(cap3)

        agent1_caps = store.list_by_subject("did:talos:agent1")
        assert len(agent1_caps) == 2

        agent2_caps = store.list_by_subject("did:talos:agent2")
        assert len(agent2_caps) == 1

    def test_list_by_scope(self, store, manager):
        """Test listing capabilities by scope."""
        cap1 = manager.grant(subject="did:talos:a", scope="tools/read", expires_in=3600)
        cap2 = manager.grant(subject="did:talos:b", scope="tools/write", expires_in=3600)
        cap3 = manager.grant(subject="did:talos:c", scope="tools/read", expires_in=3600)

        store.save(cap1)
        store.save(cap2)
        store.save(cap3)

        # "tools" scope should match all
        tools_caps = store.list_by_scope("tools")
        assert len(tools_caps) == 3

        # Specific scope
        read_caps = store.list_by_scope("tools/read")
        assert len(read_caps) == 2

    def test_list_all(self, store, manager):
        """Test listing all capabilities."""
        cap1 = manager.grant(subject="did:talos:a", scope="tools/1", expires_in=3600)
        cap2 = manager.grant(subject="did:talos:b", scope="tools/2", expires_in=3600)

        store.save(cap1)
        store.save(cap2)

        all_caps = list(store.list_all())
        assert len(all_caps) == 2

    def test_list_revocations(self, store):
        """Test listing all revocations."""
        entry1 = RevocationEntry(
            capability_id="cap_1",
            revoked_at=datetime.now(timezone.utc),
            reason="test1",
            revoked_by="did:talos:admin",
        )
        entry2 = RevocationEntry(
            capability_id="cap_2",
            revoked_at=datetime.now(timezone.utc),
            reason="test2",
            revoked_by="did:talos:admin",
        )

        store.save_revocation(entry1)
        store.save_revocation(entry2)

        all_revocations = list(store.list_revocations())
        assert len(all_revocations) == 2

    def test_context_manager(self, temp_dir):
        """Test context manager usage."""
        with CapabilityStore(temp_dir) as store:
            assert store is not None
        # Should not raise after close
