from abc import ABC, abstractmethod


class ICryptoPort(ABC):
    """Port for cryptographic operations (signing, verification).
    Abstracts the underlying crypto implementation (e.g. Ed25519).
    """

    @abstractmethod
    def sign(self, data: bytes, key: bytes) -> bytes:
        """Sign data using a private key."""
        ...

    @abstractmethod
    def verify(self, data: bytes, sig: bytes, key: bytes) -> bool:
        """Verify a signature using a public key."""
        ...
