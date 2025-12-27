"""
Connection pool for WebSocket connection reuse.

This module provides:
- ConnectionPool: Manages connection lifecycle and reuse
- Automatic connection health checks
- Connection limits and cleanup
"""

import asyncio
import logging
import time
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional

try:
    from websockets.asyncio.client import connect
    from websockets.asyncio.client import ClientConnection
    WebSocketClientProtocol = ClientConnection
except ImportError:
    from websockets import connect
    # Fallback/Legacy types
    try:
        from websockets.client import WebSocketClientProtocol
    except ImportError:
        WebSocketClientProtocol = Any

logger = logging.getLogger(__name__)


class PooledConnection(BaseModel):
    """A connection in the pool."""

    peer_id: str
    websocket: Any  # WebSocketClientProtocol (typed as Any to avoid validation/import issues)
    address: str
    port: int
    created_at: float = Field(default_factory=time.time)
    last_used: float = Field(default_factory=time.time)
    use_count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def age(self) -> float:
        """Get connection age in seconds."""
        return time.time() - self.created_at

    @property
    def idle_time(self) -> float:
        """Get idle time in seconds."""
        return time.time() - self.last_used

    def touch(self) -> None:
        """Mark connection as used."""
        self.last_used = time.time()
        self.use_count += 1

    @property
    def is_open(self) -> bool:
        """Check if connection is still open."""
        return self.websocket.open if hasattr(self.websocket, 'open') else True


