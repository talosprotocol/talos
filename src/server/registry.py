"""
Registry server for peer discovery and management.

The registry server:
- Accepts client registrations
- Maintains a directory of active peers
- Provides peer lists for discovery
- Acts as a bootstrap node for new clients
"""

import asyncio
import json
import logging
import time
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional

import websockets
try:
    from websockets.asyncio.server import ServerConnection
    WebSocketServerProtocol = ServerConnection
except ImportError:
    try:
        from websockets.server import WebSocketServerProtocol
    except ImportError:
        WebSocketServerProtocol = Any

from ..core.crypto import Wallet
from ..network.peer import Peer, PeerState
from ..network.protocol import (
    ProtocolFrame,
    FrameType,
    HandshakeMessage,
    HandshakeAck,
    PROTOCOL_VERSION,
    DEFAULT_CAPABILITIES,
)

logger = logging.getLogger(__name__)


class RegisteredClient(BaseModel):
    """A client registered with the registry."""

    peer_id: str
    name: Optional[str]
    address: str
    port: int
    public_key: bytes
    encryption_key: bytes
    registered_at: float = Field(default_factory=time.time)
    last_seen: float = Field(default_factory=time.time)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        import base64

        return {
            "peer_id": self.peer_id,
            "name": self.name,
            "address": self.address,
            "port": self.port,
            "public_key": base64.b64encode(self.public_key).decode(),
            "encryption_key": base64.b64encode(self.encryption_key).decode(),
            "registered_at": self.registered_at,
            "last_seen": self.last_seen
        }

    def to_peer(self) -> Peer:
        """Convert to Peer object."""
        return Peer(
            id=self.peer_id,
            address=self.address,
            port=self.port,
            public_key=self.public_key,
            encryption_key=self.encryption_key,
            name=self.name,
            state=PeerState.CONNECTED
        )


