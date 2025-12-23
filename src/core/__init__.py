"""
Core blockchain and cryptography components.

This package provides:
- Blockchain: Production-ready blockchain with indexing and sync support
- Block: Individual block with Merkle root calculation
- ChainSynchronizer: Peer chain synchronization
- Cryptographic primitives: Signatures, encryption, hashing
- Message protocol: Message types and serialization
"""

from .blockchain import (
    Block,
    Blockchain,
    ChainStatus,
    MerkleProof,
    BlockchainError,
    BlockValidationError,
    ChainValidationError,
    DataRejectedError,
    calculate_merkle_root,
    generate_merkle_path,
    MAX_BLOCK_SIZE,
    MAX_PENDING_DATA,
)

from .sync import (
    ChainSynchronizer,
    SyncState,
    SyncProgress,
    SyncRequest,
)

from .crypto import (
    Wallet,
    KeyPair,
    sign_message,
    verify_signature,
    encrypt_message,
    decrypt_message,
    derive_shared_secret,
    hash_data,
    hash_string,
    generate_signing_keypair,
    generate_encryption_keypair,
)

from .message import (
    MessageType,
    MessagePayload,
    ChunkInfo,
    create_text_message,
    create_ack_message,
)

__all__ = [
    # Blockchain
    "Block",
    "Blockchain",
    "ChainStatus",
    "MerkleProof",
    "BlockchainError",
    "BlockValidationError",
    "ChainValidationError",
    "DataRejectedError",
    "calculate_merkle_root",
    "generate_merkle_path",
    "MAX_BLOCK_SIZE",
    "MAX_PENDING_DATA",
    # Sync
    "ChainSynchronizer",
    "SyncState",
    "SyncProgress",
    "SyncRequest",
    # Crypto
    "Wallet",
    "KeyPair",
    "sign_message",
    "verify_signature",
    "encrypt_message",
    "decrypt_message",
    "derive_shared_secret",
    "hash_data",
    "hash_string",
    "generate_signing_keypair",
    "generate_encryption_keypair",
    # Message
    "MessageType",
    "MessagePayload",
    "ChunkInfo",
    "create_text_message",
    "create_ack_message",
]
