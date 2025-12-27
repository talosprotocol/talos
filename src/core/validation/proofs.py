"""
Cryptographic Proof Verification Functions.

This module provides standalone functions for verifying cryptographic
proofs used in block validation:
- Block hash verification
- Merkle root verification
- Proof of Work target verification
- Chain link verification
- Batch signature verification
"""

import hashlib
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def verify_block_hash(block_dict: dict[str, Any]) -> tuple[bool, str]:
    """
    Verify that a block's hash matches its content.
    
    Args:
        block_dict: Block as dictionary
        
    Returns:
        Tuple of (is_valid, calculated_hash)
    """
    # Create hash input (same as Block.calculate_hash)
    hash_input = json.dumps({
        "index": block_dict["index"],
        "timestamp": block_dict["timestamp"],
        "data": block_dict["data"],
        "previous_hash": block_dict["previous_hash"],
        "nonce": block_dict["nonce"],
        "merkle_root": block_dict.get("merkle_root", ""),
    }, sort_keys=True)

    calculated = hashlib.sha256(hash_input.encode()).hexdigest()
    stored = block_dict.get("hash", "")

    return calculated == stored, calculated


def verify_merkle_root(messages: list[dict[str, Any]], expected_root: str) -> bool:
    """
    Verify that messages produce the expected Merkle root.
    
    Args:
        messages: List of message dicts
        expected_root: Expected Merkle root hash
        
    Returns:
        True if Merkle root matches
    """
    if not messages:
        empty_hash = hashlib.sha256(b"").hexdigest()
        return expected_root == empty_hash

    # Hash each message
    hashes = [
        hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()
        for m in messages
    ]

    # Build tree
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])  # Duplicate last if odd

        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
        hashes = next_level

    return hashes[0] == expected_root


def verify_pow_target(block_hash: str, difficulty: int) -> bool:
    """
    Verify that a block hash meets the Proof of Work target.
    
    Args:
        block_hash: The block's hash
        difficulty: Required number of leading zeros
        
    Returns:
        True if hash meets target
    """
    target = "0" * difficulty
    return block_hash.startswith(target)


def verify_chain_link(
    block_dict: dict[str, Any],
    previous_block_dict: Optional[dict[str, Any]],
) -> bool:
    """
    Verify that a block correctly links to its predecessor.
    
    Args:
        block_dict: Current block as dict
        previous_block_dict: Previous block as dict (or None for genesis)
        
    Returns:
        True if chain link is valid
    """
    if previous_block_dict is None:
        # Genesis block - previous hash should be all zeros
        return block_dict.get("previous_hash") == "0" * 64

    return block_dict.get("previous_hash") == previous_block_dict.get("hash")


def verify_signature(
    message: bytes,
    signature: bytes,
    public_key: bytes,
) -> bool:
    """
    Verify an Ed25519 signature.
    
    Args:
        message: Original message bytes
        signature: 64-byte signature
        public_key: 32-byte Ed25519 public key
        
    Returns:
        True if signature is valid
    """
    # Import here to avoid circular dependency
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        key = Ed25519PublicKey.from_public_bytes(public_key)
        key.verify(signature, message)
        return True
    except Exception:
        return False


def batch_verify_signatures(
    messages: list[bytes],
    signatures: list[bytes],
    public_keys: list[bytes],
    parallel: bool = True,
) -> list[bool]:
    """
    Verify multiple signatures, optionally in parallel.
    
    Note: Ed25519 doesn't support true batch verification like Schnorr,
    but we can parallelize individual verifications for ~1.3x speedup.
    
    Args:
        messages: List of message bytes
        signatures: List of 64-byte signatures
        public_keys: List of 32-byte public keys
        parallel: Whether to verify in parallel
        
    Returns:
        List of verification results (True/False for each)
    """
    if len(messages) != len(signatures) or len(signatures) != len(public_keys):
        raise ValueError("Input lists must have same length")

    if not messages:
        return []

    if parallel and len(messages) > 1:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(verify_signature, m, s, pk)
                for m, s, pk in zip(messages, signatures, public_keys)
            ]
            return [f.result() for f in futures]
    else:
        return [
            verify_signature(m, s, pk)
            for m, s, pk in zip(messages, signatures, public_keys)
        ]


def verify_merkle_proof(
    data_hash: str,
    proof_path: list[tuple[str, str]],
    merkle_root: str,
) -> bool:
    """
    Verify a Merkle proof that data exists in a block.
    
    Args:
        data_hash: Hash of the data item
        proof_path: List of (sibling_hash, position) tuples
        merkle_root: Expected Merkle root
        
    Returns:
        True if proof is valid
    """
    current = data_hash

    for sibling_hash, position in proof_path:
        if position == "left":
            combined = sibling_hash + current
        else:
            combined = current + sibling_hash
        current = hashlib.sha256(combined.encode()).hexdigest()

    return current == merkle_root


def verify_double_hash(data: bytes, expected: str) -> bool:
    """
    Verify a Bitcoin-style double SHA-256 hash.
    
    Args:
        data: Data to hash
        expected: Expected hash (hex string)
        
    Returns:
        True if hash matches
    """
    first = hashlib.sha256(data).digest()
    second = hashlib.sha256(first).hexdigest()
    return second == expected


# Type alias for signature verifier function
SignatureVerifier = Callable[[bytes, bytes, bytes], bool]
