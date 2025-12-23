"""
Wire protocol definitions for P2P communication.

This module defines:
- Protocol frame structure
- Handshake messages
- Protocol versioning
"""

import json
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional

# Protocol constants
PROTOCOL_VERSION = 1
PROTOCOL_MAGIC = b"BMP\x01"  # Blockchain Messaging Protocol v1
MAX_FRAME_SIZE = 16 * 1024 * 1024  # 16MB max frame


class FrameType(IntEnum):
    """Types of protocol frames."""
    
    DATA = 0x01
    HANDSHAKE = 0x02
    HANDSHAKE_ACK = 0x03
    PING = 0x04
    PONG = 0x05
    ERROR = 0x06
    CLOSE = 0x07


@dataclass
class ProtocolFrame:
    """
    A frame in the wire protocol.
    
    Frame structure:
    - 4 bytes: Magic number (BMP\x01)
    - 1 byte: Frame type
    - 4 bytes: Payload length (big-endian)
    - N bytes: Payload (JSON or binary)
    """
    
    frame_type: FrameType
    payload: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize frame to bytes."""
        return (
            PROTOCOL_MAGIC +
            struct.pack("!B", self.frame_type) +
            struct.pack("!I", len(self.payload)) +
            self.payload
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> tuple["ProtocolFrame", int]:
        """
        Deserialize frame from bytes.
        
        Returns:
            Tuple of (frame, bytes_consumed)
        """
        if len(data) < 9:  # Minimum frame size
            raise ValueError("Incomplete frame header")
        
        if data[:4] != PROTOCOL_MAGIC:
            raise ValueError("Invalid protocol magic")
        
        frame_type = FrameType(data[4])
        payload_len = struct.unpack("!I", data[5:9])[0]
        
        if payload_len > MAX_FRAME_SIZE:
            raise ValueError(f"Frame too large: {payload_len} bytes")
        
        total_len = 9 + payload_len
        if len(data) < total_len:
            raise ValueError("Incomplete frame payload")
        
        payload = data[9:total_len]
        return cls(frame_type=frame_type, payload=payload), total_len
    
    @classmethod
    def data(cls, payload: bytes) -> "ProtocolFrame":
        """Create a data frame."""
        return cls(FrameType.DATA, payload)
    
    @classmethod
    def ping(cls) -> "ProtocolFrame":
        """Create a ping frame."""
        return cls(FrameType.PING, b"")
    
    @classmethod
    def pong(cls) -> "ProtocolFrame":
        """Create a pong frame."""
        return cls(FrameType.PONG, b"")
    
    @classmethod
    def error(cls, message: str) -> "ProtocolFrame":
        """Create an error frame."""
        return cls(FrameType.ERROR, message.encode())
    
    @classmethod
    def close(cls, reason: str = "") -> "ProtocolFrame":
        """Create a close frame."""
        return cls(FrameType.CLOSE, reason.encode())


@dataclass
class HandshakeMessage:
    """
    Handshake message for establishing connections.
    
    Contains identity information for peer authentication.
    """
    
    version: int
    peer_id: str  # Public key hex
    name: Optional[str]
    signing_key: bytes  # Ed25519 public key
    encryption_key: bytes  # X25519 public key
    capabilities: list[str]  # Supported features
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        import base64
        
        return {
            "version": self.version,
            "peer_id": self.peer_id,
            "name": self.name,
            "signing_key": base64.b64encode(self.signing_key).decode(),
            "encryption_key": base64.b64encode(self.encryption_key).decode(),
            "capabilities": self.capabilities
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandshakeMessage":
        """Create from dictionary."""
        import base64
        
        return cls(
            version=data["version"],
            peer_id=data["peer_id"],
            name=data.get("name"),
            signing_key=base64.b64decode(data["signing_key"]),
            encryption_key=base64.b64decode(data["encryption_key"]),
            capabilities=data.get("capabilities", [])
        )
    
    def to_frame(self) -> ProtocolFrame:
        """Create handshake protocol frame."""
        payload = json.dumps(self.to_dict()).encode()
        return ProtocolFrame(FrameType.HANDSHAKE, payload)
    
    @classmethod
    def from_frame(cls, frame: ProtocolFrame) -> "HandshakeMessage":
        """Parse from protocol frame."""
        if frame.frame_type != FrameType.HANDSHAKE:
            raise ValueError("Not a handshake frame")
        
        data = json.loads(frame.payload.decode())
        return cls.from_dict(data)


@dataclass
class HandshakeAck:
    """
    Acknowledgment for successful handshake.
    """
    
    accepted: bool
    peer_id: str
    reason: Optional[str] = None  # Rejection reason if not accepted
    
    def to_frame(self) -> ProtocolFrame:
        """Create handshake ack protocol frame."""
        payload = json.dumps({
            "accepted": self.accepted,
            "peer_id": self.peer_id,
            "reason": self.reason
        }).encode()
        return ProtocolFrame(FrameType.HANDSHAKE_ACK, payload)
    
    @classmethod
    def from_frame(cls, frame: ProtocolFrame) -> "HandshakeAck":
        """Parse from protocol frame."""
        if frame.frame_type != FrameType.HANDSHAKE_ACK:
            raise ValueError("Not a handshake ack frame")
        
        data = json.loads(frame.payload.decode())
        return cls(
            accepted=data["accepted"],
            peer_id=data["peer_id"],
            reason=data.get("reason")
        )


# Capability constants
CAP_TEXT_MESSAGING = "text"
CAP_STREAMING = "stream"
CAP_BLOCKCHAIN = "blockchain"

DEFAULT_CAPABILITIES = [CAP_TEXT_MESSAGING, CAP_BLOCKCHAIN]
