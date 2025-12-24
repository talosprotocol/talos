"""
Tests for production blockchain features.

Tests covering:
- Atomic persistence
- Block size limits
- Chain indexing
- Chain synchronization
- Merkle proofs
- Fork resolution
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.blockchain import (
    Block,
    Blockchain,
    BlockchainError,
    calculate_merkle_root,
    generate_merkle_path,
    MAX_SINGLE_ITEM_SIZE,
)
from src.core.sync import (
    ChainSynchronizer,
    SyncState,
    SyncProgress,
)


class TestAtomicPersistence:
    """Tests for atomic save/load operations."""
    
    def test_save_creates_file(self):
        """Test that save creates the blockchain file."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"test": "message"})
        bc.mine_pending()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "blockchain.json"
            bc.save(path)
            
            assert path.exists()
            
            # Verify it's valid JSON
            with open(path) as f:
                data = json.load(f)
            assert "chain" in data
            assert len(data["chain"]) == 2  # genesis + 1
    
    def test_save_load_roundtrip(self):
        """Test that save/load preserves blockchain state."""
        bc = Blockchain(difficulty=1)
        for i in range(5):
            bc.add_data({"message": f"msg_{i}"})
        bc.mine_pending()
        bc.add_data({"pending": "data"})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "blockchain.json"
            bc.save(path)
            
            loaded = Blockchain.load(path)
            
            assert len(loaded) == len(bc)
            assert loaded.latest_block.hash == bc.latest_block.hash
            assert len(loaded.pending_data) == 1
            assert loaded.pending_data[0]["pending"] == "data"
    
    def test_save_atomic_no_partial_writes(self):
        """Test that failed saves don't leave partial files."""
        bc = Blockchain(difficulty=1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "blockchain.json"
            
            # Save normally first
            bc.save(path)
            original_content = path.read_text()
            
            # Now make blockchain un-serializable
            bc.pending_data.append({"bad": object()})
            
            with pytest.raises(Exception):
                bc.save(path)
            
            # Original file should still be intact
            assert path.exists()
            assert path.read_text() == original_content
    
    def test_load_nonexistent_raises(self):
        """Test that loading nonexistent file raises error."""
        with pytest.raises(BlockchainError):
            Blockchain.load("/nonexistent/path.json")
    
    def test_load_invalid_json_raises(self):
        """Test that loading invalid JSON raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "blockchain.json"
            path.write_text("not valid json {{{")
            
            with pytest.raises(BlockchainError):
                Blockchain.load(path)


class TestBlockSizeLimits:
    """Tests for block size and mempool limits."""
    
    def test_large_data_rejected(self):
        """Test that oversized data is rejected."""
        bc = Blockchain(difficulty=1)
        
        # Create data larger than MAX_SINGLE_ITEM_SIZE
        large_data = {"data": "x" * (MAX_SINGLE_ITEM_SIZE + 1000)}
        
        result = bc.add_data(large_data)
        assert result is False
        assert len(bc.pending_data) == 0
    
    def test_normal_data_accepted(self):
        """Test that normal-sized data is accepted."""
        bc = Blockchain(difficulty=1)
        
        result = bc.add_data({"message": "hello world"})
        assert result is True
        assert len(bc.pending_data) == 1
    
    def test_mempool_limit_enforced(self):
        """Test that mempool doesn't exceed limit."""
        bc = Blockchain(difficulty=1, max_pending=5)
        
        for i in range(10):
            bc.add_data({"i": i})
        
        # Only 5 should be accepted
        assert len(bc.pending_data) == 5
    
    def test_block_splits_large_pending(self):
        """Test that mining creates appropriately sized blocks."""
        bc = Blockchain(difficulty=1, max_block_size=1000)
        
        # Add data until total exceeds block size
        for i in range(100):
            bc.add_data({"index": i, "data": "x" * 50})
        
        initial_pending = len(bc.pending_data)
        block = bc.mine_pending()
        
        # Should have mined some, but left overflow
        assert block is not None
        assert len(bc.pending_data) < initial_pending
        assert block.size <= bc.max_block_size + 500  # Allow some overhead


class TestBlockIndexing:
    """Tests for O(1) block lookup."""
    
    def test_get_block_by_hash(self):
        """Test block retrieval by hash."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"test": "data"})
        block = bc.mine_pending()
        
        found = bc.get_block_by_hash(block.hash)
        assert found is not None
        assert found.hash == block.hash
    
    def test_get_block_by_height(self):
        """Test block retrieval by height."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"test": "data"})
        bc.mine_pending()
        
        genesis = bc.get_block_by_height(0)
        assert genesis is not None
        assert genesis.data.get("type") == "system"
        
        block1 = bc.get_block_by_height(1)
        assert block1 is not None
        assert "messages" in block1.data
    
    def test_get_message_block(self):
        """Test finding block by message ID."""
        bc = Blockchain(difficulty=1)
        msg_id = "test-message-123"
        bc.add_data({"id": msg_id, "content": "hello"})
        block = bc.mine_pending()
        
        found = bc.get_message_block(msg_id)
        assert found is not None
        assert found.hash == block.hash
    
    def test_index_rebuilt_on_load(self):
        """Test that indexes are rebuilt when loading."""
        bc = Blockchain(difficulty=1)
        msg_id = "persist-test-456"
        bc.add_data({"id": msg_id, "content": "test"})
        bc.mine_pending()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "blockchain.json"
            bc.save(path)
            
            loaded = Blockchain.load(path)
            
            # Indexes should work
            assert loaded.get_block_by_hash(bc.latest_block.hash) is not None
            assert loaded.get_message_block(msg_id) is not None


class TestChainStatus:
    """Tests for chain status and comparison."""
    
    def test_get_status(self):
        """Test chain status generation."""
        bc = Blockchain(difficulty=2)
        bc.add_data({"test": "data"})
        bc.mine_pending()
        
        status = bc.get_status()
        
        assert status.height == 1
        assert status.latest_hash == bc.latest_block.hash
        assert status.genesis_hash == bc.chain[0].hash
        assert status.difficulty == 2
        assert status.total_work > 0
    
    def test_should_accept_chain_more_work(self):
        """Test that chains with more work are accepted."""
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)
        
        # Make bc2 longer
        for i in range(5):
            bc2.add_data({"i": i})
            bc2.mine_pending()
        
        # bc1 has same genesis
        bc1.chain[0] = bc2.chain[0]
        bc1._rebuild_index()
        
        status2 = bc2.get_status()
        assert bc1.should_accept_chain(status2) is True
    
    def test_should_not_accept_less_work(self):
        """Test that chains with less work are rejected."""
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)
        
        # Make bc1 longer
        for i in range(5):
            bc1.add_data({"i": i})
            bc1.mine_pending()
        
        status2 = bc2.get_status()
        assert bc1.should_accept_chain(status2) is False
    
    def test_should_not_accept_different_genesis(self):
        """Test that different genesis chains are rejected."""
        bc1 = Blockchain(difficulty=1)
        bc2 = Blockchain(difficulty=1)  # Different genesis (created at different time)
        
        for i in range(5):
            bc2.add_data({"i": i})
            bc2.mine_pending()
        
        status2 = bc2.get_status()
        # Different genesis, should reject
        assert bc1.should_accept_chain(status2) is False


