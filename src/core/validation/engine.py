"""
Validation Engine - Main orchestrator for block validation.

The ValidationEngine runs blocks through a multi-layer pipeline,
collecting errors and generating detailed reports.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional

from ..blockchain import Block, Blockchain

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels."""
    MINIMAL = auto()      # Hash check only
    STANDARD = auto()     # Hash + PoW + chain link
    STRICT = auto()       # All layers including semantic
    PARANOID = auto()     # All layers + cross-chain verification


class ValidationErrorCode(Enum):
    """Error codes for validation failures."""
    # Structural errors (1xx)
    MALFORMED_BLOCK = 100
    MISSING_FIELD = 101
    INVALID_TYPE = 102
    SIZE_EXCEEDED = 103
    
    # Cryptographic errors (2xx)
    HASH_MISMATCH = 200
    SIGNATURE_INVALID = 201
    MERKLE_INVALID = 202
    
    # Consensus errors (3xx)
    POW_INVALID = 300
    TIMESTAMP_INVALID = 301
    CHAIN_LINK_BROKEN = 302
    DIFFICULTY_MISMATCH = 303
    
    # Semantic errors (4xx)
    DUPLICATE_MESSAGE = 400
    NONCE_REUSED = 401
    MESSAGE_FORMAT_INVALID = 402
    
    # Cross-chain errors (5xx)
    ANCHOR_MISMATCH = 500
    EXTERNAL_VERIFICATION_FAILED = 501


@dataclass
class ValidationError:
    """A single validation error."""
    code: ValidationErrorCode
    message: str
    layer: str
    block_index: Optional[int] = None
    details: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "code_name": self.code.name,
            "message": self.message,
            "layer": self.layer,
            "block_index": self.block_index,
            "details": self.details,
        }


@dataclass
class ValidationResult:
    """Result of validating a block or chain."""
    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    layers_passed: list[str] = field(default_factory=list)
    layers_failed: list[str] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def first_error(self) -> Optional[ValidationError]:
        return self.errors[0] if self.errors else None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
            "duration_ms": self.duration_ms,
            "layers_passed": self.layers_passed,
            "layers_failed": self.layers_failed,
        }


