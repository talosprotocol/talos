"""
Peer representation and management for the P2P network.

This module defines:
- Peer class representing a network participant
- PeerManager for tracking and managing connections
"""

import time
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from enum import Enum, auto
from typing import Optional
import base64


class PeerState(Enum):
    """Connection state of a peer."""
    
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    HANDSHAKING = auto()
    AUTHENTICATED = auto()


class Peer(BaseModel):
    """
    Represents a peer in the P2P network.
    
    Each peer has an identity (public key), network address,
    and connection state information.
    """
    
    id: str  # Unique peer ID (usually public key hex)
    address: str  # Host address
    port: int  # Port number
    public_key: Optional[bytes] = None  # Signing public key
    encryption_key: Optional[bytes] = None  # Encryption public key
    state: PeerState = PeerState.DISCONNECTED
    last_seen: float = Field(default_factory=time.time)
    name: Optional[str] = None  # Human-readable name
    metadata: dict = Field(default_factory=dict)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_serializer('public_key', 'encryption_key')
    def serialize_keys(self, v: Optional[bytes], _info):
        if v is None:
            return None
        return base64.b64encode(v).decode()
        
    @field_serializer('state')
    def serialize_state(self, v: PeerState, _info):
        return v.name
    
    @property
    def endpoint(self) -> str:
        """Get the full endpoint address."""
        return f"{self.address}:{self.port}"
    
    @property
    def ws_url(self) -> str:
        """Get WebSocket URL for this peer."""
        return f"ws://{self.address}:{self.port}"
    
    @property
    def is_connected(self) -> bool:
        """Check if peer is currently connected."""
        return self.state in (PeerState.CONNECTED, PeerState.AUTHENTICATED)
    
    @property
    def is_authenticated(self) -> bool:
        """Check if peer has completed handshake."""
        return self.state == PeerState.AUTHENTICATED
    
    def update_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = time.time()
    
    def to_dict(self) -> dict:
        """Convert peer to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> "Peer":
        """Create peer from dictionary."""
        import base64
        
        public_key = None
        if "public_key" in data and data["public_key"]:
            public_key = base64.b64decode(data["public_key"])
        
        encryption_key = None
        if "encryption_key" in data and data["encryption_key"]:
            encryption_key = base64.b64decode(data["encryption_key"])
        
        return cls(
            id=data["id"],
            address=data["address"],
            port=data["port"],
            public_key=public_key,
            encryption_key=encryption_key,
            state=PeerState[data.get("state", "DISCONNECTED")],
            last_seen=data.get("last_seen", time.time()),
            name=data.get("name"),
            metadata=data.get("metadata", {})
        )
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Peer):
            return self.id == other.id
        return False
    
    def __repr__(self) -> str:
        name = f" ({self.name})" if self.name else ""
        id_short = f"{self.id[:8]}..." if len(self.id) > 8 else self.id
        return f"Peer({id_short}{name} @ {self.endpoint}, {self.state.name})"


class PeerManager:
    """
    Manages the collection of known peers.
    
    Provides functionality for:
    - Adding/removing peers
    - Looking up peers by ID or address
    - Tracking connection states
    - Pruning stale peers
    """
    
    def __init__(self, stale_timeout: float = 300.0) -> None:
        """
        Initialize peer manager.
        
        Args:
            stale_timeout: Seconds before a peer is considered stale
        """
        self._peers: dict[str, Peer] = {}
        self._address_index: dict[str, str] = {}  # endpoint -> peer_id
        self.stale_timeout = stale_timeout
    
    def add(self, peer: Peer) -> None:
        """Add or update a peer."""
        self._peers[peer.id] = peer
        self._address_index[peer.endpoint] = peer.id
    
    def remove(self, peer_id: str) -> Optional[Peer]:
        """Remove a peer by ID."""
        peer = self._peers.pop(peer_id, None)
        if peer:
            self._address_index.pop(peer.endpoint, None)
        return peer
    
    def get(self, peer_id: str) -> Optional[Peer]:
        """Get peer by ID."""
        return self._peers.get(peer_id)
    
    def get_by_address(self, endpoint: str) -> Optional[Peer]:
        """Get peer by endpoint address."""
        peer_id = self._address_index.get(endpoint)
        if peer_id:
            return self._peers.get(peer_id)
        return None
    
    def get_connected(self) -> list[Peer]:
        """Get all connected peers."""
        return [p for p in self._peers.values() if p.is_connected]
    
    def get_authenticated(self) -> list[Peer]:
        """Get all authenticated peers."""
        return [p for p in self._peers.values() if p.is_authenticated]
    
    def get_all(self) -> list[Peer]:
        """Get all known peers."""
        return list(self._peers.values())
    
    def update_state(self, peer_id: str, state: PeerState) -> bool:
        """Update a peer's connection state."""
        peer = self._peers.get(peer_id)
        if peer:
            peer.state = state
            if state == PeerState.CONNECTED:
                peer.update_seen()
            return True
        return False
    
    def prune_stale(self) -> list[Peer]:
        """Remove and return stale peers."""
        now = time.time()
        stale = []
        
        for peer in list(self._peers.values()):
            if (now - peer.last_seen) > self.stale_timeout:
                self.remove(peer.id)
                stale.append(peer)
        
        return stale
    
    def __len__(self) -> int:
        return len(self._peers)
    
    def __contains__(self, peer_id: str) -> bool:
        return peer_id in self._peers
    
    def __iter__(self):
        return iter(self._peers.values())
