"""
Additional tests for validation/engine.py to increase coverage.

Covers:
- Parallel validation
- Cross-chain validation with anchors
- Exception handling paths
- Edge cases for semantic validation
"""

import pytest
import time
import base64
from unittest.mock import patch

from src.core.validation.engine import (
    ValidationEngine,
    ValidationLevel,
    ValidationErrorCode,
    ValidationError,
    ValidationResult,
)
from src.core.blockchain import Block
from src.core.crypto import generate_signing_keypair, sign_message


class TestValidationEngineParallel:
    """Test parallel validation path."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine(difficulty=1)

    @pytest.fixture
    def valid_block(self):
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"messages": []},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=1)
        return block

    @pytest.mark.asyncio
    async def test_parallel_validation_passes(self, engine, valid_block):
        """Test that parallel validation works for valid blocks."""
        result = await engine.validate_block_parallel(valid_block)
        assert result.is_valid
        assert "structural" in result.layers_passed
        assert "cryptographic" in result.layers_passed
        assert "consensus" in result.layers_passed

    @pytest.mark.asyncio
    async def test_parallel_validation_structural_failure(self, engine):
        """Test parallel validation stops early on structural failure."""
        # Create malformed block
        block = Block(index=-1, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block.hash = "invalid"

        result = await engine.validate_block_parallel(block)
        assert not result.is_valid
        assert "structural" in result.layers_failed

    @pytest.mark.asyncio
    async def test_parallel_validation_with_semantic(self, engine):
        """Test parallel validation with semantic layer."""
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"messages": [{"id": "msg1", "sender": "alice", "nonce": "abc"}]},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=1)

        result = await engine.validate_block_parallel(
            block,
            level=ValidationLevel.STRICT
        )
        assert result.is_valid
        assert "semantic" in result.layers_passed


class TestValidationEngineCrossChain:
    """Test cross-chain / anchor validation."""

    @pytest.fixture
    def engine_with_anchors(self):
        # Generate trusted oracle key
        key_pair = generate_signing_keypair()
        oracle_hex = key_pair.public_key.hex()
        return ValidationEngine(
            difficulty=1,
            enable_cross_chain=True,
            trusted_anchors={oracle_hex}
        ), oracle_hex, key_pair.private_key

    @pytest.fixture
    def valid_block_with_anchor(self, engine_with_anchors):
        engine, oracle_hex, priv_key = engine_with_anchors

        # Create block first
        block = Block(index=0, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        # Create anchor signing the block hash
        statement = block.hash
        sig = sign_message(statement.encode(), priv_key)
        sig_b64 = base64.b64encode(sig).decode()

        # Add anchor to block data
        block.data = {
            "anchors": [{
                "oracle": oracle_hex,
                "signature": sig_b64,
                "statement": statement
            }]
        }
        block._calculate_hash()
        block.mine(difficulty=1)

        return block, engine

    @pytest.mark.asyncio
    async def test_cross_chain_validation_no_anchors(self, engine_with_anchors):
        """Test that blocks without anchors pass (anchors optional)."""
        engine, _, _ = engine_with_anchors
        block = Block(index=0, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        result = await engine.validate_block(
            block,
            level=ValidationLevel.PARANOID
        )
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_cross_chain_validation_invalid_anchor_type(self, engine_with_anchors):
        """Test that non-list anchors fail."""
        engine, _, _ = engine_with_anchors
        block = Block(index=0, timestamp=time.time(), data={"anchors": "not a list"}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        result = await engine.validate_block(
            block,
            level=ValidationLevel.PARANOID
        )
        assert not result.is_valid
        assert any(e.code == ValidationErrorCode.INVALID_TYPE for e in result.errors)

    @pytest.mark.asyncio
    async def test_cross_chain_validation_anchor_dict_type(self, engine_with_anchors):
        """Test that non-dict anchor entries fail."""
        engine, _, _ = engine_with_anchors
        block = Block(index=0, timestamp=time.time(), data={"anchors": ["not a dict"]}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        result = await engine.validate_block(
            block,
            level=ValidationLevel.PARANOID
        )
        assert not result.is_valid
        assert any(e.code == ValidationErrorCode.INVALID_TYPE for e in result.errors)

    @pytest.mark.asyncio
    async def test_cross_chain_validation_missing_anchor_fields(self, engine_with_anchors):
        """Test that anchors with missing fields fail."""
        engine, _, _ = engine_with_anchors
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"anchors": [{"oracle": "abc"}]},  # Missing signature and statement
            previous_hash="0" * 64
        )
        block.mine(difficulty=1)

        result = await engine.validate_block(
            block,
            level=ValidationLevel.PARANOID
        )
        assert not result.is_valid
        assert any(e.code == ValidationErrorCode.MISSING_FIELD for e in result.errors)

    @pytest.mark.asyncio
    async def test_cross_chain_validation_untrusted_oracle(self, engine_with_anchors):
        """Test that untrusted oracles are rejected."""
        engine, _, _ = engine_with_anchors
        block = Block(
            index=0,
            timestamp=time.time(),
            data={"anchors": [{
                "oracle": "untrusted_oracle_key_hex" * 4,
                "signature": base64.b64encode(b"fake_sig").decode(),
                "statement": "hash"
            }]},
            previous_hash="0" * 64
        )
        block.mine(difficulty=1)

        result = await engine.validate_block(
            block,
            level=ValidationLevel.PARANOID
        )
        assert not result.is_valid
        assert any(e.code == ValidationErrorCode.EXTERNAL_VERIFICATION_FAILED for e in result.errors)


class TestValidationEngineExceptionHandling:
    """Test exception handling paths."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine(difficulty=1)

    @pytest.mark.asyncio
    async def test_validate_block_exception_caught(self, engine):
        """Test that exceptions during validation are caught and reported."""
        block = Block(index=0, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        # Mock _validate_structural to raise an exception
        with patch.object(engine, '_validate_structural', side_effect=RuntimeError("Test error")):
            result = await engine.validate_block(block)
            assert not result.is_valid
            assert "system" in result.layers_failed
            assert any(e.code == ValidationErrorCode.MALFORMED_BLOCK for e in result.errors)

    @pytest.mark.asyncio
    async def test_parallel_validation_exception_caught(self, engine):
        """Test that exceptions during parallel validation are caught."""
        block = Block(index=0, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        with patch.object(engine, '_validate_structural', side_effect=RuntimeError("Test error")):
            result = await engine.validate_block_parallel(block)
            assert not result.is_valid


class TestValidationEngineEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def engine(self):
        return ValidationEngine(difficulty=1)

    def test_validation_result_to_dict(self):
        """Test ValidationResult.to_dict serialization."""
        error = ValidationError(
            code=ValidationErrorCode.HASH_MISMATCH,
            message="Test error",
            layer="test"
        )
        result = ValidationResult(is_valid=False, errors=[error])
        data = result.to_dict()

        assert "errors" in data
        assert len(data["errors"]) == 1
        assert data["errors"][0]["code"] == 200
        assert data["errors"][0]["code_name"] == "HASH_MISMATCH"

    def test_validation_result_properties(self):
        """Test ValidationResult properties."""
        error = ValidationError(
            code=ValidationErrorCode.HASH_MISMATCH,
            message="Test error",
            layer="test"
        )
        result = ValidationResult(is_valid=False, errors=[error])

        assert result.error_count == 1
        assert result.first_error.code == ValidationErrorCode.HASH_MISMATCH

    def test_validation_result_no_errors(self):
        """Test ValidationResult with no errors."""
        result = ValidationResult(is_valid=True)
        assert result.error_count == 0
        assert result.first_error is None

    @pytest.mark.asyncio
    async def test_validate_chain_from_genesis(self, engine):
        """Test chain validation starting from genesis."""
        block0 = Block(index=0, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block0.mine(difficulty=1)

        block1 = Block(index=1, timestamp=time.time(), data={}, previous_hash=block0.hash)
        block1.mine(difficulty=1)

        result = await engine.validate_chain([block0, block1], from_genesis=True)
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_chain_failure(self, engine):
        """Test chain validation with invalid block."""
        block0 = Block(index=0, timestamp=time.time(), data={}, previous_hash="0" * 64)
        block0.mine(difficulty=1)

        block1 = Block(index=1, timestamp=time.time(), data={}, previous_hash="invalid_hash")
        block1.mine(difficulty=1)

        result = await engine.validate_chain([block0, block1], from_genesis=True)
        assert not result.is_valid

    def test_reset_state(self, engine):
        """Test state reset clears seen messages/nonces."""
        engine._seen_message_ids.add("msg1")
        engine._seen_nonces.add(("sender", b"nonce"))

        engine.reset_state()

        assert len(engine._seen_message_ids) == 0
        assert len(engine._seen_nonces) == 0

    def test_get_metrics(self, engine):
        """Test metrics retrieval."""
        engine.blocks_validated = 100
        engine.blocks_rejected = 10
        engine.validation_times = [1.0, 2.0, 3.0]

        metrics = engine.get_metrics()

        assert metrics["blocks_validated"] == 100
        assert metrics["blocks_rejected"] == 10
        assert metrics["rejection_rate"] == 0.1
        assert metrics["avg_validation_time_ms"] == 2.0
        assert metrics["total_validation_time_ms"] == 6.0

    @pytest.mark.asyncio
    async def test_semantic_validation_messages_not_list(self, engine):
        """Test semantic validation fails when messages is not a list."""
        block = Block(index=0, timestamp=time.time(), data={"messages": "not a list"}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        result = await engine.validate_block(block, level=ValidationLevel.STRICT)
        assert not result.is_valid
        assert any(e.code == ValidationErrorCode.MESSAGE_FORMAT_INVALID for e in result.errors)

    @pytest.mark.asyncio
    async def test_semantic_validation_message_not_dict(self, engine):
        """Test semantic validation fails when message is not a dict."""
        block = Block(index=0, timestamp=time.time(), data={"messages": ["not a dict"]}, previous_hash="0" * 64)
        block.mine(difficulty=1)

        result = await engine.validate_block(block, level=ValidationLevel.STRICT)
        assert not result.is_valid
        assert any(e.code == ValidationErrorCode.MESSAGE_FORMAT_INVALID for e in result.errors)
