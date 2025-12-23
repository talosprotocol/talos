import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from src.mcp_bridge.proxy import MCPClientProxy, MCPServerProxy
from src.core.message import MessageType
from src.engine.engine import MCPMessage

@pytest.fixture
def mock_p2p():
    mock = MagicMock()
    mock.send_message = AsyncMock()
    mock.get_peer = MagicMock(return_value={"public_key": "abc", "address": "127.0.0.1"})
    return mock

@pytest.fixture
def mock_engine(mock_p2p):
    engine = MagicMock()
    engine.p2p_node = mock_p2p
    engine.wallet.address = "test_addr"
    engine.send_mcp = AsyncMock()
    return engine

@pytest.mark.asyncio
async def test_large_payload_handling(mock_engine):
    """Test handling of large MCP payloads (>100KB)."""
    # Create a huge payload
    large_data = "x" * 150_000
    huge_request = {
        "jsonrpc": "2.0",
        "method": "update_file",
        "params": {"content": large_data},
        "id": 1
    }
    json_lines = json.dumps(huge_request).encode() + b"\n"
    
    proxy = MCPClientProxy(mock_engine, "target_peer_id")
    
    # Mock stdin
    proxy.reader = AsyncMock()
    proxy.reader.readline = AsyncMock(side_effect=[json_lines, asyncio.IncompleteReadError(partial=b"", expected=None)])
    
    # Run loop briefly
    task = asyncio.create_task(proxy.start())
    await asyncio.sleep(0.1)
    proxy.running = False
    await asyncio.gather(task, return_exceptions=True)
    
    # Verify send_mcp was called with the full data
    # (The engine handles chunking internally, so the proxy just passes the blob)
    mock_engine.send_mcp.assert_called()
    call_args = mock_engine.send_mcp.call_args
    assert call_args is not None
    assert len(call_args[0][1]["params"]["content"]) >= 150_000 

@pytest.mark.asyncio
async def test_concurrency_stress(mock_engine):
    """Test rapid-fire requests handling."""
    proxy = MCPClientProxy(mock_engine, "target_peer_id")
    
    # Simulate 50 requests arriving rapidly
    requests = []
    for i in range(50):
        req = json.dumps({"jsonrpc": "2.0", "method": "ping", "id": i}).encode() + b"\n"
        requests.append(req)
    
    # Mock iterator behavior for readuntil
    iter_requests = iter(requests)
    
    async def side_effect(*args):
        try:
            return next(iter_requests)
        except StopIteration:
            raise asyncio.IncompleteReadError(partial=b"", expected=None)
            
    proxy.reader = AsyncMock()
    proxy.reader.readline = AsyncMock(side_effect=side_effect)
    
    task = asyncio.create_task(proxy.start())
    await asyncio.sleep(0.2) # Allow processing
    proxy.running = False
    await asyncio.gather(task, return_exceptions=True)
    
    # Should have sent 50 messages
    assert mock_engine.send_mcp.call_count == 50

@pytest.mark.asyncio
async def test_malformed_json_resilience(mock_engine):
    """Test that proxy survives malformed JSON input."""
    proxy = MCPClientProxy(mock_engine, "target_peer_id")
    
    bad_input = b"{ 'malformed': \n"
    good_input = json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 1}).encode() + b"\n"
    
    proxy.reader = AsyncMock()
    proxy.reader.readline = AsyncMock(side_effect=[bad_input, good_input, asyncio.IncompleteReadError(partial=b"", expected=None)])
    
    task = asyncio.create_task(proxy.start())
    await asyncio.sleep(0.1)
    proxy.running = False
    await asyncio.gather(task, return_exceptions=True)
    
    # Should have sent 1 message (the good one), ignoring the bad one
    assert mock_engine.send_mcp.call_count == 1
