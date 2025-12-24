"""
Tests for optimized crypto functions and storage backend.
"""

import pytest
from src.core.crypto import (
    Wallet,
    batch_verify_signatures,
    verify_signature_cached,
    clear_key_cache,
)
from src.core.storage import (
    StorageConfig,
    LMDBStorage,
    BlockStorage,
    LMDB_AVAILABLE,
)


class TestBatchVerifySignatures:
    """Tests for batch signature verification."""
    
    def test_empty_batch(self):
        """Empty batch returns empty list."""
        result = batch_verify_signatures([])
        assert result == []
    
    def test_single_signature(self):
        """Single signature verification."""
        wallet = Wallet.generate("test")
        msg = b"Hello"
        sig = wallet.sign(msg)
        
        items = [(msg, sig, wallet.signing_keys.public_key)]
        results = batch_verify_signatures(items)
        
        assert results == [True]
    
    def test_multiple_valid(self):
        """Multiple valid signatures."""
        wallets = [Wallet.generate(f"test{i}") for i in range(5)]
        items = []
        
        for w in wallets:
            msg = f"Message from {w.name}".encode()
            sig = w.sign(msg)
            items.append((msg, sig, w.signing_keys.public_key))
        
        results = batch_verify_signatures(items)
        assert all(results)
    
    def test_mixed_valid_invalid(self):
        """Mix of valid and invalid signatures."""
        wallet = Wallet.generate("test")
        msg = b"Valid message"
        sig = wallet.sign(msg)
        
        items = [
            (msg, sig, wallet.signing_keys.public_key),  # Valid
            (b"wrong", sig, wallet.signing_keys.public_key),  # Invalid
        ]
        
        results = batch_verify_signatures(items)
        assert results == [True, False]
    
    def test_parallel_large_batch(self):
        """Large batch uses parallel verification."""
        wallet = Wallet.generate("test")
        items = []
        
        for i in range(10):
            msg = f"Message {i}".encode()
            sig = wallet.sign(msg)
            items.append((msg, sig, wallet.signing_keys.public_key))
        
        results = batch_verify_signatures(items, parallel=True)
        assert all(results)
    
    def test_sequential_mode(self):
        """Sequential verification mode."""
        wallet = Wallet.generate("test")
        msg = b"Test"
        sig = wallet.sign(msg)
        
        items = [(msg, sig, wallet.signing_keys.public_key)] * 5
        results = batch_verify_signatures(items, parallel=False)
        
        assert all(results)


class TestCachedVerification:
    """Tests for cached signature verification."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_key_cache()
    
    def test_cached_verification(self):
        """Cached verification works correctly."""
        wallet = Wallet.generate("test")
        msg = b"Hello"
        sig = wallet.sign(msg)
        
        # First call - populates cache
        result1 = verify_signature_cached(msg, sig, wallet.signing_keys.public_key)
        # Second call - uses cache
        result2 = verify_signature_cached(msg, sig, wallet.signing_keys.public_key)
        
        assert result1 is True
        assert result2 is True
    
    def test_invalid_signature_cached(self):
        """Invalid signature with cached key."""
        wallet = Wallet.generate("test")
        msg = b"Hello"
        
        result = verify_signature_cached(msg, b"x" * 64, wallet.signing_keys.public_key)
        assert result is False
    
    def test_clear_cache(self):
        """Cache can be cleared."""
        wallet = Wallet.generate("test")
        msg = b"Hello"
        sig = wallet.sign(msg)
        
        verify_signature_cached(msg, sig, wallet.signing_keys.public_key)
        clear_key_cache()
        
        # Should still work after clearing
        result = verify_signature_cached(msg, sig, wallet.signing_keys.public_key)
        assert result is True


class TestLMDBStorage:
    """Tests for LMDB storage backend."""
    
    def test_basic_put_get(self, tmp_path):
        """Basic put and get operations."""
        config = StorageConfig(path=str(tmp_path / "db"))
        storage = LMDBStorage(config)
        
        with storage.write() as txn:
            storage.put(txn, b"key1", b"value1")
        
        with storage.read() as txn:
            result = storage.get(txn, b"key1")
        
        assert result == b"value1"
        storage.close()
    
    def test_delete(self, tmp_path):
        """Delete operation."""
        config = StorageConfig(path=str(tmp_path / "db"))
        storage = LMDBStorage(config)
        
        with storage.write() as txn:
            storage.put(txn, b"key", b"value")
        
        with storage.write() as txn:
            storage.delete(txn, b"key")
        
        with storage.read() as txn:
            result = storage.get(txn, b"key")
        
        assert result is None
        storage.close()
    
    def test_exists(self, tmp_path):
        """Exists check."""
        config = StorageConfig(path=str(tmp_path / "db"))
        storage = LMDBStorage(config)
        
        with storage.write() as txn:
            storage.put(txn, b"exists", b"yes")
        
        with storage.read() as txn:
            assert storage.exists(txn, b"exists") is True
            assert storage.exists(txn, b"missing") is False
        
        storage.close()
    
    def test_count(self, tmp_path):
        """Count entries."""
        config = StorageConfig(path=str(tmp_path / "db"))
        storage = LMDBStorage(config)
        
        with storage.write() as txn:
            for i in range(10):
                storage.put(txn, f"key{i}".encode(), b"value")
        
        with storage.read() as txn:
            count = storage.count(txn)
        
        assert count == 10
        storage.close()
    
    def test_stats(self, tmp_path):
        """Storage statistics."""
        config = StorageConfig(path=str(tmp_path / "db"))
        storage = LMDBStorage(config)
        
        stats = storage.stats
        assert "entries" in stats
        
        storage.close()


class TestBlockStorage:
    """Tests for block storage."""
    
    def test_put_and_get_by_hash(self, tmp_path):
        """Store and retrieve block by hash."""
        config = StorageConfig(path=str(tmp_path / "blocks"))
        storage = BlockStorage(config)
        
        block = {
            "index": 0,
            "hash": "abc123",
            "previous_hash": "0" * 64,
            "data": {"messages": []},
        }
        
        storage.put_block(block)
        result = storage.get_block_by_hash("abc123")
        
        assert result["index"] == 0
        assert result["hash"] == "abc123"
        storage.close()
    
    def test_get_by_height(self, tmp_path):
        """Retrieve block by height."""
        config = StorageConfig(path=str(tmp_path / "blocks"))
        storage = BlockStorage(config)
        
        block = {
            "index": 5,
            "hash": "block5hash",
            "previous_hash": "prev",
            "data": {},
        }
        
        storage.put_block(block)
        result = storage.get_block_by_height(5)
        
        assert result["hash"] == "block5hash"
        storage.close()
    
    def test_batch_put(self, tmp_path):
        """Batch block storage."""
        config = StorageConfig(path=str(tmp_path / "blocks"))
        storage = BlockStorage(config)
        
        blocks = [
            {"index": i, "hash": f"hash{i}", "previous_hash": "prev", "data": {}}
            for i in range(10)
        ]
        
        count = storage.put_blocks_batch(blocks)
        assert count == 10
        
        # Verify all stored
        for i in range(10):
            result = storage.get_block_by_height(i)
            assert result is not None
        
        storage.close()
