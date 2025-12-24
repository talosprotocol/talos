
import pytest
import asyncio
import tempfile
import os
import shutil
from pathlib import Path
from src.core.storage import StorageConfig, LMDBStorage, BlockStorage
from src.core.blockchain import Block

@pytest.fixture
def temp_db_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture
def storage_config(temp_db_path):
    return StorageConfig(path=temp_db_path)

@pytest.mark.asyncio
async def test_async_put_get(storage_config):
    storage = LMDBStorage(storage_config)
    try:
        await storage.put_async(b"key1", b"val1")
        val = await storage.get_async(b"key1")
        assert val == b"val1"
        
        # Verify sync access still works
        with storage.read() as txn:
            assert storage.get(txn, b"key1") == b"val1"
    finally:
        storage.close()

def test_block_storage_pydantic(storage_config):
    storage = BlockStorage(storage_config)
    try:
        block = Block(
            index=1,
            timestamp=1234567890.0,
            data={"msg": "test"},
            previous_hash="0" * 64,
            nonce=123
        )
        # Force hash calculation
        _ = block.hash
        
        # Test storing Pydantic object directly
        storage.put_block(block)
        
        # Test retrieval
        retrieved = storage.get_block_by_hash(block.hash)
        assert retrieved is not None
        assert retrieved["index"] == 1
        assert retrieved["hash"] == block.hash
        
        # Test height lookup
        retrieved_height = storage.get_block_by_height(1)
        assert retrieved_height["hash"] == block.hash
        
    finally:
        storage.close()

def test_batch_write_mixed(storage_config):
    storage = BlockStorage(storage_config)
    try:
        b1 = Block(index=1, timestamp=1.0, data={}, previous_hash="0"*64)
        _ = b1.hash
        
        b2 = {
            "index": 2,
            "timestamp": 2.0,
            "data": {},
            "previous_hash": b1.hash,
            "hash": "aabbcc",
            "merkle_root": ""
        }
        
        count = storage.put_blocks_batch([b1, b2])
        assert count == 2
        
        assert storage.get_block_by_height(1)["hash"] == b1.hash
        assert storage.get_block_by_height(2)["hash"] == "aabbcc"
        
    finally:
        storage.close()
