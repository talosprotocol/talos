"""
Key Security Utilities for Talos Protocol (Phase 2 Hardening).

Provides best-effort key zeroization for sensitive cryptographic material.

Note: Python's memory management makes true zeroization difficult.
These are best-effort mitigations, not guarantees.
"""

import ctypes
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def secure_zero(data: bytes | bytearray | memoryview) -> None:
    """
    Best-effort zeroing of sensitive bytes in memory.
    
    This is NOT a guarantee due to Python's GC, but reduces window of exposure.
    
    Args:
        data: Bytes to zero (must be mutable type for in-place zeroing)
    """
    if isinstance(data, bytes):
        # Immutable - can't zero in place, log warning
        logger.warning("Cannot zero immutable bytes - use bytearray for sensitive data")
        return
    
    if isinstance(data, (bytearray, memoryview)):
        try:
            # Direct memory zeroing
            addr = ctypes.addressof(ctypes.c_char.from_buffer(data))
            ctypes.memset(addr, 0, len(data))
        except (TypeError, ValueError) as e:
            # Fall back to Python-level zeroing
            for i in range(len(data)):
                data[i] = 0
            logger.debug(f"Used Python-level zeroing: {e}")


class SecureBytes:
    """
    Container for sensitive bytes with automatic zeroization.
    
    Usage:
        with SecureBytes(secret_key) as key:
            # Use key.data
            do_crypto(key.data)
        # key is zeroed on exit
    """
    
    def __init__(self, data: bytes | bytearray):
        """
        Initialize with sensitive data.
        
        Args:
            data: Bytes to protect. Copied to mutable buffer.
        """
        self._data = bytearray(data)
        self._zeroed = False
    
    @property
    def data(self) -> memoryview:
        """Get readonly view of data."""
        if self._zeroed:
            raise ValueError("Data has been zeroed")
        return memoryview(self._data)
    
    def __enter__(self) -> "SecureBytes":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.zero()
    
    def zero(self) -> None:
        """Zero the data and mark as cleared."""
        if not self._zeroed:
            secure_zero(self._data)
            self._zeroed = True
            logger.debug("SecureBytes zeroed")
    
    def __del__(self):
        """Best-effort cleanup on garbage collection."""
        try:
            self.zero()
        except Exception:
            pass  # Ignore errors during GC
    
    def __len__(self) -> int:
        return len(self._data)


class KeyManager:
    """
    Manages private keys with automatic zeroization on session end.
    """
    
    def __init__(self):
        self._keys: dict[str, SecureBytes] = {}
    
    def store_key(self, key_id: str, key_bytes: bytes) -> None:
        """Store a private key securely."""
        self._keys[key_id] = SecureBytes(key_bytes)
        logger.debug(f"Stored key: {key_id}")
    
    def get_key(self, key_id: str) -> Optional[memoryview]:
        """Get a stored key (readonly view)."""
        secure = self._keys.get(key_id)
        if secure:
            return secure.data
        return None
    
    def remove_key(self, key_id: str) -> bool:
        """Remove and zero a key."""
        if key_id in self._keys:
            self._keys[key_id].zero()
            del self._keys[key_id]
            logger.debug(f"Removed and zeroed key: {key_id}")
            return True
        return False
    
    def clear_all(self) -> int:
        """Zero and remove all keys."""
        count = len(self._keys)
        for secure in self._keys.values():
            secure.zero()
        self._keys.clear()
        logger.info(f"Cleared and zeroed {count} keys")
        return count
    
    def __del__(self):
        """Best-effort cleanup."""
        try:
            self.clear_all()
        except Exception:
            pass
