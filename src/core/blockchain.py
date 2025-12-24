"""
Production-ready blockchain implementation for message storage and integrity verification.

This module provides:
- Block creation with SHA-256 hashing
- Blockchain management with atomic persistence
- Block size limits and validation
- Chain synchronization support
- Block indexing for O(1) lookups
- Merkle proofs for data verification
- Simple Proof-of-Work consensus
"""

import hashlib
import json
import logging
import os
import tempfile
import time
from typing import Any, Callable, Optional, List, Tuple
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict, field_validator

logger = logging.getLogger(__name__)

# Configuration constants
MAX_BLOCK_SIZE = 1_000_000  # 1MB max block size
MAX_PENDING_DATA = 10_000   # Max items in mempool
MAX_SINGLE_ITEM_SIZE = MAX_BLOCK_SIZE // 10  # 100KB per item


class BlockchainError(Exception):
    """Base exception for blockchain errors."""
    pass


class BlockValidationError(BlockchainError):
    """Block validation failed."""
    pass


class ChainValidationError(BlockchainError):
    """Chain validation failed."""
    pass


class DataRejectedError(BlockchainError):
    """Data was rejected (too large, invalid, etc.)."""
    pass


class Block(BaseModel):
    """A single block in the blockchain."""
    
    index: int
    timestamp: float
    data: dict[str, Any]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate hash after initialization."""
        if not self.hash:
            self._calculate_merkle_root()
            self.hash = self.calculate_hash()
    
    def _calculate_merkle_root(self) -> None:
        """Calculate Merkle root for block data."""
        if "messages" in self.data and self.data["messages"]:
            items = [json.dumps(m, sort_keys=True).encode() 
                    for m in self.data["messages"]]
            self.merkle_root = calculate_merkle_root(items)
        else:
            self.merkle_root = hashlib.sha256(b"").hexdigest()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block contents."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine(self, difficulty: int = 2) -> None:
        """
        Mine the block using Proof-of-Work.
        
        Args:
            difficulty: Number of leading zeros required in hash
        """
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def validate(self, difficulty: int = 2) -> bool:
        """
        Validate block integrity.
        
        Args:
            difficulty: Expected mining difficulty
            
        Returns:
            True if block is valid
        """
        # Check hash matches content
        if self.hash != self.calculate_hash():
            return False
        
        # Check proof of work
        if not self.hash.startswith("0" * difficulty):
            return False
        
        return True
    
    @property
    def size(self) -> int:
        """Get approximate size of block in bytes."""
        return len(json.dumps(self.model_dump()))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert block to dictionary representation (compat alias)."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        """Create a Block from dictionary representation (compat alias)."""
        return cls(**data)


class ChainStatus(BaseModel):
    """Status of a blockchain for synchronization."""
    
    height: int
    latest_hash: str
    genesis_hash: str
    difficulty: int
    total_work: int
    
    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChainStatus":
        return cls(**data)


class MerkleProof(BaseModel):
    """Proof that data exists in a block."""
    
    block_hash: str
    block_height: int
    data_hash: str
    merkle_root: str
    proof_path: List[Tuple[str, str]]
    
    def verify(self) -> bool:
        """Verify this proof against the stored root."""
        current = self.data_hash
        
        for sibling_hash, position in self.proof_path:
            if position == "left":
                combined = sibling_hash + current
            else:
                combined = current + sibling_hash
            current = hashlib.sha256(combined.encode()).hexdigest()
        
        return current == self.merkle_root
    
    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MerkleProof":
        return cls(**data)


# Type alias for validation function
DataValidator = Callable[[dict[str, Any]], bool]


class Blockchain:
    """
    Production-ready blockchain implementation for message storage.
    
    Features:
    - Atomic persistence to prevent corruption
    - Block size limits
    - Optional data validation
    - Chain synchronization support
    - Fast block lookup via indexing
    - Merkle proof generation
    """
    
    def __init__(
        self,
        difficulty: int = 2,
        validator: Optional[DataValidator] = None,
        max_block_size: int = MAX_BLOCK_SIZE,
        max_pending: int = MAX_PENDING_DATA
    ) -> None:
        """
        Initialize the blockchain.
        
        Args:
            difficulty: Mining difficulty (number of leading zeros)
            validator: Optional function to validate data before adding
            max_block_size: Maximum block size in bytes
            max_pending: Maximum pending items in mempool
        """
        self.difficulty = difficulty
        self.validator = validator
        self.max_block_size = max_block_size
        self.max_pending = max_pending
        
        # Chain data
        self.chain: list[Block] = []
        self.pending_data: list[dict[str, Any]] = []
        
        # Indexes for O(1) lookup
        self._block_index: dict[str, Block] = {}      # hash -> block
        self._height_index: dict[int, Block] = {}     # height -> block  
        self._message_index: dict[str, int] = {}      # msg_id -> block_height
        
        # Create genesis block
        self._create_genesis_block()
    
    def _create_genesis_block(self) -> None:
        """Create the first block in the chain."""
        genesis = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Genesis Block", "type": "system"},
            previous_hash="0" * 64
        )
        genesis.mine(self.difficulty)
        self.chain.append(genesis)
        self._index_block(genesis)
    
    def _index_block(self, block: Block) -> None:
        """Index a single block for fast lookup."""
        self._block_index[block.hash] = block
        self._height_index[block.index] = block
        
        # Index message IDs
        if "messages" in block.data:
            for msg in block.data["messages"]:
                if isinstance(msg, dict) and "id" in msg:
                    self._message_index[msg["id"]] = block.index
    
    def _rebuild_index(self) -> None:
        """Rebuild all indexes from chain."""
        self._block_index.clear()
        self._height_index.clear()
        self._message_index.clear()
        
        for block in self.chain:
            self._index_block(block)
    
    @property
    def latest_block(self) -> Block:
        """Get the most recent block in the chain."""
        return self.chain[-1]
    
    @property
    def height(self) -> int:
        """Get current chain height."""
        return len(self.chain) - 1
    
    @property
    def total_work(self) -> int:
        """Calculate cumulative proof-of-work."""
        return sum(2 ** self.difficulty for _ in self.chain)
    
    @property
    def genesis_hash(self) -> str:
        """Get genesis block hash."""
        return self.chain[0].hash if self.chain else ""
    
    def get_status(self) -> ChainStatus:
        """Get chain status for synchronization."""
        return ChainStatus(
            height=self.height,
            latest_hash=self.latest_block.hash,
            genesis_hash=self.genesis_hash,
            difficulty=self.difficulty,
            total_work=self.total_work
        )
    
    def add_data(self, data: dict[str, Any]) -> bool:
        """
        Add data to pending transactions.
        
        Args:
            data: Data to be included in next block
            
        Returns:
            True if data was accepted, False if rejected
        """
        # Check mempool limit
        if len(self.pending_data) >= self.max_pending:
            logger.warning("Mempool full, rejecting data")
            return False
        
        # Check item size
        data_size = len(json.dumps(data))
        if data_size > MAX_SINGLE_ITEM_SIZE:
            logger.warning(f"Data too large ({data_size} bytes), rejecting")
            return False
        
        # Run custom validator
        if self.validator and not self.validator(data):
            logger.warning("Data failed validation, rejecting")
            return False
        
        self.pending_data.append(data)
        return True
    
    def mine_pending(self) -> Optional[Block]:
        """
        Mine a new block with pending data.
        
        Returns:
            The newly mined block, or None if no pending data
        """
        if not self.pending_data:
            return None
        
        # Select data that fits in block
        block_data = []
        current_size = 0
        remaining = []
        
        for item in self.pending_data:
            item_size = len(json.dumps(item))
            if current_size + item_size <= self.max_block_size:
                block_data.append(item)
                current_size += item_size
            else:
                remaining.append(item)
        
        if not block_data:
            return None
        
        # Create and mine block
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data={"messages": block_data},
            previous_hash=self.latest_block.hash
        )
        new_block.mine(self.difficulty)
        
        # Add to chain and index
        self.chain.append(new_block)
        self._index_block(new_block)
        
        # Update pending data
        self.pending_data = remaining
        
        logger.info(f"Mined block #{new_block.index} with {len(block_data)} items")
        return new_block
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Get block by hash (O(1) lookup)."""
        return self._block_index.get(block_hash)
    
    def get_block_by_height(self, height: int) -> Optional[Block]:
        """Get block by height (O(1) lookup)."""
        return self._height_index.get(height)
    
    def get_blocks_from(self, start_height: int, count: int = 100) -> list[Block]:
        """
        Get blocks starting from height.
        
        Args:
            start_height: Starting block height
            count: Maximum number of blocks to return
            
        Returns:
            List of blocks
        """
        end_height = min(start_height + count, len(self.chain))
        return self.chain[start_height:end_height]
    
    def get_message_block(self, message_id: str) -> Optional[Block]:
        """Get the block containing a specific message."""
        height = self._message_index.get(message_id)
        if height is not None:
            return self._height_index.get(height)
        return None
    
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain.
        
        Returns:
            True if chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Verify current block's hash
            if current.hash != current.calculate_hash():
                logger.error(f"Block {i} hash mismatch")
                return False
            
            # Verify link to previous block
            if current.previous_hash != previous.hash:
                logger.error(f"Block {i} chain link broken")
                return False
            
            # Verify proof of work
            if not current.hash.startswith("0" * self.difficulty):
                logger.error(f"Block {i} PoW invalid")
                return False
        
        return True
    
    def validate_chain(self, chain: list[Block]) -> bool:
        """
        Validate an external chain.
        
        Args:
            chain: Chain to validate
            
        Returns:
            True if valid
        """
        if not chain:
            return False
        
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
            if not current.hash.startswith("0" * self.difficulty):
                return False
        
        return True
    
    def should_accept_chain(self, remote_status: ChainStatus) -> bool:
        """
        Determine if we should sync with a remote chain.
        
        Uses longest chain rule with total work comparison.
        
        Args:
            remote_status: Status of remote chain
            
        Returns:
            True if remote chain should be adopted
        """
        # Must have same genesis
        if remote_status.genesis_hash != self.genesis_hash:
            return False
        
        # Must have more work
        if remote_status.total_work <= self.total_work:
            return False
        
        return True
    
    def replace_chain(self, new_chain: list[Block]) -> bool:
        """
        Replace chain with a new one if valid and has more work.
        
        Args:
            new_chain: New chain to adopt
            
        Returns:
            True if chain was replaced
        """
        if not self.validate_chain(new_chain):
            logger.warning("Rejecting invalid chain")
            return False
        
        new_work = sum(2 ** self.difficulty for _ in new_chain)
        if new_work <= self.total_work:
            logger.warning("Rejecting chain with less work")
            return False
        
        logger.info(f"Replacing chain: {len(self.chain)} -> {len(new_chain)} blocks")
        self.chain = new_chain
        self._rebuild_index()
        return True
    
    def get_messages(self) -> list[dict[str, Any]]:
        """
        Get all messages from the blockchain.
        
        Returns:
            List of all message data in the chain
        """
        messages = []
        for block in self.chain[1:]:  # Skip genesis
            if "messages" in block.data:
                messages.extend(block.data["messages"])
        return messages
    
    def get_merkle_proof(self, message_id: str) -> Optional[MerkleProof]:
        """
        Generate Merkle proof for a message.
        
        Args:
            message_id: ID of message to prove
            
        Returns:
            MerkleProof if message found, None otherwise
        """
        block = self.get_message_block(message_id)
        if not block or "messages" not in block.data:
            return None
        
        messages = block.data["messages"]
        
        # Find message index
        msg_idx = None
        for i, msg in enumerate(messages):
            if isinstance(msg, dict) and msg.get("id") == message_id:
                msg_idx = i
                break
        
        if msg_idx is None:
            return None
        
        # Build proof path
        hashes = [hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()
                 for m in messages]
        data_hash = hashes[msg_idx]
        proof_path = []
        
        idx = msg_idx
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            
            if idx % 2 == 0:
                sibling_idx = idx + 1
                position = "right"
            else:
                sibling_idx = idx - 1
                position = "left"
            
            if sibling_idx < len(hashes):
                proof_path.append((hashes[sibling_idx], position))
            
            # Move up tree
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = next_level
            idx = idx // 2
        
        return MerkleProof(
            block_hash=block.hash,
            block_height=block.index,
            data_hash=data_hash,
            merkle_root=block.merkle_root,
            proof_path=proof_path
        )
    
    def save(self, path: str | Path) -> None:
        """
        Atomically save blockchain to disk.
        
        Uses write-to-temp + atomic rename pattern to prevent corruption.
        
        Args:
            path: Path to save blockchain
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp file first
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix='.blockchain_',
            suffix='.tmp'
        )
        
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            
            # Atomic rename (POSIX guarantees atomicity)
            os.replace(tmp_path, path)
            logger.debug(f"Saved blockchain to {path}")
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise BlockchainError(f"Failed to save blockchain: {e}") from e
    
    @classmethod
    def load(cls, path: str | Path) -> "Blockchain":
        """
        Load blockchain from disk.
        
        Args:
            path: Path to load from
            
        Returns:
            Loaded blockchain
        """
        path = Path(path)
        
        if not path.exists():
            raise BlockchainError(f"Blockchain file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            blockchain = cls.from_dict(data)
            logger.info(f"Loaded blockchain: {len(blockchain)} blocks")
            return blockchain
            
        except json.JSONDecodeError as e:
            raise BlockchainError(f"Invalid blockchain file: {e}") from e
    
    def to_dict(self) -> dict[str, Any]:
        """Convert blockchain to dictionary representation."""
        return {
            "version": 2,  # Schema version for future compatibility
            "difficulty": self.difficulty,
            "chain": [block.to_dict() for block in self.chain],
            "pending_data": self.pending_data
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blockchain":
        """Create a Blockchain from dictionary representation."""
        blockchain = cls.__new__(cls)
        blockchain.difficulty = data["difficulty"]
        blockchain.chain = [Block.from_dict(b) for b in data["chain"]]
        blockchain.pending_data = data.get("pending_data", [])
        blockchain.validator = None
        blockchain.max_block_size = MAX_BLOCK_SIZE
        blockchain.max_pending = MAX_PENDING_DATA
        
        # Initialize indexes
        blockchain._block_index = {}
        blockchain._height_index = {}
        blockchain._message_index = {}
        blockchain._rebuild_index()
        
        return blockchain
    
    def __len__(self) -> int:
        """Return the length of the chain."""
        return len(self.chain)
    
    def __repr__(self) -> str:
        return f"Blockchain(blocks={len(self.chain)}, pending={len(self.pending_data)}, work={self.total_work})"


def calculate_merkle_root(data_list: list[bytes]) -> str:
    """
    Calculate Merkle root hash for a list of data.
    
    This is used for efficient verification of message batches.
    
    Args:
        data_list: List of data items to hash
        
    Returns:
        Merkle root hash as hex string
    """
    if not data_list:
        return hashlib.sha256(b"").hexdigest()
    
    # Hash each item
    hashes = [hashlib.sha256(data).hexdigest() for data in data_list]
    
    # Build tree
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])  # Duplicate last hash if odd
        
        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
        hashes = next_level
    
    return hashes[0]


def generate_merkle_path(
    data_list: list[bytes],
    target_index: int
) -> list[tuple[str, str]]:
    """
    Generate Merkle proof path for an item.
    
    Args:
        data_list: List of data items
        target_index: Index of item to prove
        
    Returns:
        List of (sibling_hash, position) tuples
    """
    if not data_list or target_index >= len(data_list):
        return []
    
    hashes = [hashlib.sha256(data).hexdigest() for data in data_list]
    proof_path = []
    idx = target_index
    
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        
        if idx % 2 == 0:
            sibling_idx = idx + 1
            position = "right"
        else:
            sibling_idx = idx - 1
            position = "left"
        
        if sibling_idx < len(hashes):
            proof_path.append((hashes[sibling_idx], position))
        
        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
        hashes = next_level
        idx = idx // 2
    
    return proof_path