class TestChainReplacement:
    """Tests for chain replacement and fork resolution."""
    
    def test_replace_valid_longer_chain(self):
        """Test replacing with valid longer chain."""
        bc = Blockchain(difficulty=1)
        
        # Create a longer valid chain with same genesis
        new_chain = [bc.chain[0]]  # Same genesis
        for i in range(3):
            block = Block(
                index=len(new_chain),
                timestamp=1000.0 + i,
                data={"messages": [{"i": i}]},
                previous_hash=new_chain[-1].hash
            )
            block.mine(1)
            new_chain.append(block)
        
        result = bc.replace_chain(new_chain)
        assert result is True
        assert len(bc) == 4
    
    def test_reject_invalid_chain(self):
        """Test rejecting chain with broken links."""
        bc = Blockchain(difficulty=1)
        original_len = len(bc)
        
        # Create invalid chain (broken previous_hash)
        new_chain = [bc.chain[0]]
        block = Block(
            index=1,
            timestamp=1000.0,
            data={"messages": []},
            previous_hash="invalid_hash"
        )
        block.mine(1)
        new_chain.append(block)
        
        result = bc.replace_chain(new_chain)
        assert result is False
        assert len(bc) == original_len
    
    def test_reject_shorter_chain(self):
        """Test rejecting chain with less work."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"test": "data"})
        bc.mine_pending()
        bc.add_data({"test": "data2"})
        bc.mine_pending()
        
        # Try to replace with just genesis
        new_chain = [bc.chain[0]]
        
        result = bc.replace_chain(new_chain)
        assert result is False
        assert len(bc) == 3


class TestMerkleProofs:
    """Tests for Merkle proof generation and verification."""
    
    def test_calculate_merkle_root(self):
        """Test Merkle root calculation."""
        data = [b"item1", b"item2", b"item3", b"item4"]
        root = calculate_merkle_root(data)
        
        assert len(root) == 64  # SHA-256 hex
        
        # Root should change if data changes
        root2 = calculate_merkle_root([b"item1", b"item2", b"item3", b"modified"])
        assert root != root2
    
    def test_merkle_root_consistency(self):
        """Test that same data produces same root."""
        data = [b"a", b"b", b"c"]
        
        root1 = calculate_merkle_root(data)
        root2 = calculate_merkle_root(data)
        
        assert root1 == root2
    
    def test_generate_merkle_path(self):
        """Test Merkle path generation."""
        data = [b"item0", b"item1", b"item2", b"item3"]
        path = generate_merkle_path(data, 1)
        
        # Should have log2(4) = 2 levels
        assert len(path) == 2
        
        # Each element should be (hash, position)
        for sibling_hash, position in path:
            assert len(sibling_hash) == 64
            assert position in ("left", "right")
    
    def test_get_merkle_proof(self):
        """Test Merkle proof generation from blockchain."""
        bc = Blockchain(difficulty=1)
        msg_id = "proof-test-789"
        bc.add_data({"id": msg_id, "content": "test1"})
        bc.add_data({"id": "other", "content": "test2"})
        bc.mine_pending()
        
        proof = bc.get_merkle_proof(msg_id)
        
        assert proof is not None
        assert proof.block_hash == bc.latest_block.hash
        assert proof.block_height == 1
    
    def test_merkle_proof_verification(self):
        """Test Merkle proof verification."""
        bc = Blockchain(difficulty=1)
        
        # Add multiple messages
        for i in range(4):
            bc.add_data({"id": f"msg_{i}", "value": i})
        bc.mine_pending()
        
        # Get and verify proof for middle message
        proof = bc.get_merkle_proof("msg_1")
        
        assert proof is not None
        # Proof should verify against the block's merkle root
        assert proof.merkle_root == bc.latest_block.merkle_root


class TestChainSynchronizer:
    """Tests for chain synchronization."""
    
    def test_sync_state_transitions(self):
        """Test sync state machine."""
        bc = Blockchain(difficulty=1)
        sync = ChainSynchronizer(bc)
        
        assert sync.is_syncing is False
        
        progress = SyncProgress(
            state=SyncState.DOWNLOADING,
            peer_id="test_peer",
            total_blocks=10
        )
        
        assert progress.progress == 0.0
        
        progress.received_blocks = 5
        assert progress.progress == 0.5
        assert progress.progress_percent == 50
    
    def test_get_status(self):
        """Test chain status for sync."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"test": "data"})
        bc.mine_pending()
        
        ChainSynchronizer(bc)
        status = bc.get_status()
        
        assert status.height == 1
        assert status.latest_hash == bc.latest_block.hash


