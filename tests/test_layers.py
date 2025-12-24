"""
Tests for validation layers.

These tests cover:
- StructuralValidator
- CryptographicValidator
- ConsensusValidator
- SemanticValidator
- CrossChainValidator
"""

import time
import pytest
from src.core.blockchain import Blockchain, Block
from src.core.validation.layers import (
    StructuralValidator,
    CryptographicValidator,
    ConsensusValidator,
    SemanticValidator,
    CrossChainValidator,
)


class TestStructuralValidator:
    """Tests for structural validation layer."""
    
    def test_valid_block(self):
        """Valid block passes structural validation."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"msg": "test"})
        bc.mine_pending()
        
        validator = StructuralValidator()
        errors = validator.validate(bc.chain[1], {})
        assert len(errors) == 0
    
    def test_genesis_block(self):
        """Genesis block passes validation."""
        bc = Blockchain(difficulty=1)
        
        validator = StructuralValidator()
        errors = validator.validate(bc.chain[0], {})
        assert len(errors) == 0
    
    def test_validator_name(self):
        """Validator has correct name."""
        validator = StructuralValidator()
        assert validator.name == "structural"


class TestCryptographicValidator:
    """Tests for cryptographic validation layer."""
    
    def test_valid_block_hash(self):
        """Block with valid hash passes."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"msg": "test"})
        bc.mine_pending()
        
        validator = CryptographicValidator()
        errors = validator.validate(bc.chain[1], {"difficulty": 1})
        assert len(errors) == 0
    
    def test_genesis_block(self):
        """Genesis block passes crypto validation."""
        bc = Blockchain(difficulty=1)
        
        validator = CryptographicValidator()
        errors = validator.validate(bc.chain[0], {"difficulty": 1})
        assert len(errors) == 0
    
    def test_validator_name(self):
        """Validator has correct name."""
        validator = CryptographicValidator()
        assert validator.name == "cryptographic"


class TestConsensusValidator:
    """Tests for consensus validation layer."""
    
    def test_valid_chain_link(self):
        """Valid chain link passes."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"msg": "test"})
        bc.mine_pending()
        
        validator = ConsensusValidator()
        context = {
            "difficulty": 1,
            "previous_block": bc.chain[0],
        }
        errors = validator.validate(bc.chain[1], context)
        assert len(errors) == 0
    
    def test_genesis_block(self):
        """Genesis block passes validation."""
        bc = Blockchain(difficulty=1)
        
        validator = ConsensusValidator()
        context = {"difficulty": 1, "previous_block": None}
        errors = validator.validate(bc.chain[0], context)
        assert len(errors) == 0
    
    def test_validator_name(self):
        """Validator has correct name."""
        validator = ConsensusValidator()
        assert validator.name == "consensus"
    
    def test_max_timestamp_drift(self):
        """Max timestamp drift is defined."""
        validator = ConsensusValidator()
        assert validator.MAX_TIMESTAMP_DRIFT == 300


class TestSemanticValidator:
    """Tests for semantic validation layer."""
    
    def test_valid_block(self):
        """Valid block passes semantic validation."""
        bc = Blockchain(difficulty=1)
        bc.add_data({"id": "msg1", "msg": "test"})
        bc.mine_pending()
        
        validator = SemanticValidator()
        errors = validator.validate(bc.chain[1], {})
        assert len(errors) == 0
    
    def test_reset(self):
        """Reset clears seen state."""
        validator = SemanticValidator()
        validator._seen_ids.add("test")
        validator._seen_nonces.add("nonce")
        
        validator.reset()
        
        assert len(validator._seen_ids) == 0
        assert len(validator._seen_nonces) == 0
    
    def test_validator_name(self):
        """Validator has correct name."""
        validator = SemanticValidator()
        assert validator.name == "semantic"


class TestCrossChainValidator:
    """Tests for cross-chain validation layer."""
    
    def test_always_passes(self):
        """Cross-chain validation always passes (placeholder)."""
        bc = Blockchain(difficulty=1)
        
        validator = CrossChainValidator()
        errors = validator.validate(bc.chain[0], {})
        assert len(errors) == 0
    
    def test_validator_name(self):
        """Validator has correct name."""
        validator = CrossChainValidator()
        assert validator.name == "cross_chain"
    
    def test_verify_anchor_is_async(self):
        """Verify anchor method exists."""
        validator = CrossChainValidator()
        assert hasattr(validator, "verify_anchor")
