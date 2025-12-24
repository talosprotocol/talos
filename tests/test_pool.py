
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from src.network.pool import ConnectionPool, PooledConnection

@pytest.fixture
def mock_ws():
    ws = AsyncMock()
    ws.close = AsyncMock()
    ws.open = True
    return ws

@pytest.fixture
def pool():
    return ConnectionPool(
        max_connections=2,
        max_per_peer=2,
        idle_timeout=0.1,
        max_age=1.0
    )

@pytest.mark.asyncio
async def test_pool_get_connection(pool, mock_ws):
    """Test getting a new connection"""
    with patch("src.network.pool.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_ws
        
        # First connection
        conn1 = await pool.get_connection("peer1", "localhost", 8000)
        assert conn1 is not None
        assert pool.size == 1
        assert pool.stats["total_created"] == 1
        
        # Reuse connection (needs to return it first)
        await pool.release_connection(conn1)
        
        conn2 = await pool.get_connection("peer1", "localhost", 8000)
        assert conn2 == conn1
        assert pool.stats["total_reuses"] == 1
        
@pytest.mark.asyncio
async def test_pool_limits(pool, mock_ws):
    """Test connection limits"""
    with patch("src.network.pool.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_ws
        
        # Fill pool
        c1 = await pool.get_connection("p1", "loc", 1)
        c2 = await pool.get_connection("p2", "loc", 2)
        assert pool.size == 2
        
        # Trigger eviction
        c3 = await pool.get_connection("p3", "loc", 3)
        assert pool.size <= 2  # Should have evicted one
        
@pytest.mark.asyncio
async def test_pool_cleanup(pool):
    """Test cleanup of stale connections"""
    # Create a stale connection manually
    conn = PooledConnection(
        peer_id="p1",
        websocket=AsyncMock(),
        address="loc",
        port=1
    )
    # Make it old
    conn.last_used = time.time() - 1.0
    
    # Access private dict for testing
    pool._connections["p1"] = [conn]
    
    # Cleanup
    cleaned = await pool.cleanup()
    assert cleaned == 1
    assert pool.size == 0

@pytest.mark.asyncio
async def test_pool_close_all(pool, mock_ws):
    """Test closing all connections"""
    with patch("src.network.pool.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_ws
        await pool.get_connection("p1", "loc", 1)
        await pool.close_all()
        assert pool.size == 0
        mock_ws.close.assert_called()

@pytest.mark.asyncio
async def test_pool_connect_failure(pool):
    """Test connection failure"""
    with patch("src.network.pool.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.side_effect = Exception("Connection failed")
        conn = await pool.get_connection("p1", "loc", 1)
        assert conn is None