class TestBlockValidation:
    """Tests for block validation."""
    
    def test_valid_block_passes(self):
        """Test that valid blocks pass validation."""
        block = Block(
            index=0,
            timestamp=1000.0,
            data={"test": "data"},
            previous_hash="0" * 64
        )
        block.mine(2)
        
        assert block.validate(2) is True
    
    def test_tampered_block_fails(self):
        """Test that tampered blocks fail validation."""
        block = Block(
            index=0,
            timestamp=1000.0,
            data={"test": "data"},
            previous_hash="0" * 64
        )
        block.mine(2)
        
        # Tamper with data
        block.data["test"] = "modified"
        
        assert block.validate(2) is False
    
    def test_wrong_difficulty_fails(self):
        """Test that blocks with wrong PoW fail."""
        block = Block(
            index=0,
            timestamp=1000.0,
            data={"test": "data"},
            previous_hash="0" * 64
        )
        block.mine(1)  # Mine with difficulty 1
        
        # Validate expects difficulty 3
        assert block.validate(3) is False


class TestDataValidator:
    """Tests for custom data validation."""
    
    def test_custom_validator_rejects(self):
        """Test that custom validator can reject data."""
        def validator(data):
            return "valid" in data
        
        bc = Blockchain(difficulty=1, validator=validator)
        
        assert bc.add_data({"valid": True}) is True
        assert bc.add_data({"invalid": True}) is False
        
        assert len(bc.pending_data) == 1
    
    def test_validator_allows_all_when_none(self):
        """Test that no validator accepts all data."""
        bc = Blockchain(difficulty=1)
        
        assert bc.add_data({"anything": "goes"}) is True
        assert bc.add_data({"no": "restrictions"}) is True
        
        assert len(bc.pending_data) == 2
