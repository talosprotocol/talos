"""
Message protocol definitions for the blockchain messaging system.

This module defines:
- Message types (TEXT, STREAM_*, ACK, etc.)
- MessagePayload structure with serialization
- Message validation utilities
"""

import json
import time
import uuid
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum, auto
from typing import Any, Optional

import msgpack


class MessageType(Enum):
    """Types of messages in the protocol."""
    
    # Basic messaging
    TEXT = auto()
    ACK = auto()
    
    # File transfer
    FILE = auto()           # File transfer start with metadata
    FILE_CHUNK = auto()     # File data chunk
    FILE_COMPLETE = auto()  # File transfer completion
    FILE_ERROR = auto()     # File transfer error
    
    # Streaming (for future audio/video)
    STREAM_START = auto()
    STREAM_CHUNK = auto()
    STREAM_END = auto()
    
    # Control messages
    HANDSHAKE = auto()
    HANDSHAKE_ACK = auto()
    PEER_DISCOVERY = auto()
    PING = auto()
    PONG = auto()
    
    # Registry messages
    REGISTER = auto()
    REGISTER_ACK = auto()
    PEER_LIST = auto()

    # MCP (Model Context Protocol) messages
    MCP_MESSAGE = auto()       # JSON-RPC request/notification
    MCP_RESPONSE = auto()      # JSON-RPC response
    MCP_ERROR = auto()         # MCP-specific transport error
    
    # Chain synchronization
    CHAIN_STATUS = auto()      # Share/request chain status
    CHAIN_REQUEST = auto()     # Request specific blocks
    CHAIN_RESPONSE = auto()    # Send blocks in response
    CHAIN_SYNC_START = auto()  # Begin sync process
    CHAIN_SYNC_END = auto()    # End sync process


class ChunkInfo(BaseModel):
    """
    Information about a chunk in a streaming message.
    
    Used for reassembling chunked data (text, audio, video).
    """
    
    sequence: int
    total: int
    stream_id: str
    hash: str  # Hash of chunk data for verification

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "total": self.total,
            "stream_id": self.stream_id,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkInfo":
        return cls(
            sequence=data["sequence"],
            total=data["total"],
            stream_id=data["stream_id"],
            hash=data["hash"]
        )


