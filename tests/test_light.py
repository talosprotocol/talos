"""
Tests for Light Client Blockchain.

Tests cover:
- BlockHeader creation and validation
- SPVProof verification
- LightBlockchain operations
- Header sync
- Persistence
"""

import pytest
import tempfile
from pathlib import Path

from src.core.light import (
    BlockHeader,
    SPVProof,
    LightBlockchain,
)
from src.core.blockchain import Blockchain, Block


class TestBlockHeader:
    """Tests for BlockHeader."""
    
    def test_create_header(self):
        """Test creating a block header."""
        header = BlockHeader(
            index=0,
            timestamp=1234567890.0,
            previous_hash="0" * 64,
            merkle_root="abc123",
            nonce=12345,
            hash="0" * 2 + "x" * 62,  # PoW with difficulty 2
            difficulty=2,
        )
        
        assert header.index == 0
        assert header.nonce == 12345
        assert header.validate_pow()
    
    def test_header_from_block(self):
        """Test creating header from full block."""
        # Create a full blockchain
        bc = Blockchain(difficulty=1)
        bc.add_data({"test": "message"})
        bc.mine_pending()
        
        block = bc.chain[-1]
        header = BlockHeader.from_block(block, difficulty=1)
        
        assert header.index == block.index
        assert header.hash == block.hash
        assert header.merkle_root == block.merkle_root
    
    def test_header_serialization(self):
        """Test header to_dict/from_dict."""
        header = BlockHeader(
            index=5,
            timestamp=1234567890.0,
            previous_hash="prev" * 16,
            merkle_root="root" * 16,
            nonce=999,
            hash="00" + "ab" * 31,
            difficulty=2,
        )
        
        data = header.to_dict()
        loaded = BlockHeader.from_dict(data)
        
        assert loaded.index == header.index
        assert loaded.hash == header.hash
        assert loaded.merkle_root == header.merkle_root
    
    def test_header_size(self):
        """Test header size is small."""
        header = BlockHeader(
            index=0,
            timestamp=1234567890.0,
            previous_hash="0" * 64,
            merkle_root="0" * 64,
            nonce=0,
            hash="0" * 64,
        )
        
        # Headers should be very small
        assert header.size < 500  # bytes
    
    def test_pow_validation(self):
        """Test proof-of-work validation."""
        # Valid PoW (starts with 00)
        valid = BlockHeader(
            index=0, timestamp=0, previous_hash="", merkle_root="",
            nonce=0, hash="00abc123" + "x" * 56, difficulty=2,
        )
        assert valid.validate_pow()
        
        # Invalid PoW
        invalid = BlockHeader(
            index=0, timestamp=0, previous_hash="", merkle_root="",
            nonce=0, hash="abc123" + "x" * 58, difficulty=2,
        )
        assert not invalid.validate_pow()


class TestSPVProof:
    """Tests for SPV proofs."""
    
    def test_simple_proof(self):
        """Test simple single-element proof."""
        # For a tree with just the data itself as root
        import hashlib
        data_hash = hashlib.sha256(b"test data").hexdigest()
        
        proof = SPVProof(
            data_hash=data_hash,
            block_hash="blockhash",
            block_height=5,
            merkle_root=data_hash,  # Single element tree
            merkle_path=[],  # No path needed
        )
        
        assert proof.verify()
    
    def test_two_element_proof(self):
        """Test proof with one sibling."""
        import hashlib
        
        data1 = hashlib.sha256(b"data1").hexdigest()
        data2 = hashlib.sha256(b"data2").hexdigest()
        root = hashlib.sha256((data1 + data2).encode()).hexdigest()
        
        # Prove data1 exists
        proof = SPVProof(
            data_hash=data1,
            block_hash="block",
            block_height=0,
            merkle_root=root,
            merkle_path=[(data2, "right")],
        )
        
        assert proof.verify()
    
    def test_invalid_proof(self):
        """Test invalid proof fails."""
        proof = SPVProof(
            data_hash="wronghash",
            block_hash="block",
            block_height=0,
            merkle_root="actualroot",
            merkle_path=[],
        )
        
        assert not proof.verify()
    
    def test_proof_serialization(self):
        """Test proof to_dict/from_dict."""
        proof = SPVProof(
            data_hash="datahash",
            block_hash="blockhash",
            block_height=10,
            merkle_root="merkleroot",
            merkle_path=[("sibling1", "left"), ("sibling2", "right")],
        )
        
        data = proof.to_dict()
        loaded = SPVProof.from_dict(data)
        
        assert loaded.data_hash == proof.data_hash
        assert loaded.merkle_path == proof.merkle_path


