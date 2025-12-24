"""
Client state management for the messaging protocol.

This module provides:
- Client: Main client class managing wallet, connections, and messaging
- Wallet persistence and loading
"""

import asyncio
import json
import logging
from pydantic import BaseModel, ConfigDict
from pathlib import Path
from typing import Optional

import websockets
try:
    from websockets.asyncio.client import ClientConnection
    WebSocketClientProtocol = ClientConnection
except ImportError:
    try:
        from websockets.client import WebSocketClientProtocol
    except ImportError:
        WebSocketClientProtocol = Any

from ..core.crypto import Wallet
from ..core.blockchain import Blockchain
from ..network.p2p import P2PNode, P2PConfig
from ..network.peer import Peer
from ..network.protocol import (
    ProtocolFrame,
    FrameType,
    HandshakeMessage,
    HandshakeAck,
    PROTOCOL_VERSION,
    DEFAULT_CAPABILITIES,
)
from ..engine.engine import TransmissionEngine

logger = logging.getLogger(__name__)


# Default paths
DEFAULT_DATA_DIR = Path.home() / ".talos"
WALLET_FILE = "wallet.json"
BLOCKCHAIN_FILE = "blockchain.json"


class ClientConfig(BaseModel):
    """Client configuration."""
    
    data_dir: Path = DEFAULT_DATA_DIR
    p2p_port: int = 8766
    registry_host: str = "localhost"
    registry_port: int = 8765
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Client:
    """
    Main client for the blockchain messaging protocol.
    
    Manages:
    - Wallet (identity)
    - P2P connections
    - Message transmission
    - Blockchain storage
    """
    
    def __init__(self, config: Optional[ClientConfig] = None) -> None:
        """
        Initialize client.
        
        Args:
            config: Optional client configuration
        """
        self.config = config or ClientConfig()
        
        # Ensure data directory exists
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components (initialized lazily)
        self._wallet: Optional[Wallet] = None
        self._blockchain: Optional[Blockchain] = None
        self._p2p_node: Optional[P2PNode] = None
        self._engine: Optional[TransmissionEngine] = None
        
        # Registry connection
        self._registry_ws: Optional[WebSocketClientProtocol] = None
        self._peers: dict[str, dict] = {}  # peer_id -> peer info
        
        # State
        self._running = False
        self._tasks: list[asyncio.Task] = []
    
    @property
    def wallet(self) -> Optional[Wallet]:
        return self._wallet
    
    @property
    def blockchain(self) -> Optional[Blockchain]:
        return self._blockchain
    
    @property
    def is_initialized(self) -> bool:
        return self._wallet is not None
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def wallet_path(self) -> Path:
        return self.config.data_dir / WALLET_FILE
    
    @property
    def blockchain_path(self) -> Path:
        return self.config.data_dir / BLOCKCHAIN_FILE
    
    def init_wallet(self, name: str) -> Wallet:
        """
        Initialize a new wallet.
        
        Args:
            name: User's display name
            
        Returns:
            The created wallet
        """
        if self.wallet_path.exists():
            raise FileExistsError(f"Wallet already exists at {self.wallet_path}")
        
        self._wallet = Wallet.generate(name)
        self._save_wallet()
        
        logger.info(f"Created wallet for {name}")
        logger.info(f"Address: {self._wallet.address}")
        
        return self._wallet
    
    def load_wallet(self) -> bool:
        """
        Load wallet from disk.
        
        Returns:
            True if wallet was loaded, False if not found
        """
        if not self.wallet_path.exists():
            return False
        
        with open(self.wallet_path, "r") as f:
            data = json.load(f)
        
        self._wallet = Wallet.from_dict(data)
        logger.info(f"Loaded wallet: {self._wallet.name} ({self._wallet.address_short})")
        
        return True
    
    def _save_wallet(self) -> None:
        """Save wallet to disk."""
        if not self._wallet:
            return
        
        with open(self.wallet_path, "w") as f:
            json.dump(self._wallet.to_dict(), f, indent=2)
    
    def load_blockchain(self) -> bool:
        """Load blockchain from disk."""
        if not self.blockchain_path.exists():
            self._blockchain = Blockchain(difficulty=2)
            return False
        
        with open(self.blockchain_path, "r") as f:
            data = json.load(f)
        
        self._blockchain = Blockchain.from_dict(data)
        logger.info(f"Loaded blockchain: {len(self._blockchain)} blocks")
        
        return True
    
    def save_blockchain(self) -> None:
        """Save blockchain to disk."""
        if not self._blockchain:
            return
        
        with open(self.blockchain_path, "w") as f:
            json.dump(self._blockchain.to_dict(), f)
    
    async def register(self) -> bool:
        """
        Register with the registry server.
        
        Returns:
            True if registration successful
        """
        if not self._wallet:
            raise RuntimeError("Wallet not initialized")
        
        registry_url = f"ws://{self.config.registry_host}:{self.config.registry_port}"
        
        try:
            self._registry_ws = await websockets.connect(
                registry_url,
                ping_interval=30,
                ping_timeout=10
            )
            
            # Send handshake
            handshake = HandshakeMessage(
                version=PROTOCOL_VERSION,
                peer_id=self._wallet.address,
                name=self._wallet.name,
                signing_key=self._wallet.signing_keys.public_key,
                encryption_key=self._wallet.encryption_keys.public_key,
                capabilities=DEFAULT_CAPABILITIES
            )
            
            await self._registry_ws.send(handshake.to_frame().to_bytes())
            
            # Receive server handshake
            data = await self._registry_ws.recv()
            if isinstance(data, str):
                data = data.encode()
            
            frame, _ = ProtocolFrame.from_bytes(data)
            if frame.frame_type == FrameType.HANDSHAKE:
                server_hs = HandshakeMessage.from_frame(frame)
                logger.info(f"Connected to registry: {server_hs.name}")
            
            # Receive ack
            data = await self._registry_ws.recv()
            if isinstance(data, str):
                data = data.encode()
            
            frame, _ = ProtocolFrame.from_bytes(data)
            if frame.frame_type == FrameType.HANDSHAKE_ACK:
                ack = HandshakeAck.from_frame(frame)
                if not ack.accepted:
                    logger.error(f"Registration rejected: {ack.reason}")
                    await self._registry_ws.close()
                    return False
            
            # Receive peer list
            data = await self._registry_ws.recv()
            if isinstance(data, str):
                data = data.encode()
            
            frame, _ = ProtocolFrame.from_bytes(data)
            if frame.frame_type == FrameType.DATA:
                peer_data = json.loads(frame.payload.decode())
                if peer_data.get("type") == "peer_list":
                    for peer in peer_data.get("peers", []):
                        self._peers[peer["peer_id"]] = peer
                    logger.info(f"Received {len(self._peers)} peers from registry")
            
            # Update our P2P port
            port_update = json.dumps({
                "type": "update_port",
                "port": self.config.p2p_port
            }).encode()
            await self._registry_ws.send(ProtocolFrame.data(port_update).to_bytes())
            
            logger.info("Registration successful")
            return True
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the client (P2P node and message handling)."""
        if not self._wallet:
            raise RuntimeError("Wallet not initialized")
        
        if self._running:
            return
        
        self._running = True
        
        # Load or create blockchain
        self.load_blockchain()
        
        # Create P2P node
        p2p_config = P2PConfig(
            host="0.0.0.0",
            port=self.config.p2p_port
        )
        self._p2p_node = P2PNode(self._wallet, p2p_config)
        
        # Create transmission engine
        self._engine = TransmissionEngine(
            self._wallet,
            self._p2p_node,
            self._blockchain
        )
        
        # Start P2P node
        await self._p2p_node.start()
        
        logger.info(f"Client started on port {self.config.p2p_port}")
        logger.info(f"Address: {self._wallet.address_short}")
    
    async def stop(self) -> None:
        """Stop the client."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Stop P2P node
        if self._p2p_node:
            await self._p2p_node.stop()
        
        # Close registry connection
        if self._registry_ws:
            await self._registry_ws.close()
        
        # Save blockchain
        self.save_blockchain()
        
        logger.info("Client stopped")
    
    async def connect_to_peer(self, peer_id: str) -> Optional[Peer]:
        """
        Connect to a peer by ID.
        
        Args:
            peer_id: Peer's public key hex
            
        Returns:
            Peer if connected, None otherwise
        """
        if not self._p2p_node:
            raise RuntimeError("Client not started")
        
        # Look up peer info
        peer_info = self._peers.get(peer_id)
        if not peer_info:
            logger.error(f"Unknown peer: {peer_id[:16]}...")
            return None
        
        return await self._p2p_node.connect_to_peer(
            peer_info["address"],
            peer_info["port"]
        )
    
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send a message to a peer.
        
        Args:
            recipient_id: Recipient's public key hex
            message: Message text
            
        Returns:
            True if sent successfully
        """
        if not self._engine:
            raise RuntimeError("Client not started")
        
        # Check if connected, if not try to connect
        peer = self._p2p_node.get_peer(recipient_id)
        if not peer:
            peer = await self.connect_to_peer(recipient_id)
            if not peer:
                return False
        
        return await self._engine.send_text(recipient_id, message)
    
    async def send_file(self, recipient_id: str, file_path: str) -> Optional[str]:
        """
        Send a file to a peer.
        
        Args:
            recipient_id: Recipient's public key hex
            file_path: Path to the file to send
            
        Returns:
            Transfer ID if successful, None on error
        """
        if not self._engine:
            raise RuntimeError("Client not started")
        
        # Check if connected, if not try to connect
        peer = self._p2p_node.get_peer(recipient_id)
        if not peer:
            peer = await self.connect_to_peer(recipient_id)
            if not peer:
                return None
        
        return await self._engine.send_file(recipient_id, file_path)
    
    def on_message(self, callback) -> None:
        """Register a message callback."""
        if self._engine:
            self._engine.on_message(callback)
    
    def on_file(self, callback) -> None:
        """Register a file received callback."""
        if self._engine:
            self._engine.on_file(callback)
    
    def get_peers(self) -> list[dict]:
        """Get list of known peers from registry."""
        return list(self._peers.values())
    
    def get_connected_peers(self) -> list[Peer]:
        """Get list of connected peers."""
        if not self._p2p_node:
            return []
        return self._p2p_node.get_peers()

    async def start_mcp_client_proxy(self, target_peer_id: str):
        """Start MCP client proxy (Agent side)."""
        from ..mcp_bridge.proxy import MCPClientProxy
        if not self._engine:
            raise RuntimeError("Client not started")
            
        # Connect if needed
        peer = self._p2p_node.get_peer(target_peer_id)
        if not peer:
            peer = await self.connect_to_peer(target_peer_id)
            if not peer:
                raise RuntimeError(f"Could not connect to peer {target_peer_id}")
                
        proxy = MCPClientProxy(self._engine, target_peer_id)
        await proxy.start()
        # Keep running - the proxy runs tasks
        return proxy

    async def start_mcp_server_proxy(self, authorized_peer_id: str, command: str):
        """Start MCP server proxy (Tool side)."""
        from ..mcp_bridge.proxy import MCPServerProxy
        if not self._engine:
            raise RuntimeError("Client not started")
            
        # Connect if needed (though usually server listens)
        # But we need to know the peer exists/is valid? 
        # Actually strictly we just need to accept messages from them.
        # But proactive connection helps.
        
        proxy = MCPServerProxy(self._engine, authorized_peer_id, command)
        await proxy.start()
        return proxy

