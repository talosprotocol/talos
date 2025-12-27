"""
Additional tests for storage.py to increase coverage.

Covers:
- BlockStorage methods
- IndexStorage methods
- LMDB fallback mode
- Async operations
- Edge cases
"""

import pytest
import asyncio
import tempfile
import shutil
import time
from pathlib import Path

from src.core.storage import (
    LMDBStorage,
    BlockStorage,
    IndexStorage,
    StorageConfig,
    LMDB_AVAILABLE,
)
from src.core.blockchain import Block


class TestLMDBStorageBasic:
    """Test basic LMDB storage operations."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def config(self, temp_dir):
        return StorageConfig(path=temp_dir, map_size=10 * 1024 * 1024)

    @pytest.fixture
    def storage(self, config):
        s = LMDBStorage(config)
        yield s
        s.close()

    def test_put_and_get(self, storage):
        """Test basic put and get."""
        with storage.write() as txn:
            assert storage.put(txn, b"key1", b"value1")

        with storage.read() as txn:
            assert storage.get(txn, b"key1") == b"value1"

    def test_delete(self, storage):
        """Test delete operation."""
        with storage.write() as txn:
            storage.put(txn, b"key1", b"value1")

        with storage.write() as txn:
            assert storage.delete(txn, b"key1")

        with storage.read() as txn:
            assert storage.get(txn, b"key1") is None

    def test_delete_nonexistent(self, storage):
        """Test delete of non-existent key."""
        with storage.write() as txn:
            result = storage.delete(txn, b"nonexistent")
            # Returns False if key doesn't exist (LMDB) or True (fallback)
            assert isinstance(result, bool)

    def test_exists(self, storage):
        """Test exists check."""
        with storage.write() as txn:
            storage.put(txn, b"key1", b"value1")

        with storage.read() as txn:
            assert storage.exists(txn, b"key1")
            assert not storage.exists(txn, b"key2")

    def test_keys_with_prefix(self, storage):
        """Test key iteration with prefix."""
        with storage.write() as txn:
            storage.put(txn, b"prefix:a", b"1")
            storage.put(txn, b"prefix:b", b"2")
            storage.put(txn, b"other:c", b"3")

        with storage.read() as txn:
            keys = list(storage.keys(txn, b"prefix:"))
            assert len(keys) == 2
            assert b"prefix:a" in keys
            assert b"prefix:b" in keys

    def test_count(self, storage):
        """Test entry count."""
        with storage.write() as txn:
            storage.put(txn, b"key1", b"value1")
            storage.put(txn, b"key2", b"value2")

        with storage.read() as txn:
            assert storage.count(txn) >= 2

    def test_stats(self, storage):
        """Test stats retrieval."""
        stats = storage.stats
        assert "entries" in stats

    def test_sync_to_disk(self, storage):
        """Test sync operation (should not raise)."""
        with storage.write() as txn:
            storage.put(txn, b"key1", b"value1")
        storage.sync_to_disk()


class TestLMDBStorageAsync:
    """Test async LMDB operations."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def storage(self, temp_dir):
        config = StorageConfig(path=temp_dir, map_size=10 * 1024 * 1024)
        s = LMDBStorage(config)
        yield s
        s.close()

    @pytest.mark.asyncio
    async def test_put_async(self, storage):
        """Test async put."""
        result = await storage.put_async(b"async_key", b"async_value")
        assert result

        with storage.read() as txn:
            assert storage.get(txn, b"async_key") == b"async_value"

    @pytest.mark.asyncio
    async def test_get_async(self, storage):
        """Test async get."""
        with storage.write() as txn:
            storage.put(txn, b"async_key", b"async_value")

        result = await storage.get_async(b"async_key")
        assert result == b"async_value"

    @pytest.mark.asyncio
    async def test_get_async_nonexistent(self, storage):
        """Test async get for non-existent key."""
        result = await storage.get_async(b"nonexistent")
        assert result is None


