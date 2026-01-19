from abc import ABC, abstractmethod
from typing import Any


class IHashPort(ABC):
    """Port for hashing operations.
    Includes standard hashing and canonical object hashing.
    """

    @abstractmethod
    def sha256(self, data: bytes) -> bytes:
        """Compute SHA-256 hash of bytes."""
        ...

    @abstractmethod
    def canonical_hash(self, obj: Any) -> bytes:
        """Compute hash of an object using canonical JSON Serialization.
        Essential for content-addressable storage and signatures.
        """
        ...
