from abc import ABC, abstractmethod


class IKeyValueStorePort(ABC):
    """Port for Key-Value storage operations.
    Used for projection state, caching, and metadata.
    """

    @abstractmethod
    def get(self, key: str) -> bytes | None:
        """Retrieve a value by key. Returns None if not found."""
        ...

    @abstractmethod
    def put(self, key: str, value: bytes) -> None:
        """Store a value by key. Overwrites existing value."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a key-value pair."""
        ...