class TestBlockStorage:
    """Test BlockStorage operations."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def block_storage(self, temp_dir):
        config = StorageConfig(path=temp_dir, map_size=10 * 1024 * 1024)
        s = BlockStorage(config)
        yield s
        s.close()

    @pytest.fixture
    def sample_block(self):
        block = Block(index=0, timestamp=time.time(), data={"test": "data"}, previous_hash="0" * 64)
        block.mine(difficulty=1)
        return block

    def test_put_block_object(self, block_storage, sample_block):
        """Test storing a Block object."""
        block_storage.put_block(sample_block)

        retrieved = block_storage.get_block_by_hash(sample_block.hash)
        assert retrieved is not None
        assert retrieved["index"] == 0

    def test_put_block_dict(self, block_storage):
        """Test storing a block as dict."""
        block_dict = {
            "index": 5,
            "hash": "abc123" * 10 + "abcd",
            "data": {"msg": "hello"},
            "previous_hash": "0" * 64,
            "timestamp": 1234567890.0,
            "nonce": 0,
        }
        block_storage.put_block(block_dict)

        retrieved = block_storage.get_block_by_hash(block_dict["hash"])
        assert retrieved is not None
        assert retrieved["index"] == 5

    def test_get_block_by_height(self, block_storage, sample_block):
        """Test retrieving block by height."""
        block_storage.put_block(sample_block)

        retrieved = block_storage.get_block_by_height(0)
        assert retrieved is not None
        assert retrieved["hash"] == sample_block.hash

    def test_get_block_by_height_nonexistent(self, block_storage):
        """Test retrieving non-existent height."""
        retrieved = block_storage.get_block_by_height(999)
        assert retrieved is None

    def test_get_block_by_hash_nonexistent(self, block_storage):
        """Test retrieving non-existent hash."""
        retrieved = block_storage.get_block_by_hash("nonexistent")
        assert retrieved is None

    def test_get_latest_height(self, block_storage):
        """Test getting latest height."""
        blocks = []
        for i in range(3):
            block = Block(
                index=i,
                timestamp=time.time(),
                data={},
                previous_hash="0" * 64 if i == 0 else blocks[-1].hash
            )
            block.mine(difficulty=1)
            blocks.append(block)
            block_storage.put_block(block)

        assert block_storage.get_latest_height() == 2

    def test_get_latest_height_empty(self, block_storage):
        """Test getting latest height on empty storage."""
        assert block_storage.get_latest_height() == -1

    def test_put_blocks_batch(self, block_storage):
        """Test batch block insertion."""
        blocks = []
        for i in range(5):
            block = Block(
                index=i,
                timestamp=time.time(),
                data={},
                previous_hash="0" * 64 if i == 0 else blocks[-1].hash
            )
            block.mine(difficulty=1)
            blocks.append(block)

        count = block_storage.put_blocks_batch(blocks)
        assert count == 5

        for block in blocks:
            retrieved = block_storage.get_block_by_hash(block.hash)
            assert retrieved is not None

    def test_stats(self, block_storage, sample_block):
        """Test stats retrieval."""
        block_storage.put_block(sample_block)
        stats = block_storage.stats
        assert "entries" in stats


class TestIndexStorage:
    """Test IndexStorage operations."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def index_storage(self, temp_dir):
        config = StorageConfig(path=temp_dir, map_size=10 * 1024 * 1024)
        s = IndexStorage(config)
        yield s
        s.close()

    def test_index_message(self, index_storage):
        """Test indexing a message."""
        index_storage.index_message(
            message_id="msg123",
            block_hash="blockhash456",
            sender="alice",
            timestamp=1234567890.0
        )

        block = index_storage.get_block_for_message("msg123")
        assert block == "blockhash456"

    def test_get_block_for_message_nonexistent(self, index_storage):
        """Test getting block for non-existent message."""
        result = index_storage.get_block_for_message("nonexistent")
        assert result is None

    def test_get_messages_by_sender(self, index_storage):
        """Test getting messages by sender."""
        index_storage.index_message("msg1", "block1", "alice", 1000.0)
        index_storage.index_message("msg2", "block2", "alice", 2000.0)
        index_storage.index_message("msg3", "block3", "bob", 3000.0)

        alice_messages = index_storage.get_messages_by_sender("alice")
        assert len(alice_messages) == 2
        assert "msg1" in alice_messages
        assert "msg2" in alice_messages

    def test_get_messages_by_sender_empty(self, index_storage):
        """Test getting messages for sender with no messages."""
        result = index_storage.get_messages_by_sender("nobody")
        assert result == []


class TestLMDBFallback:
    """Test fallback mode when LMDB is not available."""

    @pytest.fixture
    def fallback_storage(self, temp_dir):
        """Create storage that uses fallback mode."""
        import src.core.storage as storage_module

        # Temporarily disable LMDB
        original_available = storage_module.LMDB_AVAILABLE
        storage_module.LMDB_AVAILABLE = False

        try:
            config = StorageConfig(path=temp_dir, map_size=10 * 1024 * 1024)
            s = LMDBStorage(config)
            yield s
            s.close()
        finally:
            storage_module.LMDB_AVAILABLE = original_available

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d, ignore_errors=True)

    def test_fallback_put_get(self, fallback_storage):
        """Test put/get in fallback mode."""
        with fallback_storage.write() as txn:
            fallback_storage.put(txn, b"key", b"value")

        with fallback_storage.read() as txn:
            assert fallback_storage.get(txn, b"key") == b"value"

    def test_fallback_delete(self, fallback_storage):
        """Test delete in fallback mode."""
        with fallback_storage.write() as txn:
            fallback_storage.put(txn, b"key", b"value")

        with fallback_storage.write() as txn:
            result = fallback_storage.delete(txn, b"key")
            assert result

        with fallback_storage.read() as txn:
            assert fallback_storage.get(txn, b"key") is None

    def test_fallback_delete_nonexistent(self, fallback_storage):
        """Test delete of non-existent key in fallback mode."""
        with fallback_storage.write() as txn:
            result = fallback_storage.delete(txn, b"nonexistent")
            assert not result

    def test_fallback_keys(self, fallback_storage):
        """Test key iteration in fallback mode."""
        with fallback_storage.write() as txn:
            fallback_storage.put(txn, b"prefix:a", b"1")
            fallback_storage.put(txn, b"prefix:b", b"2")

        with fallback_storage.read() as txn:
            keys = list(fallback_storage.keys(txn, b"prefix:"))
            assert len(keys) == 2

    def test_fallback_count(self, fallback_storage):
        """Test count in fallback mode."""
        with fallback_storage.write() as txn:
            fallback_storage.put(txn, b"key1", b"value1")

        with fallback_storage.read() as txn:
            assert fallback_storage.count(txn) >= 1

    def test_fallback_stats(self, fallback_storage):
        """Test stats in fallback mode."""
        stats = fallback_storage.stats
        assert stats["type"] == "fallback"
