"""
Tests for the Talos SDK Wallet module.
"""

import pytest

from talos_sdk import TalosInvalidInputError, Wallet


class TestWallet:
    """Tests for Wallet class."""

    def test_generate_creates_valid_wallet(self):
        """Generate should create a valid wallet."""
        wallet = Wallet.generate(name="test")
        assert wallet is not None
        assert wallet.name == "test"
        assert len(wallet.public_key) == 32
        assert len(wallet.address) == 64  # SHA256 hex

    def test_generate_produces_unique_wallets(self):
        """Each generate call should produce a unique wallet."""
        wallet1 = Wallet.generate()
        wallet2 = Wallet.generate()
        assert wallet1.public_key != wallet2.public_key

    def test_from_seed_is_deterministic(self):
        """from_seed should be deterministic."""
        seed = bytes(32)  # All zeros
        wallet1 = Wallet.from_seed(seed)
        wallet2 = Wallet.from_seed(seed)
        assert wallet1.public_key == wallet2.public_key
        assert wallet1.to_did() == wallet2.to_did()

    def test_from_seed_rejects_wrong_length(self):
        """from_seed should reject seeds that aren't 32 bytes."""
        with pytest.raises(TalosInvalidInputError) as exc:
            Wallet.from_seed(bytes(16))
        assert "TALOS_INVALID_INPUT" == exc.value.code
        assert "32 bytes" in exc.value.message

    def test_to_did_format(self):
        """to_did should return a valid DID string."""
        wallet = Wallet.generate()
        did = wallet.to_did()
        assert did.startswith("did:key:z")
        assert len(did) > 20

    def test_sign_produces_64_byte_signature(self):
        """sign should produce a 64-byte Ed25519 signature."""
        wallet = Wallet.generate()
        signature = wallet.sign(b"test message")
        assert len(signature) == 64

    def test_sign_is_deterministic(self):
        """Ed25519 signing should be deterministic."""
        seed = bytes(32)
        wallet = Wallet.from_seed(seed)
        sig1 = wallet.sign(b"test")
        sig2 = wallet.sign(b"test")
        assert sig1 == sig2

    def test_verify_valid_signature(self):
        """verify should return True for valid signature."""
        wallet = Wallet.generate()
        message = b"test message"
        signature = wallet.sign(message)
        assert Wallet.verify(message, signature, wallet.public_key) is True

    def test_verify_invalid_signature(self):
        """verify should return False for invalid signature."""
        wallet = Wallet.generate()
        message = b"test message"
        # Use a bad signature (all zeros)
        bad_sig = bytes(64)
        assert Wallet.verify(message, bad_sig, wallet.public_key) is False

    def test_verify_wrong_message(self):
        """verify should return False for wrong message."""
        wallet = Wallet.generate()
        signature = wallet.sign(b"original")
        assert Wallet.verify(b"tampered", signature, wallet.public_key) is False

    def test_verify_wrong_key(self):
        """verify should return False for wrong public key."""
        wallet1 = Wallet.generate()
        wallet2 = Wallet.generate()
        message = b"test"
        signature = wallet1.sign(message)
        assert Wallet.verify(message, signature, wallet2.public_key) is False
