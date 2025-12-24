"""
Fast serialization utilities for enterprise performance.

This module provides:
- Fast JSON using orjson (10x faster than stdlib)
- MessagePack binary serialization
- Object pooling for reduced allocations
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, TypeVar

logger = logging.getLogger(__name__)

# Try to import orjson for faster JSON
try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False
    logger.debug("orjson not installed, using stdlib json")


def fast_json_dumps(obj: Any, sort_keys: bool = True) -> bytes:
    """
    Fast JSON serialization.
    
    Uses orjson if available (10x faster), falls back to stdlib.
    
    Args:
        obj: Object to serialize
        sort_keys: Sort dictionary keys (for consistent hashing)
        
    Returns:
        JSON bytes
    """
    if ORJSON_AVAILABLE:
        options = orjson.OPT_SORT_KEYS if sort_keys else 0
        return orjson.dumps(obj, option=options)
    else:
        return json.dumps(obj, sort_keys=sort_keys).encode()


def fast_json_loads(data: bytes | str) -> Any:
    """
    Fast JSON deserialization.
    
    Args:
        data: JSON bytes or string
        
    Returns:
        Parsed object
    """
    if ORJSON_AVAILABLE:
        if isinstance(data, str):
            data = data.encode()
        return orjson.loads(data)
    else:
        if isinstance(data, bytes):
            data = data.decode()
        return json.loads(data)


T = TypeVar('T')


class ObjectPool:
    """
    Generic object pool for reducing allocations.
    
    Reuses objects instead of creating new ones, reducing
    GC pressure and improving performance.
    
    Example:
        pool = ObjectPool(lambda: [], max_size=100)
        
        obj = pool.acquire()
        obj.append("data")
        # ... use object ...
        obj.clear()
        pool.release(obj)
    """
    
    def __init__(
        self,
        factory: Any,  # Callable that creates new objects
        max_size: int = 100,
        reset_fn: Optional[Any] = None,  # Callable to reset object
    ):
        """
        Initialize object pool.
        
        Args:
            factory: Callable that creates new objects
            max_size: Maximum pool size
            reset_fn: Optional function to reset object state
        """
        self._factory = factory
        self._max_size = max_size
        self._reset_fn = reset_fn
        self._pool: list = []
        
        # Metrics
        self.hits = 0
        self.misses = 0
    
    def acquire(self) -> Any:
        """Get an object from the pool or create a new one."""
        if self._pool:
            self.hits += 1
            return self._pool.pop()
        else:
            self.misses += 1
            return self._factory()
    
    def release(self, obj: Any) -> None:
        """Return an object to the pool."""
        if len(self._pool) < self._max_size:
            if self._reset_fn:
                self._reset_fn(obj)
            self._pool.append(obj)
    
    @property
    def size(self) -> int:
        """Current pool size."""
        return len(self._pool)
    
    @property
    def hit_rate(self) -> float:
        """Pool hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def clear(self) -> None:
        """Clear the pool."""
        self._pool.clear()
        self.hits = 0
        self.misses = 0


# Pre-configured pools for common types
_list_pool = ObjectPool(list, max_size=500, reset_fn=lambda x: x.clear())
_dict_pool = ObjectPool(dict, max_size=500, reset_fn=lambda x: x.clear())
_bytes_pool = ObjectPool(bytearray, max_size=100, reset_fn=lambda x: x.clear())


def get_list() -> list:
    """Get a list from the pool."""
    return _list_pool.acquire()


def release_list(lst: list) -> None:
    """Return a list to the pool."""
    _list_pool.release(lst)


def get_dict() -> dict:
    """Get a dict from the pool."""
    return _dict_pool.acquire()


def release_dict(d: dict) -> None:
    """Return a dict to the pool."""
    _dict_pool.release(d)


def get_buffer(size: int = 0) -> bytearray:
    """Get a byte buffer from the pool."""
    buf = _bytes_pool.acquire()
    if size > 0:
        buf.extend(b'\x00' * size)
    return buf


def release_buffer(buf: bytearray) -> None:
    """Return a byte buffer to the pool."""
    _bytes_pool.release(buf)


def pool_stats() -> dict:
    """Get stats for all pools."""
    return {
        "list_pool": {
            "size": _list_pool.size,
            "hit_rate": _list_pool.hit_rate,
        },
        "dict_pool": {
            "size": _dict_pool.size,
            "hit_rate": _dict_pool.hit_rate,
        },
        "bytes_pool": {
            "size": _bytes_pool.size,
            "hit_rate": _bytes_pool.hit_rate,
        },
    }


from pydantic import BaseModel, ConfigDict


class SerializationStats(BaseModel):
    """Statistics for serialization performance."""
    
    calls: int = 0
    bytes_total: int = 0
    avg_size: float = 0.0
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def record(self, size: int) -> None:
        """Record a serialization operation."""
        self.calls += 1
        self.bytes_total += size
        self.avg_size = self.bytes_total / self.calls


# Global serialization stats
_serialize_stats = SerializationStats()
_deserialize_stats = SerializationStats()


def serialize_message(msg: Any) -> bytes:
    """
    Serialize a message for transmission.
    
    Uses fast JSON with stats tracking.
    Handles Pydantic models automatically.
    """
    if hasattr(msg, "model_dump"):
        data_dict = msg.model_dump()
        data = fast_json_dumps(data_dict)
    elif hasattr(msg, "to_dict"):
        data_dict = msg.to_dict()
        data = fast_json_dumps(data_dict)
    else:
        data = fast_json_dumps(msg)
        
    _serialize_stats.record(len(data))
    return data


def deserialize_message(data: bytes) -> dict:
    """
    Deserialize a received message.
    """
    _deserialize_stats.record(len(data))
    return fast_json_loads(data)


def serialization_stats() -> dict:
    """Get serialization statistics."""
    return {
        "serialize": {
            "calls": _serialize_stats.calls,
            "bytes_total": _serialize_stats.bytes_total,
            "avg_size": _serialize_stats.avg_size,
        },
        "deserialize": {
            "calls": _deserialize_stats.calls,
            "bytes_total": _deserialize_stats.bytes_total,
            "avg_size": _deserialize_stats.avg_size,
        },
    }
