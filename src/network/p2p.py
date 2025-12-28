"""
P2P networking layer using WebSockets.

This module provides:
- P2PNode: Main node class for network participation
- Connection management
- Message routing and broadcasting
- Event handling
"""

import asyncio
import logging
from pydantic import BaseModel, ConfigDict
from typing import Any, Callable, Coroutine, Optional
import websockets
from websockets import ServerConnection, ClientConnection

from .peer import Peer, PeerManager, PeerState
from .protocol import (
    ProtocolFrame,
    FrameType,
    HandshakeMessage,
    HandshakeAck,
    PROTOCOL_VERSION,
    DEFAULT_CAPABILITIES,
)
from ..core.crypto import Wallet
from ..core.message import MessagePayload


# Type alias for compatibility
WebSocketServerProtocol = ServerConnection
WebSocketClientProtocol = ClientConnection

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


# Type aliases
MessageHandler = Callable[[MessagePayload, Peer], Coroutine[Any, Any, None]]
ConnectionHandler = Callable[[Peer], Coroutine[Any, Any, None]]


class P2PConfig(BaseModel):
    """Configuration for P2P node."""

    host: str = "0.0.0.0"
    port: int = 8765
    max_peers: int = 50
    ping_interval: float = 30.0
    ping_timeout: float = 10.0
    reconnect_interval: float = 5.0

    model_config = ConfigDict(arbitrary_types_allowed=True)


