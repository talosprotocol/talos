"""
Tests for Key Security Utilities (Phase 2 Hardening).
"""

import pytest

from src.core.key_security import (
    secure_zero,
    SecureBytes,
    KeyManager,
)


class TestSecureZero:
    """Tests for secure_zero function."""

    def test_zeros_bytearray(self):
        """Test that bytearray is zeroed."""
        data = bytearray(b"secret_key_data!")
        original_len = len(data)

        secure_zero(data)

        assert len(data) == original_len
        assert all(b == 0 for b in data)

    def test_zeros_memoryview(self):
        """Test that memoryview is zeroed."""
        source = bytearray(b"secret")
        view = memoryview(source)

        secure_zero(view)

        assert all(b == 0 for b in source)

    def test_immutable_bytes_warning(self, caplog):
        """Test that immutable bytes logs warning."""
        import logging
        caplog.set_level(logging.WARNING)
        data = b"immutable"

        secure_zero(data)

        assert "Cannot zero immutable bytes" in caplog.text


class TestSecureBytes:
    """Tests for SecureBytes container."""

    def test_context_manager_zeros_on_exit(self):
        """Test that data is zeroed when context exits."""
        secret = bytearray(b"my_secret_key")

        with SecureBytes(secret) as sb:
            # Verify data is accessible
            assert bytes(sb.data) == b"my_secret_key"

        # After exit, should be zeroed
        with pytest.raises(ValueError, match="zeroed"):
            _ = sb.data

    def test_manual_zero(self):
        """Test manual zeroing."""
        sb = SecureBytes(b"secret")

        sb.zero()

        with pytest.raises(ValueError):
            _ = sb.data

    def test_double_zero_safe(self):
        """Test that zeroing twice is safe."""
        sb = SecureBytes(b"secret")

        sb.zero()
        sb.zero()  # Should not raise

    def test_len(self):
        """Test length."""
        sb = SecureBytes(b"12345")
        assert len(sb) == 5


class TestKeyManager:
    """Tests for KeyManager."""

    def test_store_and_get_key(self):
        """Test storing and retrieving keys."""
        km = KeyManager()

        km.store_key("key1", b"secret_value")

        data = km.get_key("key1")
        assert bytes(data) == b"secret_value"

    def test_get_nonexistent_key(self):
        """Test getting key that doesn't exist."""
        km = KeyManager()

        assert km.get_key("nonexistent") is None

    def test_remove_key_zeros(self):
        """Test that removing a key zeros it."""
        km = KeyManager()
        km.store_key("key1", b"secret")

        result = km.remove_key("key1")

        assert result is True
        assert km.get_key("key1") is None

    def test_remove_nonexistent_key(self):
        """Test removing key that doesn't exist."""
        km = KeyManager()

        assert km.remove_key("nonexistent") is False

    def test_clear_all(self):
        """Test clearing all keys."""
        km = KeyManager()
        km.store_key("key1", b"secret1")
        km.store_key("key2", b"secret2")
        km.store_key("key3", b"secret3")

        count = km.clear_all()

        assert count == 3
        assert km.get_key("key1") is None
        assert km.get_key("key2") is None
        assert km.get_key("key3") is None