class ConnectionPool:
    """
    Manages WebSocket connection pooling and reuse.
    
    Features:
    - Connection reuse to reduce handshake overhead
    - Automatic cleanup of stale connections
    - Connection limits per peer
    - Health checking
    """

    DEFAULT_MAX_CONNECTIONS = 50
    DEFAULT_MAX_PER_PEER = 3
    DEFAULT_IDLE_TIMEOUT = 300.0  # 5 minutes
    DEFAULT_MAX_AGE = 3600.0      # 1 hour

    def __init__(
        self,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_per_peer: int = DEFAULT_MAX_PER_PEER,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
        max_age: float = DEFAULT_MAX_AGE
    ) -> None:
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum total connections
            max_per_peer: Maximum connections per peer
            idle_timeout: Close connections idle for this many seconds
            max_age: Close connections older than this many seconds
        """
        self.max_connections = max_connections
        self.max_per_peer = max_per_peer
        self.idle_timeout = idle_timeout
        self.max_age = max_age

        # Connection storage
        self._connections: dict[str, list[PooledConnection]] = {}
        self._lock = asyncio.Lock()

        # Stats
        self._total_connections = 0
        self._total_reuses = 0
        self._total_created = 0

    @property
    def size(self) -> int:
        """Get current pool size."""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        return {
            "current_size": self.size,
            "max_connections": self.max_connections,
            "total_created": self._total_created,
            "total_reuses": self._total_reuses,
            "reuse_ratio": (
                self._total_reuses / self._total_created
                if self._total_created > 0 else 0
            ),
            "peers": len(self._connections)
        }

    async def get_connection(
        self,
        peer_id: str,
        address: str,
        port: int
    ) -> Optional[PooledConnection]:
        """
        Get or create a connection to a peer.
        
        Args:
            peer_id: Peer identifier
            address: Peer address
            port: Peer port
            
        Returns:
            PooledConnection if successful, None otherwise
        """
        async with self._lock:
            # Try to reuse existing connection
            if peer_id in self._connections:
                for conn in self._connections[peer_id]:
                    if conn.is_open and conn.idle_time < self.idle_timeout:
                        conn.touch()
                        self._total_reuses += 1
                        logger.debug(f"Reusing connection to {peer_id[:16]}...")
                        return conn

                # Clean up dead connections
                self._connections[peer_id] = [
                    c for c in self._connections[peer_id]
                    if c.is_open
                ]

            # Check limits
            if self.size >= self.max_connections:
                await self._evict_one()

            peer_conns = self._connections.get(peer_id, [])
            if len(peer_conns) >= self.max_per_peer:
                logger.warning(f"Max connections per peer reached for {peer_id[:16]}...")
                return None

        # Create new connection
        try:
            uri = f"ws://{address}:{port}"
            websocket = await connect(uri)

            conn = PooledConnection(
                peer_id=peer_id,
                websocket=websocket,
                address=address,
                port=port
            )

            async with self._lock:
                if peer_id not in self._connections:
                    self._connections[peer_id] = []
                self._connections[peer_id].append(conn)
                self._total_created += 1

            logger.debug(f"Created new connection to {peer_id[:16]}...")
            return conn

        except Exception as e:
            logger.error(f"Failed to connect to {address}:{port}: {e}")
            return None

    async def release_connection(
        self,
        conn: PooledConnection,
        close: bool = False
    ) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            conn: Connection to release
            close: If True, close instead of returning to pool
        """
        if close or conn.age > self.max_age:
            await self._close_connection(conn)
            return

        conn.touch()

    async def close_peer_connections(self, peer_id: str) -> int:
        """
        Close all connections to a peer.
        
        Returns:
            Number of connections closed
        """
        async with self._lock:
            conns = self._connections.pop(peer_id, [])

        closed = 0
        for conn in conns:
            await self._close_connection(conn)
            closed += 1

        return closed


    async def _close_connection_locked(self, conn: PooledConnection) -> None:
        """Close connection assuming lock is already held."""
        try:
            # Release lock briefly to close socket (IO op)
            # This is tricky with asyncio locks.
            # Better approach: Remove from dict while locked, then close socket outside/after.
            # But here we are deep in logic.
            # Let's just create a task for closing or accept that close() might happen while locked.
            # verify socket.close() is async and non-blocking? older websockets might block?
            # minimal risk if just .close().
            pass
        except Exception:
            pass

        if conn.peer_id in self._connections:
            self._connections[conn.peer_id] = [
                c for c in self._connections[conn.peer_id]
                if c is not conn
            ]

        # We should close the socket. But doing it under lock is generally safe for async close().
        try:
            await conn.websocket.close()
        except Exception:
            pass

    async def _close_connection(self, conn: PooledConnection) -> None:
        """Close a single connection (acquires lock)."""
        async with self._lock:
            await self._close_connection_locked(conn)

    async def _evict_one(self) -> None:
        """Evict the oldest idle connection. Assumes lock is HELD."""
        oldest = None
        oldest_idle = 0.0

        for conns in self._connections.values():
            for conn in conns:
                if conn.idle_time > oldest_idle:
                    oldest_idle = conn.idle_time
                    oldest = conn

        if oldest:
            await self._close_connection_locked(oldest)
            logger.debug(f"Evicted connection to {oldest.peer_id[:16]}...")


    async def cleanup(self) -> int:
        """
        Clean up stale connections.
        
        Returns:
            Number of connections cleaned up
        """
        to_close = []

        async with self._lock:
            for peer_id, conns in self._connections.items():
                for conn in conns:
                    if (not conn.is_open or
                        conn.idle_time > self.idle_timeout or
                        conn.age > self.max_age):
                        to_close.append(conn)

            for conn in to_close:
                await self._close_connection_locked(conn)

        if to_close:
            logger.debug(f"Cleaned up {len(to_close)} stale connections")

        return len(to_close)

    async def close_all(self) -> None:
        """Close all pooled connections."""
        async with self._lock:
            all_conns = [
                conn
                for conns in self._connections.values()
                for conn in conns
            ]
            self._connections.clear()

        for conn in all_conns:
            try:
                await conn.websocket.close()
            except Exception:
                pass

        logger.info(f"Closed {len(all_conns)} pooled connections")

    def __repr__(self) -> str:
        return f"ConnectionPool(size={self.size}, max={self.max_connections})"
