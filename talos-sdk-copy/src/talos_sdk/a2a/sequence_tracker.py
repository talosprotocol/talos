"""Sequence tracking for sender_seq monotonicity."""

import threading
from typing import Protocol


class SequenceStorage(Protocol):
    """Interface for persisting sequence state."""

    def load(self, session_id: str, sender_id: str) -> int | None:
        """Load the next sequence number for (session_id, sender_id)."""
        ...

    def save(self, session_id: str, sender_id: str, next_seq: int) -> None:
        """Save the next sequence number for (session_id, sender_id)."""
        ...


class InMemorySequenceStorage:
    """Thread-safe in-memory sequence storage."""

    def __init__(self):
        self._data: dict[tuple[str, str], int] = {}
        self._lock = threading.Lock()

    def load(self, session_id: str, sender_id: str) -> int | None:
        with self._lock:
            return self._data.get((session_id, sender_id))

    def save(self, session_id: str, sender_id: str, next_seq: int) -> None:
        with self._lock:
            self._data[(session_id, sender_id)] = next_seq


# Process-global singleton for consistent sequence tracking across instances
_DEFAULT_STORAGE = InMemorySequenceStorage()


class SequenceTracker:
    """Tracks sender_seq per (session_id, sender_id) with atomic reserve().

    Usage:
        tracker = SequenceTracker.load(session_id, sender_id)
        seq = tracker.reserve()  # Atomically get and persist next seq
    """

    def __init__(
        self,
        session_id: str,
        sender_id: str,
        storage: SequenceStorage | None = None,
    ):
        self._session_id = session_id
        self._sender_id = sender_id
        self._storage = storage or _DEFAULT_STORAGE
        self._next_seq: int = self._storage.load(session_id, sender_id) or 0
        self._lock = threading.Lock()

    def reserve(self) -> int:
        """Atomically reserve and persist the next sequence number.

        Returns:
            The reserved sequence number (0-indexed, monotonically increasing).
        """
        with self._lock:
            seq = self._next_seq
            self._next_seq += 1
            self._storage.save(self._session_id, self._sender_id, self._next_seq)
            return seq

    def current(self) -> int:
        """Get current next sequence without incrementing."""
        return self._next_seq

    @classmethod
    def load(
        cls, session_id: str, sender_id: str, storage: SequenceStorage | None = None
    ) -> "SequenceTracker":
        """Load or create a SequenceTracker for (session_id, sender_id)."""
        return cls(session_id, sender_id, storage)
