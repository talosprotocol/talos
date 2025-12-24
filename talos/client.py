"""
Talos Client - Main entry point for the SDK.

Provides a high-level interface for secure communication.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from .config import TalosConfig
from .identity import Identity
from .exceptions import TalosError, ConnectionError, SessionError

from src.core.blockchain import Blockchain
from src.core.session import SessionManager, PrekeyBundle, Session

logger = logging.getLogger(__name__)


class TalosClient:
    """
    Main Talos SDK client.
    
    Provides a clean interface for:
    - Identity management
    - Secure messaging with forward secrecy
    - Blockchain-backed message logging
    - Peer discovery and connection
    
    Usage:
        # Quick start
        client = TalosClient.create("my-agent")
        await client.start()
        
        # Send encrypted message
        await client.send(peer_id, b"Hello!")
        
        # Receive messages
        client.on_message(lambda msg: print(f"Got: {msg}"))
        
        # Cleanup
        await client.stop()
    """
    
    def __init__(
        self,
        identity: Identity,
        config: Optional[TalosConfig] = None,
    ):
        self.identity = identity
        self.config = config or TalosConfig(name=identity.name)
        
        # Core components
        self._blockchain: Optional[Blockchain] = None
        self._session_manager: Optional[SessionManager] = None
        
        # State
        self._running = False
        self._connected_peers: set[str] = set()
        
        # Callbacks
        self._message_handlers: list[Callable] = []
        self._connection_handlers: list[Callable] = []
    
    @classmethod
    def create(
        cls,
        name: str = "talos-agent",
        config: Optional[TalosConfig] = None,
    ) -> "TalosClient":
        """
        Create a new client with auto-generated or loaded identity.
        
        This is the recommended way to create a client.
        
        Args:
            name: Agent name
            config: Optional configuration
            
        Returns:
            Configured TalosClient
        """
        config = config or TalosConfig(name=name)
        identity = Identity.load_or_create(config.keys_path, name)
        
        return cls(identity, config)
    
    @classmethod
    def from_identity(
        cls,
        identity: Identity,
        config: Optional[TalosConfig] = None,
    ) -> "TalosClient":
        """Create client from existing identity."""
        return cls(identity, config)
    
    async def start(self) -> None:
        """
        Start the client.
        
        Initializes blockchain, session manager, and network connections.
        """
        if self._running:
            return
        
        logger.info(f"Starting TalosClient: {self.identity.name}")
        
        # Initialize blockchain
        self._blockchain = Blockchain(difficulty=self.config.difficulty)
        if self.config.blockchain_path.exists():
            self._blockchain.load(self.config.blockchain_path)
        
        # Initialize session manager
        self._session_manager = SessionManager(
            self.identity.signing_keys,
            self.config.sessions_path,
        )
        if self.config.sessions_path.exists():
            self._session_manager.load()
        
        self._running = True
        logger.info(f"TalosClient started: {self.identity.address_short}")
    
    async def stop(self) -> None:
        """
        Stop the client and save state.
        """
        if not self._running:
            return
        
        logger.info("Stopping TalosClient...")
        
        # Save state
        if self._blockchain:
            self._blockchain.save(self.config.blockchain_path)
        
        if self._session_manager:
            self._session_manager.save()
        
        self._running = False
        logger.info("TalosClient stopped")
    
    @property
    def address(self) -> str:
        """Get this client's public address."""
        return self.identity.address
    
    @property
    def is_running(self) -> bool:
        """Check if client is running."""
        return self._running
    
    def get_prekey_bundle(self) -> dict:
        """
        Get prekey bundle for publishing.
        
        Others need this to establish secure sessions with you.
        """
        bundle = self.identity.get_prekey_bundle()
        return bundle.to_dict()
    
    async def establish_session(
        self,
        peer_id: str,
        peer_bundle_dict: dict,
    ) -> Session:
        """
        Establish a secure session with a peer.
        
        Args:
            peer_id: Peer's public address
            peer_bundle_dict: Peer's prekey bundle (from registry)
            
        Returns:
            Established Session
            
        Raises:
            SessionError: If session establishment fails
        """
        self._ensure_running()
        
        try:
            bundle = PrekeyBundle.from_dict(peer_bundle_dict)
            session = self._session_manager.create_session_as_initiator(peer_id, bundle)
            logger.info(f"Established session with {peer_id[:16]}...")
            return session
        except Exception as e:
            raise SessionError(f"Failed to establish session: {e}", peer_id)
    
    def has_session(self, peer_id: str) -> bool:
        """Check if we have a session with a peer."""
        return self._session_manager and self._session_manager.has_session(peer_id)
    
    async def send(
        self,
        peer_id: str,
        data: bytes,
        message_type: str = "text",
    ) -> str:
        """
        Send an encrypted message to a peer.
        
        Args:
            peer_id: Recipient's address
            data: Message content
            message_type: Type of message
            
        Returns:
            Message ID
            
        Raises:
            SessionError: If no session exists
        """
        self._ensure_running()
        
        session = self._session_manager.get_session(peer_id)
        if session is None:
            raise SessionError(f"No session with peer", peer_id)
        
        # Encrypt with forward secrecy
        encrypted = session.encrypt(data)
        
        # Generate message ID
        import uuid
        message_id = str(uuid.uuid4())
        
        # Create simplified record for blockchain
        record = {
            "id": message_id,
            "type": message_type,
            "sender": self.identity.address,
            "recipient": peer_id,
            "encrypted_size": len(encrypted),
            "timestamp": __import__("time").time(),
        }
        
        # Sign and add to blockchain
        import json
        signature = self.identity.sign(json.dumps(record).encode())
        self._blockchain.add_data({
            "message": record,
            "signature": signature.hex(),
        })
        
        logger.debug(f"Sent message to {peer_id[:16]}...")
        return message_id
    
    async def decrypt(self, peer_id: str, encrypted_data: bytes) -> bytes:
        """
        Decrypt a message from a peer.
        
        Args:
            peer_id: Sender's address
            encrypted_data: Encrypted message bytes
            
        Returns:
            Decrypted plaintext
        """
        self._ensure_running()
        
        session = self._session_manager.get_session(peer_id)
        if session is None:
            raise SessionError(f"No session with peer", peer_id)
        
        return session.decrypt(encrypted_data)
    
    def on_message(self, handler: Callable) -> None:
        """
        Register a message handler.
        
        Handler receives (sender_id, message_bytes, metadata).
        """
        self._message_handlers.append(handler)
    
    def on_connection(self, handler: Callable) -> None:
        """
        Register a connection handler.
        
        Handler receives (peer_id, connected: bool).
        """
        self._connection_handlers.append(handler)
    
    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        stats = {
            "address": self.identity.address_short,
            "running": self._running,
            "connected_peers": len(self._connected_peers),
        }
        
        if self._session_manager:
            stats.update(self._session_manager.get_stats())
        
        if self._blockchain:
            stats["blockchain_height"] = len(self._blockchain.chain)
        
        return stats
    
    def _ensure_running(self) -> None:
        """Ensure client is running."""
        if not self._running:
            raise TalosError("Client not running. Call start() first.")
    
    async def __aenter__(self) -> "TalosClient":
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
    
    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"TalosClient({self.identity.name}, {status})"
