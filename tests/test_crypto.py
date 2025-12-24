"""
Tests for the cryptography module.
"""

import pytest

from src.core.crypto import (
    KeyPair,
    Wallet,
    generate_signing_keypair,
    generate_encryption_keypair,
    sign_message,
    verify_signature,
    derive_shared_secret,
    encrypt_message,
    decrypt_message,
    hash_data,
    hash_string,
)


class TestKeyPair:
    """Tests for KeyPair class."""
    
    def test_keypair_creation(self):
        """Test that key pairs can be created."""
        kp = generate_signing_keypair()
        
        assert isinstance(kp, KeyPair)
        assert len(kp.private_key) == 32  # Ed25519 private key
        assert len(kp.public_key) == 32   # Ed25519 public key
    
    def test_keypair_serialization(self):
        """Test KeyPair to/from dict conversion."""
        original = generate_signing_keypair()
        
        data = original.model_dump()
        restored = KeyPair.model_validate(data)
        
        assert restored.private_key == original.private_key
        assert restored.public_key == original.public_key
    
    def test_public_key_hex(self):
        """Test public key hex representation."""
        kp = generate_signing_keypair()
        
        hex_key = kp.public_key_hex
        
        assert len(hex_key) == 64  # 32 bytes = 64 hex chars
        assert all(c in "0123456789abcdef" for c in hex_key)


class TestSignatures:
    """Tests for digital signatures."""
    
    def test_sign_and_verify(self):
        """Test signing and verifying a message."""
        kp = generate_signing_keypair()
        message = b"Hello, World!"
        
        signature = sign_message(message, kp.private_key)
        valid = verify_signature(message, signature, kp.public_key)
        
        assert len(signature) == 64  # Ed25519 signature
        assert valid is True
    
    def test_invalid_signature_fails(self):
        """Test that invalid signatures are rejected."""
        kp = generate_signing_keypair()
        message = b"Hello, World!"
        
        signature = sign_message(message, kp.private_key)
        
        # Tamper with message
        valid = verify_signature(b"Tampered!", signature, kp.public_key)
        assert valid is False
    
    def test_wrong_key_fails(self):
        """Test that wrong public key fails verification."""
        kp1 = generate_signing_keypair()
        kp2 = generate_signing_keypair()
        message = b"Hello, World!"
        
        signature = sign_message(message, kp1.private_key)
        
        # Verify with wrong key
        valid = verify_signature(message, signature, kp2.public_key)
        assert valid is False


class TestEncryption:
    """Tests for encryption/decryption."""
    
    def test_generate_encryption_keypair(self):
        """Test encryption keypair generation."""
        kp = generate_encryption_keypair()
        
        assert len(kp.private_key) == 32  # X25519 private key
        assert len(kp.public_key) == 32   # X25519 public key
    
    def test_shared_secret_derivation(self):
        """Test that both parties derive same shared secret."""
        alice = generate_encryption_keypair()
        bob = generate_encryption_keypair()
        
        # Alice derives secret with Bob's public key
        secret_alice = derive_shared_secret(alice.private_key, bob.public_key)
        
        # Bob derives secret with Alice's public key
        secret_bob = derive_shared_secret(bob.private_key, alice.public_key)
        
        # Should be the same
        assert secret_alice == secret_bob
        assert len(secret_alice) == 32
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        key = b"0" * 32  # 32-byte key
        plaintext = b"Secret message!"
        
        nonce, ciphertext = encrypt_message(plaintext, key)
        decrypted = decrypt_message(ciphertext, key, nonce)
        
        assert decrypted == plaintext
    
    def test_wrong_key_fails_decryption(self):
        """Test that wrong key fails to decrypt."""
        key1 = b"0" * 32
        key2 = b"1" * 32
        plaintext = b"Secret message!"
        
        nonce, ciphertext = encrypt_message(plaintext, key1)
        
        with pytest.raises(Exception):  # InvalidTag
            decrypt_message(ciphertext, key2, nonce)


class TestHashing:
    """Tests for hash utilities."""
    
    def test_hash_data(self):
        """Test hashing bytes."""
        h = hash_data(b"hello")
        
        assert len(h) == 64  # SHA-256 hex
    
    def test_hash_string(self):
        """Test hashing string."""
        h = hash_string("hello")
        
        assert len(h) == 64
        assert h == hash_data(b"hello")
    
    def test_hash_consistency(self):
        """Test that same input produces same hash."""
        h1 = hash_string("test")
        h2 = hash_string("test")
        
        assert h1 == h2


class TestWallet:
    """Tests for Wallet class."""
    
    def test_wallet_generation(self):
        """Test wallet generation."""
        wallet = Wallet.generate("Alice")
        
        assert wallet.name == "Alice"
        assert wallet.signing_keys is not None
        assert wallet.encryption_keys is not None
        assert len(wallet.address) == 64
    
    def test_wallet_signing(self):
        """Test that wallet can sign messages."""
        wallet = Wallet.generate("Test")
        message = b"Test message"
        
        signature = wallet.sign(message)
        valid = verify_signature(message, signature, wallet.signing_keys.public_key)
        
        assert valid is True
    
    def test_wallet_serialization(self):
        """Test wallet to/from dict conversion."""
        original = Wallet.generate("Test")
        
        data = original.model_dump()
        restored = Wallet.model_validate(data)
        
        assert restored.name == original.name
        assert restored.address == original.address
