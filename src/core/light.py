"""
Light Client Blockchain Implementation.

This module provides a lightweight blockchain client that:
- Stores only block headers (not full block data)
- Validates blocks using SPV (Simplified Payment Verification) proofs
- Supports efficient sync with full nodes
- Reduces storage requirements by ~99%

Usage:
    from src.core.light import LightBlockchain, BlockHeader
    
    light = LightBlockchain(difficulty=2)
    
    # Sync headers from full node
    headers = await full_node.get_headers(start=0)
    for header in headers:
        light.add_header(header)
    
    # Verify a message exists using SPV proof
    proof = await full_node.get_merkle_proof(message_hash, block_height)
    is_valid = light.verify_spv_proof(proof)
"""

import hashlib
import json
import logging
import time
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BlockHeader(BaseModel):
    """
    Block header containing only essential metadata.
    
    A header is ~200 bytes vs ~1MB for a full block.
    """
    
    index: int
    timestamp: float
    previous_hash: str
    merkle_root: str
    nonce: int
    hash: str
    difficulty: int = 2
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @property
    def size(self) -> int:
        """Approximate size in bytes."""
        return len(json.dumps(self.to_dict()))
    
    def validate_pow(self) -> bool:
        """Verify proof-of-work is valid."""
        return self.hash.startswith("0" * self.difficulty)
    
    def calculate_hash(self) -> str:
        """Recalculate hash from header fields."""
        header_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(header_string.encode()).hexdigest()
    
    def verify_hash(self) -> bool:
        """Verify hash matches content."""
        return self.hash == self.calculate_hash()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "hash": self.hash,
            "difficulty": self.difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlockHeader":
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            previous_hash=data["previous_hash"],
            merkle_root=data["merkle_root"],
            nonce=data["nonce"],
            hash=data["hash"],
            difficulty=data.get("difficulty", 2),
        )
    
    @classmethod
    def from_block(cls, block: Any, difficulty: int = 2) -> "BlockHeader":
        """Create header from full Block object."""
        return cls(
            index=block.index,
            timestamp=block.timestamp,
            previous_hash=block.previous_hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce,
            hash=block.hash,
            difficulty=difficulty,
        )


class SPVProof(BaseModel):
    """
    Simplified Payment Verification proof.
    
    Proves that a piece of data exists in a block without
    requiring the full block data.
    """
    
    data_hash: str
    block_hash: str
    block_height: int
    merkle_root: str
    merkle_path: list[tuple[str, str]]  # (sibling_hash, "left"|"right")
    timestamp: float = Field(default_factory=time.time)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def verify(self) -> bool:
        """
        Verify the Merkle proof.
        
        Returns:
            True if data_hash is in the Merkle tree
        """
        current = self.data_hash
        
        for sibling_hash, position in self.merkle_path:
            if position == "left":
                combined = sibling_hash + current
            else:
                combined = current + sibling_hash
            current = hashlib.sha256(combined.encode()).hexdigest()
        
        return current == self.merkle_root
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "data_hash": self.data_hash,
            "block_hash": self.block_hash,
            "block_height": self.block_height,
            "merkle_root": self.merkle_root,
            "merkle_path": self.merkle_path,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SPVProof":
        return cls(
            data_hash=data["data_hash"],
            block_hash=data["block_hash"],
            block_height=data["block_height"],
            merkle_root=data["merkle_root"],
            merkle_path=[(p[0], p[1]) for p in data["merkle_path"]],
            timestamp=data.get("timestamp", 0),
        )


