"""Talos SDK Wallet.

Identity management as defined in SDK_CONTRACT.md.
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .errors import TalosInvalidInputError

# Base58btc alphabet for DID encoding
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58_encode(data: bytes) -> str:
    """Encode bytes to base58btc."""
    num = int.from_bytes(data, "big")
    result = []
    while num > 0:
        num, remainder = divmod(num, 58)
        result.append(_BASE58_ALPHABET[remainder])
    # Handle leading zeros
    for byte in data:
        if byte == 0:
            result.append(_BASE58_ALPHABET[0])
        else:
            break
    return "".join(reversed(result))


class Wallet:
    """Talos identity wallet for key management and signing.

    Implements the Identity module from SDK_CONTRACT.md.
    """

    def __init__(
        self,
        private_key: Ed25519PrivateKey,
        name: str | None = None,
    ):
        """Initialize a Wallet from a private key.

        Args:
            private_key: Ed25519 private key
            name: Optional human-readable name
        """
        self._private_key = private_key
        self._public_key = private_key.public_key()
        self._name = name

    @classmethod
    def generate(cls, name: str | None = None) -> "Wallet":
        """Generate a new wallet with a random keypair.

        Args:
            name: Optional human-readable name for the wallet

        Returns:
            A new Wallet instance with a randomly generated keypair

        Note:
            This method is non-deterministic (uses secure random).
        """
        private_key = Ed25519PrivateKey.generate()
        return cls(private_key, name)

    @classmethod
    def from_seed(cls, seed: bytes, name: str | None = None) -> "Wallet":
        """Create a wallet from a 32-byte seed.

        Args:
            seed: 32-byte seed (raw bytes)
            name: Optional human-readable name

        Returns:
            A Wallet instance derived deterministically from the seed

        Raises:
            TalosInvalidInputError: If seed length is not 32 bytes
        """
        if len(seed) != 32:
            raise TalosInvalidInputError(
                f"Seed must be exactly 32 bytes, got {len(seed)}",
                details={"seed_length": len(seed)},
            )
        private_key = Ed25519PrivateKey.from_private_bytes(seed)
        return cls(private_key, name)

    def to_did(self) -> str:
        """Convert the wallet's public key to a DID string.

        Returns:
            DID string in format did:key:z6Mk...

        Note:
            Deterministic - same public key produces identical DID.
        """
        # Multicodec prefix for Ed25519 public key: 0xed01
        prefix = bytes([0xED, 0x01])
        public_bytes = self._public_key.public_bytes_raw()
        multicodec_key = prefix + public_bytes
        return f"did:key:z{_base58_encode(multicodec_key)}"

    @property
    def address(self) -> str:
        """Get the hex-encoded public key hash (address).

        Returns:
            64-character hex string
        """
        public_bytes = self._public_key.public_bytes_raw()
        return hashlib.sha256(public_bytes).hexdigest()

    @property
    def public_key(self) -> bytes:
        """Get the 32-byte public key."""
        return self._public_key.public_bytes_raw()

    @property
    def name(self) -> str | None:
        """Get the wallet name."""
        return self._name

    @property
    def key_id(self) -> str:
        """Get the key ID (truncated DID for HTTP headers)."""
        return self.to_did()

    def sign(self, message: bytes) -> bytes:
        """Sign a message using Ed25519.

        Args:
            message: Arbitrary message bytes

        Returns:
            64-byte Ed25519 signature

        Note:
            Deterministic - Ed25519 signing is deterministic.
        """
        return self._private_key.sign(message)

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify a signature against a message and public key.

        Args:
            message: Original message bytes
            signature: 64-byte signature
            public_key: 32-byte public key

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            pk = Ed25519PublicKey.from_public_bytes(public_key)
            pk.verify(signature, message)
            return True
        except Exception:
            return False