class Registry:
    """
    Registry for managing client registrations.
    
    Provides a central point for peer discovery in the network.
    """

    def __init__(self, expiry_time: float = 300.0) -> None:
        """
        Initialize registry.
        
        Args:
            expiry_time: Time in seconds before a client registration expires
        """
        self._clients: dict[str, RegisteredClient] = {}
        self.expiry_time = expiry_time

    def register(
        self,
        peer_id: str,
        name: Optional[str],
        address: str,
        port: int,
        public_key: bytes,
        encryption_key: bytes
    ) -> RegisteredClient:
        """Register a new client or update existing."""
        client = RegisteredClient(
            peer_id=peer_id,
            name=name,
            address=address,
            port=port,
            public_key=public_key,
            encryption_key=encryption_key
        )
        self._clients[peer_id] = client
        logger.info(f"Registered client: {peer_id[:16]}... ({name})")
        return client

    def unregister(self, peer_id: str) -> bool:
        """Unregister a client."""
        if peer_id in self._clients:
            del self._clients[peer_id]
            logger.info(f"Unregistered client: {peer_id[:16]}...")
            return True
        return False

    def get(self, peer_id: str) -> Optional[RegisteredClient]:
        """Get a registered client."""
        return self._clients.get(peer_id)

    def update_seen(self, peer_id: str) -> bool:
        """Update last seen timestamp for a client."""
        client = self._clients.get(peer_id)
        if client:
            client.last_seen = time.time()
            return True
        return False

    def get_all(self) -> list[RegisteredClient]:
        """Get all registered clients."""
        return list(self._clients.values())

    def get_peer_list(self, exclude: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Get peer list for discovery.
        
        Args:
            exclude: Peer ID to exclude from list (usually the requester)
            
        Returns:
            List of peer dictionaries
        """
        peers = []
        for client in self._clients.values():
            if exclude and client.peer_id == exclude:
                continue
            peers.append(client.to_dict())
        return peers

    def prune_expired(self) -> list[str]:
        """Remove expired registrations."""
        now = time.time()
        expired = []

        for peer_id, client in list(self._clients.items()):
            if (now - client.last_seen) > self.expiry_time:
                del self._clients[peer_id]
                expired.append(peer_id)
                logger.info(f"Pruned expired client: {peer_id[:16]}...")

        return expired

    def __len__(self) -> int:
        return len(self._clients)

    def __contains__(self, peer_id: str) -> bool:
        return peer_id in self._clients


class RegistryServer:
    """
    WebSocket server for the registry.
    
    Handles:
    - Client registration requests
    - Peer list queries
    - Keep-alive pings
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        wallet: Optional[Wallet] = None
    ) -> None:
        """
        Initialize registry server.
        
        Args:
            host: Host address to bind
            port: Port to listen on
            wallet: Optional server identity wallet
        """
        self.host = host
        self.port = port
        self.wallet = wallet or Wallet.generate("RegistryServer")
        self.registry = Registry()

        self._server: Optional[websockets.WebSocketServer] = None
        self._connections: dict[str, WebSocketServerProtocol] = {}
        self._running = False
        self._prune_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._running

    async def _process_request(self, *args):
        """
        Intercept HTTP requests before WebSocket handshake.
        Used for health checks. Supports both legacy and new websockets API.
        """
        try:
            path = None
            if len(args) == 2:
                arg1, arg2 = args
                if isinstance(arg1, str):
                    # Legacy: (path, headers)
                    path = arg1
                else:
                    # New: (connection, request)
                    path = getattr(arg2, "path", None)

            if path == "/healthz":
                return (200, [], b"OK\n")
            
            return None
        except Exception as e:
            logger.error(f"Error in process_request: {e}")
            return None

    async def start(self) -> None:
        """Start the registry server."""
        if self._running:
            return

        self._running = True

        # compatibility: choose the right serve function
        # Prefer legacy server for reliable process_request support
        try:
            from websockets.server import serve
        except ImportError:
            try:
                from websockets.asyncio.server import serve
            except ImportError:
                from websockets import serve

        self._server = await serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
            process_request=self._process_request
        )

        # Start periodic pruning
        self._prune_task = asyncio.create_task(self._prune_loop())

        logger.info(f"Registry server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the registry server."""
        if not self._running:
            return

        self._running = False

        if self._prune_task:
            self._prune_task.cancel()

        for ws in list(self._connections.values()):
            await ws.close()
        self._connections.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Registry server stopped")

    async def _prune_loop(self) -> None:
        """Periodically prune expired registrations."""
        while self._running:
            await asyncio.sleep(60)
            self.registry.prune_expired()

    async def _handle_connection(self, ws: WebSocketServerProtocol) -> None:
        """Handle incoming WebSocket connection."""
        peer_id = None

        try:
            # Perform handshake and registration
            peer_id = await self._handle_handshake(ws)
            if not peer_id:
                await ws.close()
                return

            self._connections[peer_id] = ws

            # Handle messages
            async for data in ws:
                if isinstance(data, str):
                    data = data.encode()

                try:
                    await self._handle_message(data, peer_id, ws)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            if peer_id:
                self._connections.pop(peer_id, None)
                logger.info(f"Client disconnected: {peer_id[:16]}...")

    async def _handle_handshake(
        self,
        ws: WebSocketServerProtocol
    ) -> Optional[str]:
        """Handle client handshake and registration."""
        try:
            data = await asyncio.wait_for(ws.recv(), timeout=10.0)
            if isinstance(data, str):
                data = data.encode()

            frame, _ = ProtocolFrame.from_bytes(data)

            if frame.frame_type != FrameType.HANDSHAKE:
                return None

            handshake = HandshakeMessage.from_frame(frame)

            # Get client address
            remote = ws.remote_address
            address = remote[0] if remote else "unknown"

            # Register the client
            # Use a default port for now - client should specify in metadata
            self.registry.register(
                peer_id=handshake.peer_id,
                name=handshake.name,
                address=address,
                port=8766,  # Default P2P port for clients
                public_key=handshake.signing_key,
                encryption_key=handshake.encryption_key
            )

            # Send our handshake
            our_handshake = HandshakeMessage(
                version=PROTOCOL_VERSION,
                peer_id=self.wallet.address,
                name="RegistryServer",
                signing_key=self.wallet.signing_keys.public_key,
                encryption_key=self.wallet.encryption_keys.public_key,
                capabilities=["registry"] + DEFAULT_CAPABILITIES
            )
            await ws.send(our_handshake.to_frame().to_bytes())

            # Send ack with peer list
            ack = HandshakeAck(
                accepted=True,
                peer_id=self.wallet.address
            )
            await ws.send(ack.to_frame().to_bytes())

            # Send peer list
            peer_list = self.registry.get_peer_list(exclude=handshake.peer_id)
            peer_list_msg = json.dumps({
                "type": "peer_list",
                "peers": peer_list
            }).encode()
            await ws.send(ProtocolFrame.data(peer_list_msg).to_bytes())

            return handshake.peer_id

        except asyncio.TimeoutError:
            logger.warning("Handshake timeout")
            return None
        except Exception as e:
            logger.error(f"Handshake error: {e}")
            return None

    async def _handle_message(
        self,
        data: bytes,
        peer_id: str,
        ws: WebSocketServerProtocol
    ) -> None:
        """Handle incoming message from client."""
        frame, _ = ProtocolFrame.from_bytes(data)

        # Update last seen
        self.registry.update_seen(peer_id)

        if frame.frame_type == FrameType.PING:
            await ws.send(ProtocolFrame.pong().to_bytes())

        elif frame.frame_type == FrameType.DATA:
            # Parse as JSON command
            try:
                cmd = json.loads(frame.payload.decode())
                await self._handle_command(cmd, peer_id, ws)
            except json.JSONDecodeError:
                pass

    async def _handle_command(
        self,
        cmd: dict[str, Any],
        peer_id: str,
        ws: WebSocketServerProtocol
    ) -> None:
        """Handle registry command."""
        cmd_type = cmd.get("type")

        if cmd_type == "get_peers":
            peer_list = self.registry.get_peer_list(exclude=peer_id)
            response = json.dumps({
                "type": "peer_list",
                "peers": peer_list
            }).encode()
            await ws.send(ProtocolFrame.data(response).to_bytes())

        elif cmd_type == "lookup":
            target_id = cmd.get("peer_id")
            client = self.registry.get(target_id)
            if client:
                response = json.dumps({
                    "type": "lookup_result",
                    "found": True,
                    "peer": client.to_dict()
                }).encode()
            else:
                response = json.dumps({
                    "type": "lookup_result",
                    "found": False,
                    "peer_id": target_id
                }).encode()
            await ws.send(ProtocolFrame.data(response).to_bytes())

        elif cmd_type == "update_port":
            # Allow client to update their P2P port
            new_port = cmd.get("port")
            client = self.registry.get(peer_id)
            if client and new_port:
                client.port = new_port
                logger.info(f"Updated port for {peer_id[:16]}... to {new_port}")

    async def broadcast_peer_update(self, new_peer: RegisteredClient) -> None:
        """Broadcast new peer to all connected clients."""
        update = json.dumps({
            "type": "peer_joined",
            "peer": new_peer.to_dict()
        }).encode()
        frame = ProtocolFrame.data(update)

        for ws in self._connections.values():
            try:
                await ws.send(frame.to_bytes())
            except Exception:
                pass
