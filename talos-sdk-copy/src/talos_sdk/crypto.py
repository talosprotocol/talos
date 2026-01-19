"""Cryptographic primitives for Talos SDK.

Provides wrappers for X25519, Ed25519, and common utilities.
"""

import base64
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from pydantic import BaseModel, ConfigDict
import os


def b64u_encode(data: bytes) -> str:
    """Base64URL encoding without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def b64u_decode(data: str) -> bytes:
    """Base64URL decoding without padding."""
    padding = "=" * (4 - (len(data) % 4))
    if padding == "====":
        padding = ""
    return base64.urlsafe_b64decode(data + padding)


class KeyPair(BaseModel):
    """A generic keypair (Ed25519 or X25519)."""

    public_key: bytes
    private_key: bytes
    key_type: str = "x25519"  # x25519 or ed25519

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert to base64 dictionary."""
        return {
            "public": base64.b64encode(self.public_key).decode(),
            "private": base64.b64encode(self.private_key).decode(),
            "type": self.key_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyPair":
        """Load from base64 dictionary."""
        return cls(
            public_key=base64.b64decode(data["public"]),
            private_key=base64.b64decode(data["private"]),
            key_type=data.get("type", "x25519"),
        )


def generate_encryption_keypair() -> KeyPair:
    """Generate an ephemeral X25519 keypair."""
    priv = X25519PrivateKey.generate()
    pub = priv.public_key()

    # Use Raw encoding for X25519
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )

    pub_bytes = pub.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)
    priv_bytes = priv.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )

    return KeyPair(
        public_key=pub_bytes,
        private_key=priv_bytes,
        key_type="x25519",
    )


def generate_signing_keypair() -> KeyPair:
    """Generate an Ed25519 signing keypair."""
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    pub_bytes = pub.public_bytes_raw()
    priv_bytes = priv.private_bytes_raw()

    return KeyPair(
        public_key=pub_bytes,
        private_key=priv_bytes,
        key_type="ed25519",
    )


def sign_message(message: bytes, private_key_bytes: bytes) -> bytes:
    """Sign a message with Ed25519."""
    priv = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    return priv.sign(message)


def verify_signature(message: bytes, signature: bytes, public_key_bytes: bytes) -> bool:
    """Verify an Ed25519 signature."""
    try:
        pub = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        pub.verify(signature, message)
        return True
    except Exception:
        return False


def derive_shared_secret(private_key_bytes: bytes, peer_public_key_bytes: bytes) -> bytes:
    """Derive X25519 shared secret."""
    priv = X25519PrivateKey.from_private_bytes(private_key_bytes)
    pub = X25519PublicKey.from_public_bytes(peer_public_key_bytes)
    return priv.exchange(pub)


def encrypt_message(message: bytes, key: bytes) -> tuple[bytes, bytes]:
    """Encrypt using ChaCha20Poly1305. Returns (nonce, ciphertext)."""
    cipher = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ciphertext = cipher.encrypt(nonce, message, None)
    return nonce, ciphertext


def decrypt_message(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    """Decrypt using ChaCha20Poly1305."""
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, None)


def hash_data(data: bytes) -> str:
    """Compute SHA-256 hash (hex string)."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize().hex()