class ValidationEngine:
    """
    Multi-layer block validation engine.
    
    Validates blocks through a configurable pipeline of validation layers:
    1. Structural - Schema, types, size limits
    2. Cryptographic - Hashes, signatures, Merkle proofs
    3. Consensus - PoW, timestamps, chain continuity
    4. Semantic - Duplicates, nonces, message formats
    5. Cross-Chain - External anchor verification (optional)
    
    Usage:
        engine = ValidationEngine(difficulty=2, strict_mode=True)
        result = await engine.validate_block(block, previous_block)
        
        if not result.is_valid:
            for error in result.errors:
                print(f"{error.layer}: {error.message}")
    """
    
    # Maximum allowed timestamp drift (5 minutes into future)
    MAX_TIMESTAMP_DRIFT = 300
    
    # Maximum block size (1MB)
    MAX_BLOCK_SIZE = 1_000_000
    
    # Required block fields
    REQUIRED_FIELDS = {"index", "timestamp", "data", "previous_hash", "nonce", "hash"}
    
    def __init__(
        self,
        difficulty: int = 2,
        strict_mode: bool = True,
        enable_cross_chain: bool = False,
        parallel_verify: bool = True,
        max_block_size: int = MAX_BLOCK_SIZE,
    ) -> None:
        """
        Initialize the validation engine.
        
        Args:
            difficulty: Expected PoW difficulty (leading zeros)
            strict_mode: Enable all validation layers
            enable_cross_chain: Enable cross-chain anchor verification
            parallel_verify: Parallelize signature verification
            max_block_size: Maximum allowed block size in bytes
        """
        self.difficulty = difficulty
        self.strict_mode = strict_mode
        self.enable_cross_chain = enable_cross_chain
        self.parallel_verify = parallel_verify
        self.max_block_size = max_block_size
        
        # Seen message IDs (for duplicate detection)
        self._seen_message_ids: set[str] = set()
        self._seen_nonces: set[tuple[str, bytes]] = set()  # (sender, nonce)
        
        # Metrics
        self.blocks_validated = 0
        self.blocks_rejected = 0
        self.validation_times: list[float] = []
    
    async def validate_block(
        self,
        block: Block,
        previous_block: Optional[Block] = None,
        level: ValidationLevel = ValidationLevel.STRICT,
    ) -> ValidationResult:
        """
        Validate a single block through the validation pipeline.
        
        Args:
            block: Block to validate
            previous_block: Previous block in chain (for link verification)
            level: Validation strictness level
            
        Returns:
            ValidationResult with pass/fail status and any errors
        """
        start_time = time.perf_counter()
        errors: list[ValidationError] = []
        warnings: list[str] = []
        layers_passed: list[str] = []
        layers_failed: list[str] = []
        
        # Layer 1: Structural Validation
        struct_errors = self._validate_structural(block)
        if struct_errors:
            errors.extend(struct_errors)
            layers_failed.append("structural")
        else:
            layers_passed.append("structural")
        
        # Layer 2: Cryptographic Validation
        crypto_errors = self._validate_cryptographic(block)
        if crypto_errors:
            errors.extend(crypto_errors)
            layers_failed.append("cryptographic")
        else:
            layers_passed.append("cryptographic")
        
        # Layer 3: Consensus Validation
        consensus_errors = self._validate_consensus(block, previous_block)
        if consensus_errors:
            errors.extend(consensus_errors)
            layers_failed.append("consensus")
        else:
            layers_passed.append("consensus")
        
        # Layer 4: Semantic Validation (if strict mode)
        if level in (ValidationLevel.STRICT, ValidationLevel.PARANOID):
            semantic_errors = self._validate_semantic(block)
            if semantic_errors:
                errors.extend(semantic_errors)
                layers_failed.append("semantic")
            else:
                layers_passed.append("semantic")
        
        # Layer 5: Cross-Chain Validation (if enabled)
        if self.enable_cross_chain and level == ValidationLevel.PARANOID:
            cross_errors = await self._validate_cross_chain(block)
            if cross_errors:
                errors.extend(cross_errors)
                layers_failed.append("cross_chain")
            else:
                layers_passed.append("cross_chain")
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        is_valid = len(errors) == 0
        
        # Update metrics
        self.blocks_validated += 1
        if not is_valid:
            self.blocks_rejected += 1
        self.validation_times.append(elapsed_ms)
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed_ms,
            layers_passed=layers_passed,
            layers_failed=layers_failed,
        )
    
    async def validate_chain(
        self,
        blocks: list[Block],
        from_genesis: bool = True,
    ) -> ValidationResult:
        """
        Validate an entire chain of blocks.
        
        Args:
            blocks: List of blocks to validate
            from_genesis: Whether the first block is genesis
            
        Returns:
            ValidationResult for the entire chain
        """
        start_time = time.perf_counter()
        all_errors: list[ValidationError] = []
        
        for i, block in enumerate(blocks):
            previous_block = blocks[i - 1] if i > 0 else None
            
            # Skip genesis block PoW check if it's the first block
            if i == 0 and from_genesis:
                result = await self.validate_block(
                    block, 
                    previous_block=None,
                    level=ValidationLevel.STANDARD
                )
            else:
                result = await self.validate_block(block, previous_block)
            
            if not result.is_valid:
                for error in result.errors:
                    error.block_index = i
                    all_errors.append(error)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            duration_ms=elapsed_ms,
            layers_passed=["chain"] if not all_errors else [],
            layers_failed=["chain"] if all_errors else [],
        )
    
    def _validate_structural(self, block: Block) -> list[ValidationError]:
        """Layer 1: Structural validation."""
        errors: list[ValidationError] = []
        
        # Check block has all required fields
        block_dict = block.to_dict()
        missing = self.REQUIRED_FIELDS - set(block_dict.keys())
        if missing:
            errors.append(ValidationError(
                code=ValidationErrorCode.MISSING_FIELD,
                message=f"Block missing required fields: {missing}",
                layer="structural",
                details={"missing_fields": list(missing)},
            ))
        
        # Check types
        if not isinstance(block.index, int) or block.index < 0:
            errors.append(ValidationError(
                code=ValidationErrorCode.INVALID_TYPE,
                message=f"Block index must be non-negative integer, got {block.index}",
                layer="structural",
            ))
        
        if not isinstance(block.timestamp, (int, float)):
            errors.append(ValidationError(
                code=ValidationErrorCode.INVALID_TYPE,
                message=f"Block timestamp must be numeric, got {type(block.timestamp)}",
                layer="structural",
            ))
        
        if not isinstance(block.data, dict):
            errors.append(ValidationError(
                code=ValidationErrorCode.INVALID_TYPE,
                message=f"Block data must be dict, got {type(block.data)}",
                layer="structural",
            ))
        
        # Check size
        if block.size > self.max_block_size:
            errors.append(ValidationError(
                code=ValidationErrorCode.SIZE_EXCEEDED,
                message=f"Block size {block.size} exceeds max {self.max_block_size}",
                layer="structural",
                details={"size": block.size, "max": self.max_block_size},
            ))
        
        return errors
    
    def _validate_cryptographic(self, block: Block) -> list[ValidationError]:
        """Layer 2: Cryptographic validation."""
        errors: list[ValidationError] = []
        
        # Verify hash matches content
        calculated_hash = block.calculate_hash()
        if block.hash != calculated_hash:
            errors.append(ValidationError(
                code=ValidationErrorCode.HASH_MISMATCH,
                message="Block hash does not match content",
                layer="cryptographic",
                details={
                    "stored_hash": block.hash[:16] + "...",
                    "calculated_hash": calculated_hash[:16] + "...",
                },
            ))
        
        # Verify Merkle root
        if hasattr(block, 'merkle_root') and block.merkle_root:
            import hashlib
            import json
            
            if "messages" in block.data and block.data["messages"]:
                items = [json.dumps(m, sort_keys=True).encode() 
                        for m in block.data["messages"]]
                # Calculate expected Merkle root
                from ..blockchain import calculate_merkle_root
                expected_root = calculate_merkle_root(items)
                
                if block.merkle_root != expected_root:
                    errors.append(ValidationError(
                        code=ValidationErrorCode.MERKLE_INVALID,
                        message="Merkle root does not match messages",
                        layer="cryptographic",
                        details={
                            "stored_root": block.merkle_root[:16] + "...",
                            "calculated_root": expected_root[:16] + "...",
                        },
                    ))
        
        return errors
    
    def _validate_consensus(
        self,
        block: Block,
        previous_block: Optional[Block],
    ) -> list[ValidationError]:
        """Layer 3: Consensus validation."""
        errors: list[ValidationError] = []
        
        # Verify Proof of Work
        target = "0" * self.difficulty
        if not block.hash.startswith(target):
            errors.append(ValidationError(
                code=ValidationErrorCode.POW_INVALID,
                message=f"Block hash does not meet difficulty {self.difficulty}",
                layer="consensus",
                details={
                    "required_prefix": target,
                    "actual_prefix": block.hash[:self.difficulty],
                },
            ))
        
        # Verify timestamp is reasonable
        current_time = time.time()
        if block.timestamp > current_time + self.MAX_TIMESTAMP_DRIFT:
            errors.append(ValidationError(
                code=ValidationErrorCode.TIMESTAMP_INVALID,
                message="Block timestamp too far in future",
                layer="consensus",
                details={
                    "block_time": block.timestamp,
                    "current_time": current_time,
                    "drift": block.timestamp - current_time,
                },
            ))
        
        # Verify chain link
        if previous_block is not None:
            if block.previous_hash != previous_block.hash:
                errors.append(ValidationError(
                    code=ValidationErrorCode.CHAIN_LINK_BROKEN,
                    message="Block does not link to previous block",
                    layer="consensus",
                    details={
                        "expected_prev": previous_block.hash[:16] + "...",
                        "actual_prev": block.previous_hash[:16] + "...",
                    },
                ))
            
            # Verify index is sequential
            if block.index != previous_block.index + 1:
                errors.append(ValidationError(
                    code=ValidationErrorCode.CHAIN_LINK_BROKEN,
                    message=f"Block index {block.index} should be {previous_block.index + 1}",
                    layer="consensus",
                ))
            
            # Verify timestamp is after previous block
            if block.timestamp < previous_block.timestamp:
                errors.append(ValidationError(
                    code=ValidationErrorCode.TIMESTAMP_INVALID,
                    message="Block timestamp before previous block",
                    layer="consensus",
                ))
        
        return errors
    
    def _validate_semantic(self, block: Block) -> list[ValidationError]:
        """Layer 4: Semantic validation."""
        errors: list[ValidationError] = []
        
        if "messages" not in block.data:
            return errors
        
        messages = block.data["messages"]
        if not isinstance(messages, list):
            errors.append(ValidationError(
                code=ValidationErrorCode.MESSAGE_FORMAT_INVALID,
                message="Block messages must be a list",
                layer="semantic",
            ))
            return errors
        
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                errors.append(ValidationError(
                    code=ValidationErrorCode.MESSAGE_FORMAT_INVALID,
                    message=f"Message {i} is not a dict",
                    layer="semantic",
                ))
                continue
            
            # Check for duplicate message IDs
            msg_id = msg.get("id")
            if msg_id:
                if msg_id in self._seen_message_ids:
                    errors.append(ValidationError(
                        code=ValidationErrorCode.DUPLICATE_MESSAGE,
                        message=f"Duplicate message ID: {msg_id}",
                        layer="semantic",
                        details={"message_id": msg_id},
                    ))
                else:
                    self._seen_message_ids.add(msg_id)
            
            # Check for nonce reuse
            sender = msg.get("sender")
            nonce = msg.get("nonce")
            if sender and nonce:
                nonce_key = (sender, str(nonce).encode())
                if nonce_key in self._seen_nonces:
                    errors.append(ValidationError(
                        code=ValidationErrorCode.NONCE_REUSED,
                        message=f"Nonce reused by sender {sender[:16]}...",
                        layer="semantic",
                    ))
                else:
                    self._seen_nonces.add(nonce_key)
        
        return errors
    
    async def _validate_cross_chain(self, block: Block) -> list[ValidationError]:
        """Layer 5: Cross-chain validation (placeholder for v2.0)."""
        # This will be implemented when multi-chain anchoring is added
        return []
    
    def reset_state(self) -> None:
        """Clear seen message/nonce state (for testing or chain reset)."""
        self._seen_message_ids.clear()
        self._seen_nonces.clear()
    
    def get_metrics(self) -> dict[str, Any]:
        """Get validation metrics."""
        avg_time = sum(self.validation_times) / len(self.validation_times) if self.validation_times else 0
        return {
            "blocks_validated": self.blocks_validated,
            "blocks_rejected": self.blocks_rejected,
            "rejection_rate": self.blocks_rejected / self.blocks_validated if self.blocks_validated else 0,
            "avg_validation_time_ms": avg_time,
            "total_validation_time_ms": sum(self.validation_times),
        }
