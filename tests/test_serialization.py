"""
Tests for fast serialization and object pooling.
"""

import pytest
from src.core.serialization import (
    fast_json_dumps,
    fast_json_loads,
    ObjectPool,
    get_list,
    release_list,
    get_dict,
    release_dict,
    pool_stats,
    serialize_message,
    deserialize_message,
)


class TestFastJson:
    """Tests for fast JSON serialization."""

    def test_dumps_simple(self):
        """Serialize simple object."""
        data = {"key": "value", "num": 123}
        result = fast_json_dumps(data)

        assert b"key" in result
        assert b"value" in result

    def test_dumps_sorted_keys(self):
        """Keys are sorted for consistent hashing."""
        data = {"z": 1, "a": 2, "m": 3}
        result = fast_json_dumps(data, sort_keys=True)

        # a should come before m, m before z
        a_pos = result.find(b'"a"')
        m_pos = result.find(b'"m"')
        z_pos = result.find(b'"z"')

        assert a_pos < m_pos < z_pos

    def test_loads_bytes(self):
        """Deserialize from bytes."""
        data = b'{"key": "value"}'
        result = fast_json_loads(data)

        assert result == {"key": "value"}

    def test_loads_string(self):
        """Deserialize from string."""
        data = '{"key": "value"}'
        result = fast_json_loads(data)

        assert result == {"key": "value"}

    def test_roundtrip(self):
        """Serialize and deserialize."""
        original = {"nested": {"list": [1, 2, 3]}, "bool": True}
        serialized = fast_json_dumps(original)
        result = fast_json_loads(serialized)

        assert result == original


class TestObjectPool:
    """Tests for object pooling."""

    def test_acquire_creates_new(self):
        """Acquire creates new object when pool empty."""
        pool = ObjectPool(list, max_size=10)
        obj = pool.acquire()

        assert obj == []
        assert pool.misses == 1

    def test_release_and_acquire(self):
        """Released object can be reacquired."""
        pool = ObjectPool(list, max_size=10)
        obj1 = pool.acquire()
        obj1.append("data")
        pool.release(obj1)

        obj2 = pool.acquire()
        assert obj2 is obj1  # Same object
        assert pool.hits == 1

    def test_reset_function(self):
        """Reset function clears object."""
        pool = ObjectPool(list, max_size=10, reset_fn=lambda x: x.clear())

        obj = pool.acquire()
        obj.append("data")
        pool.release(obj)

        obj2 = pool.acquire()
        assert obj2 == []  # Was cleared

    def test_max_size_respected(self):
        """Pool doesn't exceed max size."""
        pool = ObjectPool(list, max_size=2)

        objs = [pool.acquire() for _ in range(5)]
        for obj in objs:
            pool.release(obj)

        assert pool.size == 2  # Only 2 kept

    def test_hit_rate(self):
        """Hit rate calculation."""
        pool = ObjectPool(list, max_size=10)

        obj = pool.acquire()  # miss
        pool.release(obj)
        pool.acquire()  # hit
        pool.acquire()  # miss (pool empty)

        assert pool.hits == 1
        assert pool.misses == 2
        assert pool.hit_rate == pytest.approx(1/3)

    def test_clear(self):
        """Clear empties pool and resets stats."""
        pool = ObjectPool(list, max_size=10)
        pool.acquire()
        pool.release([])
        pool.clear()

        assert pool.size == 0
        assert pool.hits == 0
        assert pool.misses == 0


class TestGlobalPools:
    """Tests for pre-configured pools."""

    def test_list_pool(self):
        """Global list pool."""
        lst = get_list()
        assert isinstance(lst, list)

        lst.append("test")
        release_list(lst)

        lst2 = get_list()
        assert lst2 == []  # Was reset

    def test_dict_pool(self):
        """Global dict pool."""
        d = get_dict()
        assert isinstance(d, dict)

        d["key"] = "value"
        release_dict(d)

        d2 = get_dict()
        assert d2 == {}  # Was reset

    def test_pool_stats(self):
        """Pool statistics."""
        stats = pool_stats()

        assert "list_pool" in stats
        assert "dict_pool" in stats
        assert "bytes_pool" in stats


class TestMessageSerialization:
    """Tests for message serialization."""

    def test_serialize_message(self):
        """Serialize a message dict."""
        msg = {"id": "123", "content": "hello"}
        data = serialize_message(msg)

        assert isinstance(data, bytes)
        assert b"123" in data

    def test_deserialize_message(self):
        """Deserialize message bytes."""
        data = b'{"id": "456", "content": "world"}'
        msg = deserialize_message(data)

        assert msg["id"] == "456"
        assert msg["content"] == "world"

    def test_roundtrip(self):
        """Message roundtrip."""
        original = {"type": "text", "payload": [1, 2, 3]}
        serialized = serialize_message(original)
        result = deserialize_message(serialized)

        assert result == original
