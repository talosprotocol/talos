"""
Tests for the blockchain core module.
"""

import pytest
import time

from src.core.blockchain import Block, Blockchain, calculate_merkle_root


class TestBlock:
    """Tests for the Block class."""
    
    def test_block_creation(self):
        """Test that a block can be created with correct fields."""
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Hello"},
            previous_hash="0" * 64
        )
        
        assert block.index == 0
        assert block.data == {"message": "Hello"}
        assert block.previous_hash == "0" * 64
        assert block.nonce == 0
        assert len(block.hash) == 64  # SHA-256 hex
    
    def test_block_hash_changes_with_content(self):
        """Test that changing content changes the hash."""
        block1 = Block(
            index=0,
            timestamp=1000.0,
            data={"message": "Hello"},
            previous_hash="0" * 64
        )
        
        block2 = Block(
            index=0,
            timestamp=1000.0,
            data={"message": "World"},
            previous_hash="0" * 64
        )
        
        assert block1.hash != block2.hash
    
    def test_block_mining(self):
        """Test that mining produces valid hash with leading zeros."""
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Test"},
            previous_hash="0" * 64
        )
        
        block.mine(difficulty=2)
        
        assert block.hash.startswith("00")
        assert block.nonce >= 0
    
    def test_block_serialization(self):
        """Test block to/from dict conversion."""
        original = Block(
            index=1,
            timestamp=1000.0,
            data={"test": "data"},
            previous_hash="abc" + "0" * 61,
            nonce=42
        )
        original.hash = original.calculate_hash()
        
        data = original.model_dump()
        restored = Block.model_validate(data)
        
        assert restored.index == original.index
        assert restored.timestamp == original.timestamp
        assert restored.data == original.data
        assert restored.previous_hash == original.previous_hash
        assert restored.nonce == original.nonce
        assert restored.hash == original.hash


class TestBlockchain:
    """Tests for the Blockchain class."""
    
    def test_blockchain_creation(self):
        """Test blockchain initializes with genesis block."""
        bc = Blockchain(difficulty=1)
        
        assert len(bc) == 1
        assert bc.chain[0].index == 0
        assert bc.chain[0].previous_hash == "0" * 64
    
    def test_add_and_mine_data(self):
        """Test adding data and mining a block."""
        bc = Blockchain(difficulty=1)
        
        bc.add_data({"message": "Test 1"})
        bc.add_data({"message": "Test 2"})
        
        block = bc.mine_pending()
        
        assert block is not None
        assert len(bc) == 2
        assert block.index == 1
        assert len(bc.pending_data) == 0
    
    def test_chain_validation(self):
        """Test that a valid chain passes validation."""
        bc = Blockchain(difficulty=1)
        
        bc.add_data({"message": "Block 1"})
        bc.mine_pending()
        
        bc.add_data({"message": "Block 2"})
        bc.mine_pending()
        
        assert bc.is_chain_valid()
    
    def test_tampered_chain_fails_validation(self):
        """Test that tampering invalidates the chain."""
        bc = Blockchain(difficulty=1)
        
        bc.add_data({"message": "Block 1"})
        bc.mine_pending()
        
        # Tamper with the block
        bc.chain[1].data = {"message": "Tampered!"}
        
        assert not bc.is_chain_valid()
    
    def test_get_messages(self):
        """Test retrieving messages from blockchain."""
        bc = Blockchain(difficulty=1)
        
        bc.add_data({"msg": "Hello"})
        bc.add_data({"msg": "World"})
        bc.mine_pending()
        
        messages = bc.get_messages()
        
        assert len(messages) == 2
        assert messages[0]["msg"] == "Hello"
        assert messages[1]["msg"] == "World"
    
    def test_blockchain_serialization(self):
        """Test blockchain to/from dict conversion."""
        bc = Blockchain(difficulty=1)
        
        bc.add_data({"test": "data"})
        bc.mine_pending()
        
        data = bc.to_dict()
        restored = Blockchain.from_dict(data)
        
        assert len(restored) == len(bc)
        assert restored.difficulty == bc.difficulty


class TestMerkleTree:
    """Tests for Merkle tree functionality."""
    
    def test_empty_merkle_root(self):
        """Test merkle root of empty list."""
        root = calculate_merkle_root([])
        assert len(root) == 64  # SHA-256 of empty
    
    def test_single_item_merkle_root(self):
        """Test merkle root of single item."""
        root = calculate_merkle_root([b"hello"])
        assert len(root) == 64
    
    def test_merkle_root_consistency(self):
        """Test same data produces same root."""
        data = [b"one", b"two", b"three"]
        
        root1 = calculate_merkle_root(data)
        root2 = calculate_merkle_root(data)
        
        assert root1 == root2
    
    def test_merkle_root_changes_with_data(self):
        """Test different data produces different root."""
        root1 = calculate_merkle_root([b"one", b"two"])
        root2 = calculate_merkle_root([b"one", b"three"])
        
        assert root1 != root2
