"""
Validation Layers - Individual validator implementations.

Each layer validates a specific aspect of block integrity:
- Structural: Schema and type validation
- Cryptographic: Hash and signature verification
- Consensus: PoW and chain rules
- Semantic: Message format and duplicate detection
- Cross-Chain: External anchor verification
"""

import asyncio
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from ..blockchain import Block, calculate_merkle_root

logger = logging.getLogger(__name__)


class ValidationLayer(ABC):
    """Base class for validation layers."""

    name: str = "base"

    @abstractmethod
    def validate(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Validate a block.
        
        Args:
            block: Block to validate
            context: Additional context (previous_block, difficulty, etc.)
            
        Returns:
            List of error dicts, empty if valid
        """
        pass


class StructuralValidator(ValidationLayer):
    """
    Layer 1: Structural Validation
    
    Validates block schema, field types, and size limits.
    """

    name = "structural"

    REQUIRED_FIELDS = {"index", "timestamp", "data", "previous_hash", "nonce", "hash"}
    MAX_BLOCK_SIZE = 1_000_000  # 1MB

    def validate(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        errors = []

        # Check required fields
        block_dict = block.to_dict()
        missing = self.REQUIRED_FIELDS - set(block_dict.keys())
        if missing:
            errors.append({
                "code": "MISSING_FIELD",
                "message": f"Missing fields: {missing}",
                "details": {"missing": list(missing)},
            })

        # Type checks
        if not isinstance(block.index, int) or block.index < 0:
            errors.append({
                "code": "INVALID_TYPE",
                "message": f"Invalid index: {block.index}",
            })

        if not isinstance(block.timestamp, (int, float)):
            errors.append({
                "code": "INVALID_TYPE",
                "message": f"Invalid timestamp type: {type(block.timestamp)}",
            })

        if not isinstance(block.data, dict):
            errors.append({
                "code": "INVALID_TYPE",
                "message": f"Invalid data type: {type(block.data)}",
            })

        # Size check
        max_size = context.get("max_block_size", self.MAX_BLOCK_SIZE)
        if block.size > max_size:
            errors.append({
                "code": "SIZE_EXCEEDED",
                "message": f"Block size {block.size} exceeds {max_size}",
                "details": {"size": block.size, "max": max_size},
            })

        return errors


class CryptographicValidator(ValidationLayer):
    """
    Layer 2: Cryptographic Validation
    
    Validates hash integrity, Merkle roots, and signatures.
    """

    name = "cryptographic"

    def validate(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        errors = []

        # Verify hash
        if block.hash != block.calculate_hash():
            errors.append({
                "code": "HASH_MISMATCH",
                "message": "Block hash does not match content",
                "details": {
                    "stored": block.hash[:16] + "...",
                    "calculated": block.calculate_hash()[:16] + "...",
                },
            })

        # Verify Merkle root
        if hasattr(block, 'merkle_root') and block.merkle_root:
            merkle_errors = self._verify_merkle_root(block)
            errors.extend(merkle_errors)

        # Verify message signatures if present
        signature_errors = self._verify_signatures(block, context)
        errors.extend(signature_errors)

        return errors

    def _verify_merkle_root(self, block: Block) -> list[dict[str, Any]]:
        """Verify the Merkle root matches the message content."""
        errors = []

        if "messages" in block.data and block.data["messages"]:
            items = [json.dumps(m, sort_keys=True).encode()
                    for m in block.data["messages"]]
            expected = calculate_merkle_root(items)

            if block.merkle_root != expected:
                errors.append({
                    "code": "MERKLE_INVALID",
                    "message": "Merkle root mismatch",
                    "details": {
                        "stored": block.merkle_root[:16] + "...",
                        "calculated": expected[:16] + "...",
                    },
                })

        return errors

    def _verify_signatures(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Verify message signatures in the block."""
        errors = []

        if "messages" not in block.data:
            return errors

        verify_func = context.get("signature_verifier")
        if not verify_func:
            return errors  # Skip if no verifier provided

        for i, msg in enumerate(block.data["messages"]):
            if not isinstance(msg, dict):
                continue

            signature = msg.get("signature")
            content = msg.get("content")
            public_key = msg.get("sender")

            if signature and content and public_key:
                try:
                    if not verify_func(content, signature, public_key):
                        errors.append({
                            "code": "SIGNATURE_INVALID",
                            "message": f"Invalid signature on message {i}",
                            "details": {"message_index": i},
                        })
                except Exception as e:
                    errors.append({
                        "code": "SIGNATURE_INVALID",
                        "message": f"Signature verification failed: {e}",
                        "details": {"message_index": i, "error": str(e)},
                    })

        return errors


class ConsensusValidator(ValidationLayer):
    """
    Layer 3: Consensus Validation
    
    Validates Proof of Work, timestamps, and chain continuity.
    """

    name = "consensus"

    # Maximum timestamp drift (5 minutes)
    MAX_TIMESTAMP_DRIFT = 300

    def validate(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        errors = []

        difficulty = context.get("difficulty", 2)
        previous_block = context.get("previous_block")

        # Verify PoW
        target = "0" * difficulty
        if not block.hash.startswith(target):
            errors.append({
                "code": "POW_INVALID",
                "message": f"Hash does not meet difficulty {difficulty}",
                "details": {
                    "required": target,
                    "actual": block.hash[:difficulty],
                },
            })

        # Verify timestamp
        current_time = time.time()
        if block.timestamp > current_time + self.MAX_TIMESTAMP_DRIFT:
            errors.append({
                "code": "TIMESTAMP_FUTURE",
                "message": "Block timestamp too far in future",
                "details": {
                    "block_time": block.timestamp,
                    "current_time": current_time,
                },
            })

        # Verify chain link
        if previous_block:
            if block.previous_hash != previous_block.hash:
                errors.append({
                    "code": "CHAIN_BROKEN",
                    "message": "Block does not link to previous",
                    "details": {
                        "expected": previous_block.hash[:16] + "...",
                        "actual": block.previous_hash[:16] + "...",
                    },
                })

            if block.index != previous_block.index + 1:
                errors.append({
                    "code": "INDEX_INVALID",
                    "message": f"Index {block.index} should be {previous_block.index + 1}",
                })

            if block.timestamp < previous_block.timestamp:
                errors.append({
                    "code": "TIMESTAMP_PAST",
                    "message": "Block timestamp before previous block",
                })

        return errors


class SemanticValidator(ValidationLayer):
    """
    Layer 4: Semantic Validation
    
    Validates message formats, duplicates, and nonce reuse.
    """

    name = "semantic"

    def __init__(self):
        self._seen_ids: set[str] = set()
        self._seen_nonces: set[str] = set()

    def validate(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        errors = []

        if "messages" not in block.data:
            return errors

        messages = block.data["messages"]
        if not isinstance(messages, list):
            errors.append({
                "code": "FORMAT_INVALID",
                "message": "messages must be a list",
            })
            return errors

        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                errors.append({
                    "code": "FORMAT_INVALID",
                    "message": f"Message {i} is not a dict",
                })
                continue

            # Check for duplicate IDs
            msg_id = msg.get("id")
            if msg_id:
                if msg_id in self._seen_ids:
                    errors.append({
                        "code": "DUPLICATE_ID",
                        "message": f"Duplicate message ID: {msg_id[:16]}...",
                        "details": {"message_id": msg_id},
                    })
                self._seen_ids.add(msg_id)

            # Check for nonce reuse
            sender = msg.get("sender", "")
            nonce = msg.get("nonce", "")
            if sender and nonce:
                nonce_key = f"{sender}:{nonce}"
                if nonce_key in self._seen_nonces:
                    errors.append({
                        "code": "NONCE_REUSED",
                        "message": f"Nonce reused by {sender[:16]}...",
                    })
                self._seen_nonces.add(nonce_key)

        return errors

    def reset(self):
        """Clear seen state."""
        self._seen_ids.clear()
        self._seen_nonces.clear()


class CrossChainValidator(ValidationLayer):
    """
    Layer 5: Cross-Chain Validation
    
    Validates external blockchain anchors (Ethereum, Solana, etc.).
    """

    name = "cross_chain"

    def validate(self, block: Block, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Validate block anchors if present.
        """
        errors = []
        
        # Check if block data contains anchor information
        anchor = block.data.get("anchor")
        if not anchor:
            return errors

        chain = anchor.get("chain")
        tx_hash = anchor.get("tx_hash")
        root = anchor.get("root")

        if not chain or not tx_hash or not root:
            errors.append({
                "code": "ANCHOR_INCOMPLETE",
                "message": "Block contains incomplete anchor information",
                "details": {"anchor": anchor},
            })
            return errors

        # Verify anchor root matches block merkle_root
        if root != block.merkle_root:
            errors.append({
                "code": "ANCHOR_ROOT_MISMATCH",
                "message": "Anchor root does not match block Merkle root",
                "details": {"anchor_root": root, "block_root": block.merkle_root},
            })

        # Verify against external signal (simulated for now)
        if not self.verify_anchor_sync(root, chain, tx_hash):
            errors.append({
                "code": "ANCHOR_VERIFICATION_FAILED",
                "message": f"Anchor verification failed on {chain} for {tx_hash}",
            })

        return errors

    def verify_anchor_sync(self, merkle_root: str, chain: str, tx_hash: str) -> bool:
        """
        Synchronous version of anchor verification.
        
        Note: Currently restricted to format validation and opt-in debug mode.
        Full implementation requires wiring to an external chain adapter.
        """
        # 1. Basic Format Validation
        # Most transaction hashes are 32-byte hex (64 chars)
        if not re.match(r"^(0x)?[0-9a-fA-F]{64}$", tx_hash):
             logger.error(f"Anchor verification failed: Invalid tx_hash format: {tx_hash}")
             return False

        # 2. FAIL-CLOSED Logic
        # This is a critical security boundary. Returning True by default is a loophole.
        # Until a real external adapter (e.g., Infura, Alchemy) is wired,
        # we must fail if strict verification is requested.
        strict_mode = os.getenv("TALOS_STRICT_ANCHOR_VERIFICATION") == "true"
        if strict_mode:
            logger.error(f"STRICT MODE: Anchor verification failed - No production adapter for {chain}")
            return False

        # 3. Development/Demo Mode (Insecure)
        # Use this ONLY for local development or integrated demos where external signal is mocked.
        if os.getenv("TALOS_INSECURE_DEBUG_ANCHORS") == "true":
            logger.warning(f"INSECURE: Allowing unverified anchor {tx_hash} on {chain} (debug mode)")
            return True

        # Default to False: Fail-Closed
        logger.error(f"Anchor verification failed: No implementation for {chain} and not in insecure debug mode.")
        return False

    async def verify_anchor(
        self,
        merkle_root: str,
        chain: str,
        tx_hash: str,
    ) -> bool:
        """
        Verify that a Merkle root was anchored on an external chain.
        
        Args:
            merkle_root: Expected Merkle root
            chain: Chain name (ethereum, solana, bitcoin)
            tx_hash: Transaction hash containing the anchor
            
        Returns:
            True if anchor is valid
        """
        # Simulate network latency
        await asyncio.sleep(0.01) if "asyncio" in globals() else None
        return self.verify_anchor_sync(merkle_root, chain, tx_hash)
