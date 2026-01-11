
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from src.server.registry import Registry, RegistryServer, RegisteredClient
from src.core.crypto import Wallet
from src.network.protocol import HandshakeMessage, DEFAULT_CAPABILITIES, PROTOCOL_VERSION

@pytest.fixture
def mock_wallet():
    return Wallet.generate()

@pytest.fixture
def registry():
    return Registry(expiry_time=1.0)

def test_registered_client_model():
    """Test RegisteredClient Pydantic model"""
    client = RegisteredClient(
        peer_id="abc",
        name="test",
        address="1.2.3.4",
        port=8000,
        public_key=b"key",
        encryption_key=b"enc"
    )
    assert client.peer_id == "abc"
    assert client.to_dict()["peer_id"] == "abc"

def test_registry_lifecycle(registry):
    """Test register, check, and unregister"""
    # Register
    client = registry.register(
        peer_id="peer1",
        name="Peer 1",
        address="localhost",
        port=8000,
        public_key=b"pk",
        encryption_key=b"ek"
    )
    assert "peer1" in registry
    assert len(registry) == 1
    assert registry.get("peer1") == client

    # Update seen
    old_seen = client.last_seen
    time.sleep(0.01)
    registry.update_seen("peer1")
    assert client.last_seen > old_seen

    # Get all
    assert len(registry.get_all()) == 1

    # Get peer list
    peers = registry.get_peer_list(exclude="other")
    assert len(peers) == 1
    peers_excl = registry.get_peer_list(exclude="peer1")
    assert len(peers_excl) == 0

    # Unregister
    assert registry.unregister("peer1")
    assert "peer1" not in registry
    assert not registry.unregister("peer1")

def test_registry_pruning(registry):
    """Test pruning of expired clients"""
    registry.register(
        peer_id="peer1", name="p1", address="loc", port=1,
        public_key=b"k", encryption_key=b"e"
    )

    # Not expired yet
    assert len(registry.prune_expired()) == 0

    # Wait for expiry
    time.sleep(1.1)

    # Should expire
    expired = registry.prune_expired()
    assert "peer1" in expired
    assert len(registry) == 0

@pytest.mark.asyncio
async def test_registry_server_start_stop():
    """Test server start/stop logic"""
    server = RegistryServer(port=0)

    # Mock websockets.serve at the correct import path
    with patch("websockets.server.serve", new_callable=AsyncMock) as mock_serve:
        mock_serve.return_value.close = MagicMock()
        mock_serve.return_value.wait_closed = AsyncMock()

        await server.start()
        assert server.is_running

        await server.stop()
        assert not server.is_running

@pytest.mark.asyncio
async def test_registry_handle_client(registry):
    """Test client handling logic (Handshake)"""
    server = RegistryServer(port=0)
    server.registry = registry

    mock_ws = AsyncMock()
    mock_ws.remote_address = ("127.0.0.1", 12345)

    # Create valid HandshakeMessage
    handshake = HandshakeMessage(
        version=PROTOCOL_VERSION,
        peer_id="p1",
        name="TestClient",
        signing_key=b"pubkey",
        encryption_key=b"enckey",
        capabilities=DEFAULT_CAPABILITIES
    )

    # Convert to frame bytes
    frame_bytes = handshake.to_frame().to_bytes()

    # Mock recv behavior
    # 1. Handshake frame
    # 2. Connection closed (to break loop)
    mock_ws.recv.side_effect = [frame_bytes, asyncio.CancelledError()]

    try:
        await server._handle_connection(mock_ws)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass

    # Verify registration
    assert "p1" in server.registry
    val = server.registry.get("p1")
    assert val.name == "TestClient"
    assert val.address == "127.0.0.1"

    # Check that send was called (Handshake response + ACK + PeerList)
    assert mock_ws.send.call_count >= 1