class MessagePayload(BaseModel):
    """
    The core message structure for the protocol.
    
    All messages in the system use this structure, whether they're
    simple text messages, streaming chunks, or control messages.
    """
    
    id: str
    type: MessageType
    sender: str  # Sender's public key (hex)
    recipient: str  # Recipient's public key (hex), or "*" for broadcast
    timestamp: float
    content: bytes  # Encrypted content
    signature: bytes  # Sender's signature
    nonce: Optional[bytes] = None  # Encryption nonce
    chunk_info: Optional[ChunkInfo] = None  # For streaming
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @classmethod
    def create(
        cls,
        msg_type: MessageType,
        sender: str,
        recipient: str,
        content: bytes,
        signature: bytes,
        nonce: Optional[bytes] = None,
        chunk_info: Optional[ChunkInfo] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> "MessagePayload":
        """Create a new message with auto-generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            type=msg_type,
            sender=sender,
            recipient=recipient,
            timestamp=time.time(),
            content=content,
            signature=signature,
            nonce=nonce,
            chunk_info=chunk_info,
            metadata=metadata or {}
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        import base64
        
        result = {
            "id": self.id,
            "type": self.type.name,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "content": base64.b64encode(self.content).decode(),
            "signature": base64.b64encode(self.signature).decode(),
            "metadata": self.metadata
        }
        
        if self.nonce:
            result["nonce"] = base64.b64encode(self.nonce).decode()
        
        if self.chunk_info:
            result["chunk_info"] = self.chunk_info.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessagePayload":
        """Create from dictionary."""
        import base64
        
        chunk_info = None
        if "chunk_info" in data and data["chunk_info"]:
            chunk_info = ChunkInfo.from_dict(data["chunk_info"])
        
        nonce = None
        if "nonce" in data and data["nonce"]:
            nonce = base64.b64decode(data["nonce"])
        
        return cls(
            id=data["id"],
            type=MessageType[data["type"]],
            sender=data["sender"],
            recipient=data["recipient"],
            timestamp=data["timestamp"],
            content=base64.b64decode(data["content"]),
            signature=base64.b64decode(data["signature"]),
            nonce=nonce,
            chunk_info=chunk_info,
            metadata=data.get("metadata", {})
        )
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes using MessagePack for efficiency."""
        return msgpack.packb(self.to_dict())
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "MessagePayload":
        """Deserialize from MessagePack bytes."""
        return cls.from_dict(msgpack.unpackb(data, raw=False))
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, data: str) -> "MessagePayload":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(data))
    
    def get_signable_content(self) -> bytes:
        """
        Get the content that should be signed.
        
        This excludes the signature itself to avoid circular dependencies.
        """
        import base64
        
        signable = {
            "id": self.id,
            "type": self.type.name,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "content": base64.b64encode(self.content).decode()
        }
        
        if self.nonce:
            signable["nonce"] = base64.b64encode(self.nonce).decode()
        
        if self.chunk_info:
            signable["chunk_info"] = self.chunk_info.to_dict()
        
        return json.dumps(signable, sort_keys=True).encode()
    
    @property
    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return self.recipient == "*"
    
    @property
    def is_streaming(self) -> bool:
        """Check if this is part of a stream."""
        return self.type in (
            MessageType.STREAM_START,
            MessageType.STREAM_CHUNK,
            MessageType.STREAM_END
        )
    
    def __repr__(self) -> str:
        sender_short = f"{self.sender[:8]}..." if len(self.sender) > 8 else self.sender
        recipient_short = f"{self.recipient[:8]}..." if len(self.recipient) > 8 else self.recipient
        return (
            f"MessagePayload(type={self.type.name}, "
            f"sender={sender_short}, recipient={recipient_short})"
        )


def create_text_message(
    sender: str,
    recipient: str,
    text: str,
    sign_func,
    encrypt_func=None,
    recipient_public_key: Optional[bytes] = None
) -> MessagePayload:
    """
    Convenience function to create a text message.
    
    Args:
        sender: Sender's public key hex
        recipient: Recipient's public key hex
        text: Plain text message
        sign_func: Function to sign message (takes bytes, returns signature)
        encrypt_func: Optional function to encrypt (takes plaintext, key -> nonce, ciphertext)
        recipient_public_key: Recipient's encryption public key if encrypting
        
    Returns:
        A ready-to-send MessagePayload
    """
    content = text.encode()
    nonce = None
    
    # Encrypt if we have the function and key
    if encrypt_func and recipient_public_key:
        nonce, content = encrypt_func(content, recipient_public_key)
    
    # Create message without signature first
    msg = MessagePayload(
        id=str(uuid.uuid4()),
        type=MessageType.TEXT,
        sender=sender,
        recipient=recipient,
        timestamp=time.time(),
        content=content,
        signature=b"",  # Placeholder
        nonce=nonce
    )
    
    # Sign and update
    signature = sign_func(msg.get_signable_content())
    msg.signature = signature
    
    return msg


def create_ack_message(
    sender: str,
    recipient: str,
    original_message_id: str,
    sign_func
) -> MessagePayload:
    """Create an acknowledgment message."""
    content = json.dumps({"ack_for": original_message_id}).encode()
    
    msg = MessagePayload(
        id=str(uuid.uuid4()),
        type=MessageType.ACK,
        sender=sender,
        recipient=recipient,
        timestamp=time.time(),
        content=content,
        signature=b""
    )
    
    signature = sign_func(msg.get_signable_content())
    msg.signature = signature
    
    return msg