class P2PNode:
    """
    A node in the P2P messaging network.
    
    The node can:
    - Accept incoming connections (server mode)
    - Connect to other peers (client mode)
    - Route messages between peers
    - Broadcast messages to all connected peers
    """

    def __init__(
        self,
        wallet: Wallet,
        config: Optional[P2PConfig] = None
    ) -> None:
        """
        Initialize P2P node.
        
        Args:
            wallet: The node's identity wallet
            config: Optional configuration
        """
        self.wallet = wallet
        self.config = config or P2PConfig()
        self.peer_manager = PeerManager()

        # WebSocket connections
        self._server: Optional[websockets.WebSocketServer] = None
        self._connections: dict[str, WebSocketClientProtocol | WebSocketServerProtocol] = {}

        # Event handlers
        self._message_handlers: list[MessageHandler] = []
        self._connect_handlers: list[ConnectionHandler] = []
        self._disconnect_handlers: list[ConnectionHandler] = []

        # Running state
        self._running = False
        self._tasks: list[asyncio.Task] = []

    @property
    def peer_id(self) -> str:
        """Get this node's peer ID."""
        return self.wallet.address

    @property
    def is_running(self) -> bool:
        """Check if node is running."""
        return self._running

    def on_message(self, handler: MessageHandler) -> None:
        """Register a message handler."""
        self._message_handlers.append(handler)

    def on_connect(self, handler: ConnectionHandler) -> None:
        """Register a connection handler."""
        self._connect_handlers.append(handler)

    def on_disconnect(self, handler: ConnectionHandler) -> None:
        """Register a disconnection handler."""
        self._disconnect_handlers.append(handler)

    async def start(self) -> None:
        """Start the P2P node (server mode)."""
        if self._running:
            return

        self._running = True

        # Start WebSocket server
        self._server = await websockets.serve(
            self._handle_connection,
            self.config.host,
            self.config.port,
            ping_interval=self.config.ping_interval,
            ping_timeout=self.config.ping_timeout
        )

        # Update port if it was 0 (ephemeral)
        if self.config.port == 0 and self._server.sockets:
            # Get port from first socket
            sock = self._server.sockets[0]
            self.config.port = sock.getsockname()[1]

        logger.info(f"P2P node started on {self.config.host}:{self.config.port}")
        logger.info(f"Peer ID: {self.wallet.address_short}")

    async def stop(self) -> None:
        """Stop the P2P node."""
        if not self._running:
            return

        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        # Close all connections
        for ws in list(self._connections.values()):
            await ws.close()
        self._connections.clear()

        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        logger.info("P2P node stopped")

    async def connect_to_peer(self, address: str, port: int) -> Optional[Peer]:
        """
        Connect to a remote peer.
        
        Args:
            address: Peer's host address
            port: Peer's port
            
        Returns:
            Peer object if connected, None otherwise
        """
        endpoint = f"{address}:{port}"
        ws_url = f"ws://{endpoint}"

        try:
            ws = await websockets.connect(
                ws_url,
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout
            )

            # Perform handshake
            peer = await self._perform_handshake(ws, address, port)
            if peer:
                self._connections[peer.id] = ws
                self.peer_manager.add(peer)

                # Start message handler
                task = asyncio.create_task(self._handle_messages(ws, peer))
                self._tasks.append(task)

                # Notify handlers
                for handler in self._connect_handlers:
                    await handler(peer)

                logger.info(f"Connected to peer: {peer}")
                return peer
            else:
                await ws.close()
                return None

        except Exception as e:
            logger.error(f"Failed to connect to {endpoint}: {e}")
            return None

    async def _handle_connection(self, ws: WebSocketServerProtocol) -> None:
        """Handle incoming WebSocket connection."""
        peer = None

        try:
            # Wait for handshake
            peer = await self._receive_handshake(ws)
            if not peer:
                await ws.close()
                return

            self._connections[peer.id] = ws
            self.peer_manager.add(peer)

            # Notify handlers
            for handler in self._connect_handlers:
                await handler(peer)

            logger.info(f"Accepted connection from: {peer}")

            # Handle messages
            await self._handle_messages(ws, peer)

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            if peer:
                await self._handle_disconnect(peer)

    async def _perform_handshake(
        self,
        ws: WebSocketClientProtocol,
        address: str,
        port: int
    ) -> Optional[Peer]:
        """Perform outgoing handshake."""
        # Send our handshake
        handshake = HandshakeMessage(
            version=PROTOCOL_VERSION,
            peer_id=self.peer_id,
            name=self.wallet.name,
            signing_key=self.wallet.signing_keys.public_key,
            encryption_key=self.wallet.encryption_keys.public_key,
            capabilities=DEFAULT_CAPABILITIES
        )

        await ws.send(handshake.to_frame().to_bytes())

        # Receive their handshake
        data = await asyncio.wait_for(ws.recv(), timeout=10.0)
        if isinstance(data, str):
            data = data.encode()

        frame, _ = ProtocolFrame.from_bytes(data)

        if frame.frame_type == FrameType.HANDSHAKE:
            their_handshake = HandshakeMessage.from_frame(frame)

            # Send ack
            ack = HandshakeAck(
                accepted=True,
                peer_id=self.peer_id
            )
            await ws.send(ack.to_frame().to_bytes())

            # Wait for their ack
            data = await asyncio.wait_for(ws.recv(), timeout=10.0)
            if isinstance(data, str):
                data = data.encode()

            frame, _ = ProtocolFrame.from_bytes(data)
            if frame.frame_type == FrameType.HANDSHAKE_ACK:
                their_ack = HandshakeAck.from_frame(frame)
                if their_ack.accepted:
                    return Peer(
                        id=their_handshake.peer_id,
                        address=address,
                        port=port,
                        public_key=their_handshake.signing_key,
                        encryption_key=their_handshake.encryption_key,
                        state=PeerState.AUTHENTICATED,
                        name=their_handshake.name
                    )

        return None

    async def _receive_handshake(
        self,
        ws: WebSocketServerProtocol
    ) -> Optional[Peer]:
        """Receive incoming handshake."""
        try:
            data = await asyncio.wait_for(ws.recv(), timeout=10.0)
            if isinstance(data, str):
                data = data.encode()

            frame, _ = ProtocolFrame.from_bytes(data)

            if frame.frame_type != FrameType.HANDSHAKE:
                return None

            their_handshake = HandshakeMessage.from_frame(frame)

            # Send our handshake
            our_handshake = HandshakeMessage(
                version=PROTOCOL_VERSION,
                peer_id=self.peer_id,
                name=self.wallet.name,
                signing_key=self.wallet.signing_keys.public_key,
                encryption_key=self.wallet.encryption_keys.public_key,
                capabilities=DEFAULT_CAPABILITIES
            )
            await ws.send(our_handshake.to_frame().to_bytes())

            # Send ack
            ack = HandshakeAck(
                accepted=True,
                peer_id=self.peer_id
            )
            await ws.send(ack.to_frame().to_bytes())

            # Wait for their ack
            data = await asyncio.wait_for(ws.recv(), timeout=10.0)
            if isinstance(data, str):
                data = data.encode()

            frame, _ = ProtocolFrame.from_bytes(data)
            if frame.frame_type == FrameType.HANDSHAKE_ACK:
                their_ack = HandshakeAck.from_frame(frame)
                if their_ack.accepted:
                    # Get remote address
                    remote = ws.remote_address
                    address = remote[0] if remote else "unknown"
                    port = remote[1] if remote and len(remote) > 1 else 0

                    return Peer(
                        id=their_handshake.peer_id,
                        address=address,
                        port=port,
                        public_key=their_handshake.signing_key,
                        encryption_key=their_handshake.encryption_key,
                        state=PeerState.AUTHENTICATED,
                        name=their_handshake.name
                    )

            return None

        except asyncio.TimeoutError:
            logger.warning("Handshake timeout")
            return None
        except Exception as e:
            logger.error(f"Handshake error: {e}")
            return None

    async def _handle_messages(
        self,
        ws: WebSocketClientProtocol | WebSocketServerProtocol,
        peer: Peer
    ) -> None:
        """Handle messages from a connected peer."""
        try:
            async for data in ws:
                if isinstance(data, str):
                    data = data.encode()

                try:
                    frame, _ = ProtocolFrame.from_bytes(data)
                    await self._process_frame(frame, peer)
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")

        except websockets.ConnectionClosed:
            pass

    async def _process_frame(self, frame: ProtocolFrame, peer: Peer) -> None:
        """Process a received protocol frame."""
        peer.update_seen()

        if frame.frame_type == FrameType.PING:
            ws = self._connections.get(peer.id)
            if ws:
                await ws.send(ProtocolFrame.pong().to_bytes())

        elif frame.frame_type == FrameType.PONG:
            pass  # Just update last_seen

        elif frame.frame_type == FrameType.DATA:
            # Parse message payload
            try:
                message = MessagePayload.from_bytes(frame.payload)

                # Notify handlers
                for handler in self._message_handlers:
                    await handler(message, peer)

            except Exception as e:
                logger.error(f"Error parsing message: {e}")

        elif frame.frame_type == FrameType.CLOSE:
            ws = self._connections.get(peer.id)
            if ws:
                await ws.close()

    async def _handle_disconnect(self, peer: Peer) -> None:
        """Handle peer disconnection."""
        self._connections.pop(peer.id, None)
        self.peer_manager.update_state(peer.id, PeerState.DISCONNECTED)

        for handler in self._disconnect_handlers:
            await handler(peer)

        logger.info(f"Peer disconnected: {peer}")

    async def send_message(self, message: MessagePayload, recipient_id: str) -> bool:
        """
        Send a message to a specific peer.
        
        Args:
            message: The message to send
            recipient_id: Target peer's ID
            
        Returns:
            True if sent, False otherwise
        """
        ws = self._connections.get(recipient_id)
        if not ws:
            # Try to find peer by address
            peer = self.peer_manager.get(recipient_id)
            if peer:
                ws = self._connections.get(peer.id)

        if ws:
            try:
                frame = ProtocolFrame.data(message.to_bytes())
                await ws.send(frame.to_bytes())
                return True
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

        return False

    async def broadcast(self, message: MessagePayload) -> int:
        """
        Broadcast a message to all connected peers.
        
        Args:
            message: The message to broadcast
            
        Returns:
            Number of peers message was sent to
        """
        frame = ProtocolFrame.data(message.to_bytes())
        frame_bytes = frame.to_bytes()

        sent = 0
        for peer_id, ws in list(self._connections.items()):
            try:
                await ws.send(frame_bytes)
                sent += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to {peer_id}: {e}")

        return sent

    def get_peer(self, peer_id: str) -> Optional[Peer]:
        """Get a peer by ID."""
        return self.peer_manager.get(peer_id)

    def get_peers(self) -> list[Peer]:
        """Get all connected peers."""
        return self.peer_manager.get_connected()

    def get_peer_count(self) -> int:
        """Get number of connected peers."""
        return len(self._connections)
