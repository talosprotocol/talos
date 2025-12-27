import asyncio
import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.message import MessageType
from src.core.capability import CapabilityManager, Capability
from src.engine.engine import TransmissionEngine, MCPMessage
from src.mcp_bridge.proxy import MCPClientProxy, MCPServerProxy

@pytest.mark.asyncio
async def test_mcp_workflow():
    # 1. Mock Engine & P2P
    mock_p2p = MagicMock()
    mock_p2p.send_message = AsyncMock(return_value=True)
    # get_peer is synchronous
    mock_p2p.get_peer.return_value = MagicMock(encryption_key=None)
    # on_message is synchronous registration
    mock_p2p.on_message = MagicMock()

    mock_wallet = MagicMock()
    mock_wallet.address = "test_wallet_address"
    mock_wallet.sign.return_value = b"signature"

    engine = TransmissionEngine(mock_wallet, mock_p2p, MagicMock())

    # 2. Setup Client Proxy
    # We want to verified that when ClientProxy reads from "stdin", it calls engine.send_mcp
    client_proxy = MCPClientProxy(engine, "remote_peer_id")

    # Simulating reading from stdin is hard without full integration,
    # so we will test the handle_bmp_message part of ClientProxy (receiving response)

    # 3. Test Client Proxy receiving response
    # It should print to stdout (we'll capture this if we could, but for now we look for no error)
    msg_content = {"result": "success", "id": 1}
    mcp_msg = MCPMessage(
        id="msg1",
        sender="remote_peer_id",
        content=msg_content,
        timestamp=123.0,
        verified=True
    )

    # This just prints to stdout, difficult to assert side effect without capsys,
    # but ensures no exception
    await client_proxy.handle_bmp_message(mcp_msg)

    # 4. Create a CapabilityManager for server proxy
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    capability_manager = CapabilityManager(
        issuer_id="did:talos:server",
        private_key=private_key,
        public_key=public_key,
    )

    # Grant a capability for the test
    capability = capability_manager.grant(
        subject="client_peer_id",
        scope="tool:ping/method:ping",
        expires_in=3600,
    )

    # 5. Test Server Proxy (now requires capability_manager)
    server_proxy = MCPServerProxy(engine, "client_peer_id", "cat", capability_manager)
    await server_proxy.start()

    # 6. Simulate Server Proxy receiving a Request from BMP with capability
    request_content = {
        "method": "ping",
        "id": 1,
        "_talos_capability": capability.to_dict(),  # Include capability in request
    }
    req_msg = MCPMessage(
        id="msg2",
        sender="client_peer_id",
        content=request_content,
        timestamp=123.0,
        verified=True
    )

    # This should write to 'cat' stdin -> 'cat' writes to stdout -> server proxy reads stdout -> engine.send_mcp
    await server_proxy.handle_bmp_message(req_msg)

    # Allow some time for asyncio loops
    await asyncio.sleep(0.5)

    # Verify engine.send_mcp was called with the echoed response
    # 'cat' might output exact input, so we expect {"method": "ping", "id": 1} back
    # But usually server responds. Here we just test the loop.

    assert mock_p2p.send_message.called
    call_args = mock_p2p.send_message.call_args[0]
    sent_msg = call_args[0]

    assert sent_msg.type == MessageType.MCP_RESPONSE
    # We expect the content to be the echoed JSON because we used 'cat'
    # In real life it would be a result
    decoded = json.loads(sent_msg.content.decode())
    # The echoed content includes _talos_capability, so just check id and method
    assert decoded.get("method") == "ping"
    assert decoded.get("id") == 1

    await server_proxy.stop()

