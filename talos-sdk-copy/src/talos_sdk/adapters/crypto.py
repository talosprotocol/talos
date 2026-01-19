from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from talos_sdk.ports.crypto import ICryptoPort


class Ed25519CryptoAdapter(ICryptoPort):
    def sign(self, data: bytes, key: bytes) -> bytes:
        """Sign data using Ed25519 private key.
        Key must be 32 bytes (seed).
        """
        # Load from seed (32 bytes)
        private_key = Ed25519PrivateKey.from_private_bytes(key)
        return private_key.sign(data)

    def verify(self, data: bytes, sig: bytes, key: bytes) -> bool:
        """Verify signature using Ed25519 public key.
        Key must be 32 bytes.
        """
        try:
            public_key = Ed25519PublicKey.from_public_bytes(key)
            public_key.verify(sig, data)
            return True
        except InvalidSignature:
            return False
        except ValueError:
            # Invalid key format
            return False
