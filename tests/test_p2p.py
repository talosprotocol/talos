"""
Tests for P2P networking and protocol modules.
"""

import pytest

from src.network.peer import Peer, PeerManager, PeerState
from src.network.protocol import (
    ProtocolFrame,
    FrameType,
    HandshakeMessage,
    HandshakeAck,
    PROTOCOL_VERSION,
    PROTOCOL_MAGIC,
)


class TestPeer:
    """Tests for Peer class."""
    
    def test_peer_creation(self):
        """Test peer can be created."""
        peer = Peer(
            id="peer123",
            address="192.168.1.1",
            port=8765
        )
        
        assert peer.id == "peer123"
        assert peer.address == "192.168.1.1"
        assert peer.port == 8765
        assert peer.state == PeerState.DISCONNECTED
    
    def test_peer_endpoint(self):
        """Test endpoint property."""
        peer = Peer(id="test", address="localhost", port=8080)
        
        assert peer.endpoint == "localhost:8080"
        assert peer.ws_url == "ws://localhost:8080"
    
    def test_peer_connection_state(self):
        """Test connection state properties."""
        peer = Peer(id="test", address="localhost", port=8080)
        
        assert peer.is_connected is False
        assert peer.is_authenticated is False
        
        peer.state = PeerState.CONNECTED
        assert peer.is_connected is True
        assert peer.is_authenticated is False
        
        peer.state = PeerState.AUTHENTICATED
        assert peer.is_connected is True
        assert peer.is_authenticated is True
    
    def test_peer_serialization(self):
        """Test peer to/from dict."""
        original = Peer(
            id="test-peer",
            address="10.0.0.1",
            port=9000,
            name="TestPeer",
            public_key=b"pubkey123",
            encryption_key=b"enckey456"
        )
        
        data = original.to_dict()
        restored = Peer.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.public_key == original.public_key


class TestPeerManager:
    """Tests for PeerManager class."""
    
    def test_add_and_get_peer(self):
        """Test adding and retrieving peers."""
        manager = PeerManager()
        peer = Peer(id="peer1", address="localhost", port=8080)
        
        manager.add(peer)
        
        assert len(manager) == 1
        assert manager.get("peer1") == peer
    
    def test_get_by_address(self):
        """Test getting peer by address."""
        manager = PeerManager()
        peer = Peer(id="peer1", address="localhost", port=8080)
        manager.add(peer)
        
        found = manager.get_by_address("localhost:8080")
        
        assert found == peer
    
    def test_remove_peer(self):
        """Test removing peers."""
        manager = PeerManager()
        peer = Peer(id="peer1", address="localhost", port=8080)
        manager.add(peer)
        
        removed = manager.remove("peer1")
        
        assert removed == peer
        assert len(manager) == 0
    
    def test_get_connected_peers(self):
        """Test getting connected peers only."""
        manager = PeerManager()
        
        peer1 = Peer(id="p1", address="h1", port=1, state=PeerState.CONNECTED)
        peer2 = Peer(id="p2", address="h2", port=2, state=PeerState.DISCONNECTED)
        peer3 = Peer(id="p3", address="h3", port=3, state=PeerState.AUTHENTICATED)
        
        manager.add(peer1)
        manager.add(peer2)
        manager.add(peer3)
        
        connected = manager.get_connected()
        
        assert len(connected) == 2
        assert peer1 in connected
        assert peer3 in connected


class TestProtocolFrame:
    """Tests for ProtocolFrame class."""
    
    def test_frame_creation(self):
        """Test frame can be created."""
        frame = ProtocolFrame(
            frame_type=FrameType.DATA,
            payload=b"test data"
        )
        
        assert frame.frame_type == FrameType.DATA
        assert frame.payload == b"test data"
    
    def test_frame_serialization(self):
        """Test frame to/from bytes."""
        original = ProtocolFrame(
            frame_type=FrameType.DATA,
            payload=b"Hello, Protocol!"
        )
        
        data = original.to_bytes()
        restored, consumed = ProtocolFrame.from_bytes(data)
        
        assert restored.frame_type == original.frame_type
        assert restored.payload == original.payload
        assert consumed == len(data)
    
    def test_frame_magic_header(self):
        """Test frame starts with magic bytes."""
        frame = ProtocolFrame.data(b"test")
        data = frame.to_bytes()
        
        assert data.startswith(PROTOCOL_MAGIC)
    
    def test_ping_pong_frames(self):
        """Test ping/pong frame creation."""
        ping = ProtocolFrame.ping()
        pong = ProtocolFrame.pong()
        
        assert ping.frame_type == FrameType.PING
        assert pong.frame_type == FrameType.PONG


class TestHandshake:
    """Tests for handshake messages."""
    
    def test_handshake_message_creation(self):
        """Test handshake message can be created."""
        hs = HandshakeMessage(
            version=PROTOCOL_VERSION,
            peer_id="peer123",
            name="TestPeer",
            signing_key=b"sign_key",
            encryption_key=b"enc_key",
            capabilities=["text"]
        )
        
        assert hs.version == PROTOCOL_VERSION
        assert hs.peer_id == "peer123"
        assert hs.name == "TestPeer"
    
    def test_handshake_to_frame(self):
        """Test handshake message to frame conversion."""
        hs = HandshakeMessage(
            version=1,
            peer_id="test",
            name="Test",
            signing_key=b"sk",
            encryption_key=b"ek",
            capabilities=[]
        )
        
        frame = hs.to_frame()
        
        assert frame.frame_type == FrameType.HANDSHAKE
    
    def test_handshake_ack(self):
        """Test handshake acknowledgment."""
        ack = HandshakeAck(
            accepted=True,
            peer_id="peer123"
        )
        
        frame = ack.to_frame()
        restored = HandshakeAck.from_frame(frame)
        
        assert restored.accepted is True
        assert restored.peer_id == "peer123"
