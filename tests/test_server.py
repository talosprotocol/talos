
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from src.server.server import TalosServer, main

@pytest.fixture
def mock_registry_server():
    with patch("src.server.server.RegistryServer") as MockRS:
        instance = MockRS.return_value
        instance.start = AsyncMock()
        instance.stop = AsyncMock()
        yield instance

@pytest.mark.asyncio
async def test_server_start_stop(mock_registry_server):
    """Test TalosServer start and stop"""
    server = TalosServer(host="1.2.3.4", port=9999, name="TestServer")
    
    assert server.host == "1.2.3.4"
    assert server.port == 9999
    assert server.name == "TestServer"
    assert not server._running
    
    # Start
    await server.start()
    assert server._running
    mock_registry_server.start.assert_called_once()
    
    # Start again (idempotent)
    await server.start()
    assert mock_registry_server.start.call_count == 1
    
    # Stop
    await server.stop()
    assert not server._running
    mock_registry_server.stop.assert_called_once()
    
    # Stop again (idempotent)
    await server.stop()
    assert mock_registry_server.stop.call_count == 1

def test_server_main_cli():
    """Test CLI entry point logic"""
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        with patch("src.server.server.TalosServer") as MockServer:
             with patch("asyncio.run") as mock_run:
                # Use a simple object or Namespace to avoid MagicMock name collision
                from argparse import Namespace
                mock_args.return_value = Namespace(
                    host="localhost",
                    port=1234,
                    name="CLI",
                    debug=True
                )
                
                main()
                
                MockServer.assert_called_with(
                    host="localhost",
                    port=1234,
                    name="CLI"
                )
                mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_server_run_forever(mock_registry_server):
    """Test run_forever handling signals"""
    server = TalosServer()
    
    # Mock loop and signal handlers
    loop = MagicMock()
    # Mock add_signal_handler to actually trigger the callback immediately for the test
    # (In real life this waits for a signal, but for test we want to verify logic)
    # We can't easily mock the loop inside run_forever without refactoring, 
    # but we can rely on asyncio.Event waiting.
    
    # We'll patch asyncio.get_running_loop
    with patch("asyncio.get_running_loop", return_value=loop):
        # We start a task that waits for the server to be running, then stops it
        task = asyncio.create_task(server.run_forever())
        
        # Give it a moment to start
        await asyncio.sleep(0.01)
        assert server._running
        
        # Manually verify loop.add_signal_handler was called
        handler = loop.add_signal_handler.call_args[0][1]
        
        # Trigger the handler (simulating SIGINT)
        handler()
        
        # Wait for task to finish
        await task
        assert not server._running

