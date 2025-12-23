"""
Cryptographic utilities for secure messaging.

This module provides:
- Ed25519 key pair generation for digital signatures
- X25519 key exchange for establishing shared secrets
- ChaCha20-Poly1305 encryption for message confidentiality
- Hash utilities for integrity verification
"""

import base64
import hashlib
import os
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


@dataclass
class KeyPair:
    """Container for a cryptographic key pair."""
    
    private_key: bytes
    public_key: bytes
    
    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary with base64-encoded keys."""
        return {
            "private_key": base64.b64encode(self.private_key).decode(),
            "public_key": base64.b64encode(self.public_key).decode()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "KeyPair":
        """Create from dictionary with base64-encoded keys."""
        return cls(
            private_key=base64.b64decode(data["private_key"]),
            public_key=base64.b64decode(data["public_key"])
        )
    
    @property
    def public_key_hex(self) -> str:
        """Get public key as hex string (for display/sharing)."""
        return self.public_key.hex()
    
    @property
    def public_key_short(self) -> str:
        """Get shortened public key for display."""
        hex_key = self.public_key_hex
        return f"{hex_key[:8]}...{hex_key[-8:]}"


def generate_signing_keypair() -> KeyPair:
    """
    Generate an Ed25519 key pair for digital signatures.
    
    Returns:
        KeyPair with private and public signing keys
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    return KeyPair(private_key=private_bytes, public_key=public_bytes)


def generate_encryption_keypair() -> KeyPair:
    """
    Generate an X25519 key pair for key exchange/encryption.
    
    Returns:
        KeyPair with private and public encryption keys
    """
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    return KeyPair(private_key=private_bytes, public_key=public_bytes)


def sign_message(message: bytes, private_key: bytes) -> bytes:
    """
    Sign a message using Ed25519.
    
    Args:
        message: The message to sign
        private_key: Ed25519 private key bytes
        
    Returns:
        64-byte signature
    """
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    return key.sign(message)


def verify_signature(message: bytes, signature: bytes, public_key: bytes) -> bool:
    """
    Verify an Ed25519 signature.
    
    Args:
        message: The original message
        signature: The signature to verify
        public_key: Ed25519 public key bytes
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        key = Ed25519PublicKey.from_public_bytes(public_key)
        key.verify(signature, message)
        return True
    except Exception:
        return False


def derive_shared_secret(
    private_key: bytes, 
    peer_public_key: bytes,
    info: bytes = b"bmp-message-key"
) -> bytes:
    """
    Derive a shared secret using X25519 key exchange.
    
    Args:
        private_key: Our X25519 private key
        peer_public_key: Peer's X25519 public key
        info: Context info for key derivation
        
    Returns:
        32-byte shared secret suitable for encryption
    """
    our_key = X25519PrivateKey.from_private_bytes(private_key)
    peer_key = X25519PublicKey.from_public_bytes(peer_public_key)
    
    shared_key = our_key.exchange(peer_key)
    
    # Derive encryption key using HKDF
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info
    )
    return hkdf.derive(shared_key)


def encrypt_message(plaintext: bytes, key: bytes, nonce: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Encrypt a message using ChaCha20-Poly1305.
    
    Args:
        plaintext: Message to encrypt
        key: 32-byte encryption key
        nonce: Optional 12-byte nonce (generated if not provided)
        
    Returns:
        Tuple of (nonce, ciphertext with auth tag)
    """
    if nonce is None:
        nonce = os.urandom(12)
    
    cipher = ChaCha20Poly1305(key)
    ciphertext = cipher.encrypt(nonce, plaintext, None)
    
    return nonce, ciphertext


def decrypt_message(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    """
    Decrypt a message using ChaCha20-Poly1305.
    
    Args:
        ciphertext: Encrypted message with auth tag
        key: 32-byte encryption key
        nonce: 12-byte nonce used during encryption
        
    Returns:
        Decrypted plaintext
        
    Raises:
        cryptography.exceptions.InvalidTag: If authentication fails
    """
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, None)


def hash_data(data: bytes) -> str:
    """
    Calculate SHA-256 hash of data.
    
    Args:
        data: Data to hash
        
    Returns:
        Hex-encoded hash string
    """
    return hashlib.sha256(data).hexdigest()


def hash_string(text: str) -> str:
    """
    Calculate SHA-256 hash of a string.
    
    Args:
        text: String to hash
        
    Returns:
        Hex-encoded hash string
    """
    return hash_data(text.encode())


@dataclass
class Wallet:
    """
    A wallet containing both signing and encryption key pairs.
    
    This represents a user's identity in the messaging network.
    """
    
    name: str
    signing_keys: KeyPair
    encryption_keys: KeyPair
    
    @classmethod
    def generate(cls, name: str) -> "Wallet":
        """Generate a new wallet with fresh key pairs."""
        return cls(
            name=name,
            signing_keys=generate_signing_keypair(),
            encryption_keys=generate_encryption_keypair()
        )
    
    @property
    def address(self) -> str:
        """Get the wallet address (signing public key hex)."""
        return self.signing_keys.public_key_hex
    
    @property
    def address_short(self) -> str:
        """Get shortened address for display."""
        return self.signing_keys.public_key_short
    
    def sign(self, message: bytes) -> bytes:
        """Sign a message with this wallet's signing key."""
        return sign_message(message, self.signing_keys.private_key)
    
    def to_dict(self) -> dict:
        """Serialize wallet to dictionary."""
        return {
            "name": self.name,
            "signing_keys": self.signing_keys.to_dict(),
            "encryption_keys": self.encryption_keys.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Deserialize wallet from dictionary."""
        return cls(
            name=data["name"],
            signing_keys=KeyPair.from_dict(data["signing_keys"]),
            encryption_keys=KeyPair.from_dict(data["encryption_keys"])
        )
    
    def __repr__(self) -> str:
        return f"Wallet(name={self.name!r}, address={self.address_short})"
