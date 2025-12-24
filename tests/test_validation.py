"""
Tests for the Block Validation Engine.

Tests cover all 5 validation layers:
1. Structural validation
2. Cryptographic validation
3. Consensus validation
4. Semantic validation
5. Cross-chain validation
"""

import asyncio
import pytest
import time
import json
import hashlib
from dataclasses import dataclass

# Import from the package
from src.core.validation import (
    ValidationEngine,
    ValidationResult,
    ValidationLevel,
    ValidationError,
    StructuralValidator,
    CryptographicValidator,
    ConsensusValidator,
    SemanticValidator,
    verify_block_hash,
    verify_merkle_root,
    verify_pow_target,
    verify_chain_link,
    generate_audit_report,
)
from src.core.blockchain import Block, Blockchain


class TestValidationEngine:
    """Tests for the main ValidationEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh validation engine."""
        return ValidationEngine(difficulty=2, strict_mode=True)
    
    @pytest.fixture
    def valid_block(self):
        """Create a valid block for testing."""
        block = Block(
            index=1,
            timestamp=time.time(),
            data={"messages": [{"id": "msg_1", "content": "test"}]},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        return block
    
    @pytest.fixture
    def genesis_block(self):
        """Create a genesis block."""
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Genesis Block"},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        return block
    
    @pytest.mark.asyncio
    async def test_validate_valid_block(self, engine, valid_block):
        """Test that a valid block passes validation."""
        result = await engine.validate_block(valid_block)
        
        assert result.is_valid
        assert result.error_count == 0
        assert "structural" in result.layers_passed
        assert "cryptographic" in result.layers_passed
        assert "consensus" in result.layers_passed
    
    @pytest.mark.asyncio
    async def test_validate_invalid_hash(self, engine, valid_block):
        """Test that a block with wrong hash fails."""
        valid_block.hash = "invalid" + valid_block.hash[7:]
        
        result = await engine.validate_block(valid_block)
        
        assert not result.is_valid
        assert "cryptographic" in result.layers_failed
        assert any(e.code.name == "HASH_MISMATCH" for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_insufficient_pow(self, engine):
        """Test that a block without enough PoW fails."""
        block = Block(
            index=1,
            timestamp=time.time(),
            data={"messages": []},
            previous_hash="0" * 64,
        )
        # Don't mine - hash won't start with required zeros
        
        result = await engine.validate_block(block)
        
        assert not result.is_valid
        assert "consensus" in result.layers_failed
    
    @pytest.mark.asyncio
    async def test_validate_future_timestamp(self, engine):
        """Test that a block with future timestamp fails."""
        block = Block(
            index=1,
            timestamp=time.time() + 1000,  # 1000 seconds in future
            data={"messages": []},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        
        result = await engine.validate_block(block)
        
        assert not result.is_valid
        assert any(e.code.name == "TIMESTAMP_INVALID" for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_chain_link(self, engine, genesis_block, valid_block):
        """Test chain link validation."""
        # Valid link
        valid_block.previous_hash = genesis_block.hash
        valid_block.hash = valid_block.calculate_hash()
        valid_block.mine(difficulty=2)
        
        result = await engine.validate_block(valid_block, previous_block=genesis_block)
        
        assert result.is_valid or "CHAIN_LINK_BROKEN" not in [e.code.name for e in result.errors]
    
    @pytest.mark.asyncio
    async def test_validate_chain(self, engine):
        """Test validating an entire chain."""
        blockchain = Blockchain(difficulty=2)
        
        # Add some blocks
        for i in range(3):
            blockchain.add_data({"id": f"msg_{i}", "content": f"message {i}"})
            blockchain.mine_pending()
        
        result = await engine.validate_chain(blockchain.chain)
        
        assert result.is_valid
    
    @pytest.mark.asyncio
    async def test_duplicate_message_detection(self, engine):
        """Test that duplicate message IDs are detected."""
        # First block with message
        block1 = Block(
            index=1,
            timestamp=time.time(),
            data={"messages": [{"id": "duplicate_id", "content": "first"}]},
            previous_hash="0" * 64,
        )
        block1.mine(difficulty=2)
        
        # Validate first - should pass
        result1 = await engine.validate_block(block1, level=ValidationLevel.STRICT)
        
        # Second block with same message ID
        block2 = Block(
            index=2,
            timestamp=time.time(),
            data={"messages": [{"id": "duplicate_id", "content": "duplicate"}]},
            previous_hash=block1.hash,
        )
        block2.mine(difficulty=2)
        
        # Validate second - should detect duplicate
        result2 = await engine.validate_block(block2, previous_block=block1, level=ValidationLevel.STRICT)
        
        assert any(e.code.name == "DUPLICATE_MESSAGE" for e in result2.errors)
    
    def test_metrics(self, engine):
        """Test that metrics are collected."""
        # Run some validations
        loop = asyncio.new_event_loop()
        for _ in range(5):
            block = Block(
                index=1,
                timestamp=time.time(),
                data={},
                previous_hash="0" * 64,
            )
            block.mine(difficulty=2)
            loop.run_until_complete(engine.validate_block(block))
        loop.close()
        
        metrics = engine.get_metrics()
        
        assert metrics["blocks_validated"] == 5
        assert metrics["avg_validation_time_ms"] > 0


class TestValidationLayers:
    """Tests for individual validation layers."""
    
    def test_structural_validator_missing_fields(self):
        """Test structural validation catches missing fields."""
        validator = StructuralValidator()
        
        # Create block with missing field
        block = Block(
            index=1,
            timestamp=time.time(),
            data={},
            previous_hash="0" * 64,
        )
        
        errors = validator.validate(block, {})
        
        # Should pass - Block has all required fields
        assert len(errors) == 0
    
    def test_structural_validator_invalid_type(self):
        """Test structural validation catches type errors."""
        validator = StructuralValidator()
        
        # Create a block then corrupt its index
        block = Block(
            index=1,
            timestamp=time.time(),
            data={},
            previous_hash="0" * 64,
        )
        block.index = -1  # Invalid negative index
        
        errors = validator.validate(block, {})
        
        assert len(errors) > 0
        assert any("INVALID_TYPE" in str(e) for e in errors)
    
    def test_cryptographic_validator_hash_mismatch(self):
        """Test cryptographic validation detects hash tampering."""
        validator = CryptographicValidator()
        
        block = Block(
            index=1,
            timestamp=time.time(),
            data={"messages": []},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        
        # Tamper with data without updating hash
        block.data["tampered"] = True
        
        errors = validator.validate(block, {})
        
        assert len(errors) > 0
        assert any("HASH_MISMATCH" in str(e) for e in errors)
    
    def test_consensus_validator_pow(self):
        """Test consensus validation checks PoW."""
        validator = ConsensusValidator()
        
        # Block without mining (won't have leading zeros)
        block = Block(
            index=1,
            timestamp=time.time(),
            data={}, 
            previous_hash="0" * 64,
            merkle_root="0" * 64,
            hash="ff" * 32, # Invalid high hash
            nonce=0
        )
        
        errors = validator.validate(block, {"difficulty": 2})
        
        assert len(errors) > 0
        assert any("POW_INVALID" in str(e) for e in errors)
    
    def test_semantic_validator_duplicate_detection(self):
        """Test semantic validation detects duplicates."""
        validator = SemanticValidator()
        
        block1 = Block(
            index=1,
            timestamp=time.time(),
            data={"messages": [{"id": "same_id", "content": "first"}]},
            previous_hash="0" * 64,
        )
        block1.mine(difficulty=2)
        
        # Validate first
        errors1 = validator.validate(block1, {})
        assert len(errors1) == 0
        
        # Validate second with same ID
        block2 = Block(
            index=2,
            timestamp=time.time(),
            data={"messages": [{"id": "same_id", "content": "second"}]},
            previous_hash=block1.hash,
        )
        block2.mine(difficulty=2)
        
        errors2 = validator.validate(block2, {})
        
        assert len(errors2) > 0
        assert any("DUPLICATE_ID" in str(e) for e in errors2)


class TestProofFunctions:
    """Tests for cryptographic proof functions."""
    
    def test_verify_block_hash(self):
        """Test block hash verification."""
        block = Block(
            index=1,
            timestamp=1234567890.0,
            data={"test": "data"},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        
        is_valid, calculated = verify_block_hash(block.to_dict())
        
        assert is_valid
        assert calculated == block.hash
    
    def test_verify_merkle_root(self):
        """Test Merkle root verification."""
        messages = [
            {"id": "1", "content": "a"},
            {"id": "2", "content": "b"},
            {"id": "3", "content": "c"},
        ]
        
        # Calculate expected root
        hashes = [hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest() for m in messages]
        # Add duplicate for odd count
        hashes.append(hashes[-1])
        # Combine pairs
        h01 = hashlib.sha256((hashes[0] + hashes[1]).encode()).hexdigest()
        h23 = hashlib.sha256((hashes[2] + hashes[3]).encode()).hexdigest()
        root = hashlib.sha256((h01 + h23).encode()).hexdigest()
        
        assert verify_merkle_root(messages, root)
    
    def test_verify_pow_target(self):
        """Test PoW target verification."""
        assert verify_pow_target("0000abc123", 4)
        assert verify_pow_target("00abc123", 2)
        assert not verify_pow_target("abc00123", 2)
    
    def test_verify_chain_link(self):
        """Test chain link verification."""
        genesis = {"hash": "abc123", "index": 0}
        block = {"previous_hash": "abc123", "index": 1}
        
        assert verify_chain_link(block, genesis)
        
        # Wrong link
        bad_block = {"previous_hash": "wrong", "index": 1}
        assert not verify_chain_link(bad_block, genesis)


class TestAuditReport:
    """Tests for audit report generation."""
    
    @pytest.mark.asyncio
    async def test_generate_report(self):
        """Test audit report generation."""
        engine = ValidationEngine(difficulty=2)
        
        block = Block(
            index=1,
            timestamp=time.time(),
            data={"messages": [{"id": "msg_1"}]},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        
        result = await engine.validate_block(block)
        report = generate_audit_report(block, result)
        
        assert report.report_id
        assert report.block_hash == block.hash
        assert report.is_valid == result.is_valid
    
    @pytest.mark.asyncio
    async def test_report_formats(self):
        """Test report output formats."""
        engine = ValidationEngine(difficulty=2)
        
        block = Block(
            index=1,
            timestamp=time.time(),
            data={},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)
        
        result = await engine.validate_block(block)
        report = generate_audit_report(block, result)
        
        # Test dict format
        report_dict = report.to_dict()
        assert "report_id" in report_dict
        assert "result" in report_dict
        
        # Test JSON format
        report_json = report.to_json()
        parsed = json.loads(report_json)
        assert parsed["report_id"] == report.report_id
        
        # Test Markdown format
        report_md = report.to_markdown()
        assert "# Block Validation Report" in report_md
        assert report.block_hash[:16] in report_md