class LightBlockchain:
    """
    Light client blockchain that stores only headers.
    
    Features:
    - Header-only storage (~99% size reduction)
    - SPV proof verification
    - Efficient sync with full nodes
    - Chain validation without full data
    
    Usage:
        light = LightBlockchain(difficulty=2)
        
        # Add headers from sync
        light.add_header(header)
        
        # Verify SPV proof
        if light.verify_spv_proof(proof):
            print("Data exists in block!")
    """
    
    def __init__(
        self,
        difficulty: int = 2,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize light blockchain.
        
        Args:
            difficulty: Expected mining difficulty
            storage_path: Optional path for header persistence
        """
        self.difficulty = difficulty
        self.storage_path = storage_path
        
        # Header chain
        self.headers: list[BlockHeader] = []
        
        # Indexes for fast lookup
        self._hash_index: dict[str, int] = {}  # hash -> height
        self._merkle_index: dict[str, str] = {}  # merkle_root -> block_hash
        
        # Verified SPV proofs cache
        self._verified_proofs: dict[str, SPVProof] = {}
        
        # Stats
        self._sync_height = 0
        self._proofs_verified = 0
        self._proofs_failed = 0
    
    @property
    def height(self) -> int:
        """Current chain height (number of headers - 1)."""
        return len(self.headers) - 1 if self.headers else -1
    
    @property
    def latest_hash(self) -> Optional[str]:
        """Hash of the latest header."""
        return self.headers[-1].hash if self.headers else None
    
    @property
    def genesis_hash(self) -> Optional[str]:
        """Hash of the genesis header."""
        return self.headers[0].hash if self.headers else None
    
    def add_header(self, header: BlockHeader) -> bool:
        """
        Add a header to the chain.
        
        Args:
            header: BlockHeader to add
            
        Returns:
            True if header was added, False if invalid
        """
        # Validate header
        if not self._validate_header(header):
            logger.warning(f"Invalid header at height {header.index}")
            return False
        
        # Add to chain
        self.headers.append(header)
        
        # Update indexes
        self._hash_index[header.hash] = header.index
        self._merkle_index[header.merkle_root] = header.hash
        
        logger.debug(f"Added header {header.index}: {header.hash[:16]}...")
        return True
    
    def add_headers(self, headers: list[BlockHeader]) -> int:
        """
        Add multiple headers to the chain.
        
        Args:
            headers: List of BlockHeaders
            
        Returns:
            Number of headers successfully added
        """
        added = 0
        for header in headers:
            if self.add_header(header):
                added += 1
            else:
                break  # Stop on first invalid header
        return added
    
    def _validate_header(self, header: BlockHeader) -> bool:
        """Validate a header before adding."""
        # Check index is next
        expected_index = len(self.headers)
        if header.index != expected_index:
            logger.debug(f"Wrong index: expected {expected_index}, got {header.index}")
            return False
        
        # Check previous hash (except genesis)
        if expected_index > 0:
            if header.previous_hash != self.headers[-1].hash:
                logger.debug("Previous hash mismatch")
                return False
        
        # Check proof of work
        if not header.validate_pow():
            logger.debug("Invalid proof of work")
            return False
        
        # Check timestamp not too far in future
        if header.timestamp > time.time() + 600:  # 10 min tolerance
            logger.debug("Timestamp too far in future")
            return False
        
        return True
    
    def get_header(self, height: int) -> Optional[BlockHeader]:
        """Get header by height."""
        if 0 <= height < len(self.headers):
            return self.headers[height]
        return None
    
    def get_header_by_hash(self, block_hash: str) -> Optional[BlockHeader]:
        """Get header by block hash."""
        height = self._hash_index.get(block_hash)
        if height is not None:
            return self.headers[height]
        return None
    
    def verify_spv_proof(self, proof: SPVProof) -> bool:
        """
        Verify an SPV proof against our header chain.
        
        Args:
            proof: SPVProof to verify
            
        Returns:
            True if proof is valid and block exists in our chain
        """
        # Check block exists in our chain
        header = self.get_header_by_hash(proof.block_hash)
        if header is None:
            logger.debug(f"Block not in chain: {proof.block_hash[:16]}...")
            self._proofs_failed += 1
            return False
        
        # Check merkle root matches
        if header.merkle_root != proof.merkle_root:
            logger.debug("Merkle root mismatch")
            self._proofs_failed += 1
            return False
        
        # Verify the Merkle proof itself
        if not proof.verify():
            logger.debug("Merkle proof verification failed")
            self._proofs_failed += 1
            return False
        
        # Cache successful proof
        self._verified_proofs[proof.data_hash] = proof
        self._proofs_verified += 1
        
        logger.debug(f"SPV proof verified: {proof.data_hash[:16]}... in block {proof.block_height}")
        return True
    
    def has_verified_data(self, data_hash: str) -> bool:
        """Check if we've verified a piece of data exists."""
        return data_hash in self._verified_proofs
    
    def get_verified_proof(self, data_hash: str) -> Optional[SPVProof]:
        """Get a previously verified proof."""
        return self._verified_proofs.get(data_hash)
    
    def validate_chain(self) -> bool:
        """Validate the entire header chain."""
        if not self.headers:
            return True
        
        for i, header in enumerate(self.headers):
            # Check index
            if header.index != i:
                return False
            
            # Check previous hash link
            if i > 0 and header.previous_hash != self.headers[i-1].hash:
                return False
            
            # Check PoW
            if not header.validate_pow():
                return False
        
        return True
    
    def get_sync_request(self, batch_size: int = 100) -> dict[str, Any]:
        """
        Generate a sync request for a full node.
        
        Returns:
            Request dict with start height and count
        """
        return {
            "type": "GET_HEADERS",
            "start_height": len(self.headers),
            "count": batch_size,
            "latest_hash": self.latest_hash,
        }
    
    def get_proof_request(self, data_hash: str) -> dict[str, Any]:
        """
        Generate an SPV proof request.
        
        Args:
            data_hash: Hash of data to prove
            
        Returns:
            Request dict for full node
        """
        return {
            "type": "GET_MERKLE_PROOF",
            "data_hash": data_hash,
        }
    
    def get_stats(self) -> dict[str, Any]:
        """Get light client statistics."""
        header_size = sum(h.size for h in self.headers) if self.headers else 0
        
        return {
            "height": self.height,
            "headers_count": len(self.headers),
            "header_storage_bytes": header_size,
            "proofs_verified": self._proofs_verified,
            "proofs_failed": self._proofs_failed,
            "cached_proofs": len(self._verified_proofs),
            "difficulty": self.difficulty,
        }
    
    def save(self, path: Optional[Path] = None) -> None:
        """
        Save headers to disk.
        
        Args:
            path: Optional override path
        """
        save_path = path or self.storage_path
        if not save_path:
            raise ValueError("No storage path specified")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "difficulty": self.difficulty,
            "headers": [h.to_dict() for h in self.headers],
            "verified_proofs": {k: v.to_dict() for k, v in self._verified_proofs.items()},
        }
        
        # Atomic write
        temp_path = save_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f)
        temp_path.rename(save_path)
        
        logger.debug(f"Saved {len(self.headers)} headers to {save_path}")
    
    def load(self, path: Optional[Path] = None) -> None:
        """
        Load headers from disk.
        
        Args:
            path: Optional override path
        """
        load_path = path or self.storage_path
        if not load_path:
            raise ValueError("No storage path specified")
        
        load_path = Path(load_path)
        if not load_path.exists():
            return
        
        with open(load_path) as f:
            data = json.load(f)
        
        self.difficulty = data.get("difficulty", self.difficulty)
        self.headers = [BlockHeader.from_dict(h) for h in data.get("headers", [])]
        self._verified_proofs = {
            k: SPVProof.from_dict(v)
            for k, v in data.get("verified_proofs", {}).items()
        }
        
        # Rebuild indexes
        self._hash_index = {h.hash: h.index for h in self.headers}
        self._merkle_index = {h.merkle_root: h.hash for h in self.headers}
        
        logger.debug(f"Loaded {len(self.headers)} headers from {load_path}")
    
    @classmethod
    def from_blockchain(cls, blockchain: Any, difficulty: int = 2) -> "LightBlockchain":
        """
        Create a LightBlockchain from a full Blockchain.
        
        Args:
            blockchain: Full Blockchain instance
            difficulty: Mining difficulty
            
        Returns:
            LightBlockchain with headers extracted
        """
        light = cls(difficulty=difficulty)
        
        for block in blockchain.chain:
            header = BlockHeader.from_block(block, difficulty)
            light.add_header(header)
        
        return light
    
    def __len__(self) -> int:
        return len(self.headers)
    
    def __repr__(self) -> str:
        return f"LightBlockchain(height={self.height}, headers={len(self.headers)})"
