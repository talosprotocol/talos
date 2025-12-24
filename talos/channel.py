"""
Secure Channel - Async context manager for peer communication.

Provides a clean interface for bidirectional encrypted communication.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Optional

from .client import TalosClient
from .exceptions import ConnectionError, SessionError, TimeoutError

logger = logging.getLogger(__name__)


class SecureChannel:
    """
    Async context manager for secure peer communication.
    
    Establishes a Double Ratchet session and provides send/receive methods.
    
    Usage:
        async with SecureChannel(client, peer_id, peer_bundle) as channel:
            await channel.send(b"Hello!")
            response = await channel.receive(timeout=5.0)
            print(f"Got: {response}")
    
    Or for continuous receiving:
        async with SecureChannel(client, peer_id) as channel:
            async for message in channel:
                print(f"Got: {message}")
    """
    
    def __init__(
        self,
        client: TalosClient,
        peer_id: str,
        peer_bundle: Optional[dict] = None,
    ):
        """
        Create a secure channel.
        
        Args:
            client: TalosClient instance
            peer_id: Peer's public address
            peer_bundle: Peer's prekey bundle (required for new sessions)
        """
        self.client = client
        self.peer_id = peer_id
        self.peer_bundle = peer_bundle
        
        self._session = None
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
    
    async def __aenter__(self) -> "SecureChannel":
        """Establish the secure channel."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the channel."""
        await self.close()
    
    async def connect(self) -> None:
        """
        Establish connection and session with peer.
        """
        if not self.client.is_running:
            raise ConnectionError("Client not running", self.peer_id)
        
        # Check for existing session
        if self.client.has_session(self.peer_id):
            logger.debug(f"Using existing session with {self.peer_id[:16]}...")
            return
        
        # Need bundle for new session
        if self.peer_bundle is None:
            raise SessionError(
                "No existing session and no prekey bundle provided",
                self.peer_id,
            )
        
        # Establish new session
        self._session = await self.client.establish_session(
            self.peer_id,
            self.peer_bundle,
        )
        
        logger.info(f"Secure channel established with {self.peer_id[:16]}...")
    
    async def close(self) -> None:
        """Close the channel."""
        self._closed = True
        logger.debug(f"Closed channel with {self.peer_id[:16]}...")
    
    @property
    def is_open(self) -> bool:
        """Check if channel is open."""
        return not self._closed and self.client.has_session(self.peer_id)
    
    async def send(self, data: bytes) -> str:
        """
        Send encrypted data to peer.
        
        Args:
            data: Plaintext bytes to send
            
        Returns:
            Message ID
        """
        if self._closed:
            raise ConnectionError("Channel is closed", self.peer_id)
        
        return await self.client.send(self.peer_id, data)
    
    async def send_text(self, text: str) -> str:
        """
        Send text message to peer.
        
        Args:
            text: Text string to send
            
        Returns:
            Message ID
        """
        return await self.send(text.encode("utf-8"))
    
    async def send_json(self, data: Any) -> str:
        """
        Send JSON data to peer.
        
        Args:
            data: JSON-serializable data
            
        Returns:
            Message ID
        """
        import json
        return await self.send(json.dumps(data).encode("utf-8"))
    
    async def receive(self, timeout: Optional[float] = None) -> bytes:
        """
        Receive next message from peer.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Decrypted message bytes
            
        Raises:
            TimeoutError: If timeout expires
        """
        try:
            if timeout:
                return await asyncio.wait_for(
                    self._receive_queue.get(),
                    timeout=timeout,
                )
            else:
                return await self._receive_queue.get()
        except asyncio.TimeoutError:
            raise TimeoutError("Receive timed out", timeout)
    
    async def receive_text(self, timeout: Optional[float] = None) -> str:
        """Receive and decode as text."""
        data = await self.receive(timeout)
        return data.decode("utf-8")
    
    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        """Receive and parse as JSON."""
        import json
        data = await self.receive(timeout)
        return json.loads(data.decode("utf-8"))
    
    def _enqueue_message(self, data: bytes) -> None:
        """Internal: Add received message to queue."""
        if not self._closed:
            self._receive_queue.put_nowait(data)
    
    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Async iterator for receiving messages."""
        while not self._closed:
            try:
                message = await self._receive_queue.get()
                yield message
            except asyncio.CancelledError:
                break
    
    def __repr__(self) -> str:
        status = "open" if self.is_open else "closed"
        return f"SecureChannel({self.peer_id[:16]}..., {status})"


class ChannelPool:
    """
    Manages multiple secure channels.
    
    Useful for agents communicating with many peers.
    """
    
    def __init__(self, client: TalosClient):
        self.client = client
        self._channels: dict[str, SecureChannel] = {}
    
    async def get_or_create(
        self,
        peer_id: str,
        peer_bundle: Optional[dict] = None,
    ) -> SecureChannel:
        """Get existing channel or create new one."""
        if peer_id in self._channels and self._channels[peer_id].is_open:
            return self._channels[peer_id]
        
        channel = SecureChannel(self.client, peer_id, peer_bundle)
        await channel.connect()
        self._channels[peer_id] = channel
        return channel
    
    async def close_all(self) -> None:
        """Close all channels."""
        for channel in self._channels.values():
            await channel.close()
        self._channels.clear()
    
    def __len__(self) -> int:
        return len(self._channels)
