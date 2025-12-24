"""
Block Validation Engine for Talos Protocol v2.0.

This module provides a comprehensive, multi-layer validation system for
blockchain blocks. It ensures integrity at every level through:

- Structural validation (schema, types, sizes)
- Cryptographic validation (hashes, signatures, Merkle proofs)
- Consensus validation (PoW, timestamps, chain continuity)
- Semantic validation (duplicates, nonces, message formats)

Usage:
    from src.core.validation import ValidationEngine, ValidationResult
    
    engine = ValidationEngine(difficulty=2)
    result = await engine.validate_block(block)
    if result.is_valid:
        chain.append(block)
"""

from .engine import (
    ValidationEngine,
    ValidationResult,
    ValidationLevel,
    ValidationError,
)
from .layers import (
    StructuralValidator,
    CryptographicValidator,
    ConsensusValidator,
    SemanticValidator,
    CrossChainValidator,
)
from .proofs import (
    verify_block_hash,
    verify_merkle_root,
    verify_pow_target,
    verify_chain_link,
    batch_verify_signatures,
)
from .report import ValidationReport, generate_audit_report

__all__ = [
    # Engine
    "ValidationEngine",
    "ValidationResult", 
    "ValidationLevel",
    "ValidationError",
    # Validators
    "StructuralValidator",
    "CryptographicValidator",
    "ConsensusValidator",
    "SemanticValidator",
    "CrossChainValidator",
    # Proofs
    "verify_block_hash",
    "verify_merkle_root",
    "verify_pow_target",
    "verify_chain_link",
    "batch_verify_signatures",
    # Reports
    "ValidationReport",
    "generate_audit_report",
]