class TestLightBlockchain:
    """Tests for LightBlockchain."""
    
    @pytest.fixture
    def blockchain(self):
        """Create a test blockchain with blocks."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"msg": "hello"})
        bc.mine_pending()
        bc.add_data({"msg": "world"})
        bc.mine_pending()
        return bc
    
    def test_create_light_blockchain(self):
        """Test creating empty light blockchain."""
        light = LightBlockchain(difficulty=2)
        
        assert light.height == -1
        assert len(light) == 0
        assert light.latest_hash is None
    
    def test_from_full_blockchain(self, blockchain):
        """Test creating light client from full blockchain."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        assert len(light) == len(blockchain.chain)
        assert light.latest_hash == blockchain.chain[-1].hash
    
    def test_add_headers(self, blockchain):
        """Test adding headers manually."""
        light = LightBlockchain(difficulty=1)
        
        for block in blockchain.chain:
            header = BlockHeader.from_block(block, difficulty=1)
            result = light.add_header(header)
            assert result is True
        
        assert len(light) == len(blockchain.chain)
    
    def test_add_headers_batch(self, blockchain):
        """Test adding multiple headers at once."""
        light = LightBlockchain(difficulty=1)
        
        headers = [BlockHeader.from_block(b, difficulty=1) for b in blockchain.chain]
        added = light.add_headers(headers)
        
        assert added == len(blockchain.chain)
    
    def test_reject_invalid_header(self, blockchain):
        """Test that invalid headers are rejected."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        # Try to add header with wrong index
        bad_header = BlockHeader(
            index=999,  # Wrong index
            timestamp=0,
            previous_hash="0" * 64,
            merkle_root="0" * 64,
            nonce=0,
            hash="0" * 64,
            difficulty=1,
        )
        
        assert light.add_header(bad_header) is False
    
    def test_get_header(self, blockchain):
        """Test retrieving headers."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        header = light.get_header(0)
        assert header is not None
        assert header.index == 0
        
        header = light.get_header(1)
        assert header is not None
        assert header.index == 1
        
        # Out of range
        assert light.get_header(999) is None
    
    def test_get_header_by_hash(self, blockchain):
        """Test retrieving header by hash."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        target_hash = blockchain.chain[1].hash
        header = light.get_header_by_hash(target_hash)
        
        assert header is not None
        assert header.hash == target_hash
    
    def test_validate_chain(self, blockchain):
        """Test chain validation."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        assert light.validate_chain() is True
    
    def test_verify_spv_proof(self, blockchain):
        """Test SPV proof verification."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        # Create a valid proof
        block = blockchain.chain[-1]
        proof = SPVProof(
            data_hash=block.merkle_root,
            block_hash=block.hash,
            block_height=block.index,
            merkle_root=block.merkle_root,
            merkle_path=[],  # Single element
        )
        
        assert light.verify_spv_proof(proof) is True
        assert light.has_verified_data(block.merkle_root)
    
    def test_reject_invalid_spv_proof(self, blockchain):
        """Test invalid SPV proof rejection."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        # Proof for non-existent block
        proof = SPVProof(
            data_hash="fake",
            block_hash="nonexistent",
            block_height=999,
            merkle_root="fake",
            merkle_path=[],
        )
        
        assert light.verify_spv_proof(proof) is False
    
    def test_get_stats(self, blockchain):
        """Test getting statistics."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        stats = light.get_stats()
        
        assert stats["height"] == len(blockchain.chain) - 1
        assert stats["headers_count"] == len(blockchain.chain)
        assert "header_storage_bytes" in stats
        assert stats["difficulty"] == 1
    
    def test_sync_request(self, blockchain):
        """Test generating sync request."""
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        
        request = light.get_sync_request(batch_size=50)
        
        assert request["type"] == "GET_HEADERS"
        assert request["start_height"] == len(light)
        assert request["count"] == 50
    
    def test_proof_request(self):
        """Test generating proof request."""
        light = LightBlockchain(difficulty=1)
        
        request = light.get_proof_request("datahash123")
        
        assert request["type"] == "GET_MERKLE_PROOF"
        assert request["data_hash"] == "datahash123"
    
    def test_persistence(self, blockchain):
        """Test save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "light.json"
            
            # Save
            light1 = LightBlockchain.from_blockchain(blockchain, difficulty=1)
            light1.storage_path = path
            light1.save()
            
            # Load
            light2 = LightBlockchain(difficulty=1, storage_path=path)
            light2.load()
            
            assert len(light2) == len(light1)
            assert light2.latest_hash == light1.latest_hash
    
    def test_storage_reduction(self, blockchain):
        """Test that light client uses much less storage."""
        import json
        
        # Full blockchain size
        full_size = len(json.dumps([b.to_dict() for b in blockchain.chain]))
        
        # Light client size
        light = LightBlockchain.from_blockchain(blockchain, difficulty=1)
        light_size = sum(h.size for h in light.headers)
        
        # Light should be significantly smaller
        # (In practice, full blocks have data; headers don't)
        assert light_size < full_size
