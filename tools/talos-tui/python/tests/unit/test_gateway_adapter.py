import pytest
from unittest.mock import AsyncMock, MagicMock
from aiohttp import ClientSession, ClientResponse
from talos_tui.adapters.gateway_http import HttpGatewayAdapter
from talos_tui.ports.errors import TuiError

@pytest.mark.asyncio
async def test_gateway_get_version_success():
    mock_resp = AsyncMock(spec=ClientResponse)
    mock_resp.status = 200
    mock_resp.content_length = 500
    mock_resp.json.return_value = {
        "service_version": "1.0.0",
        "git_sha": "abc",
        "contracts_version": "1.0.0",
        "api_version": "v1"
    }
    
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    
    adapter = HttpGatewayAdapter("http://test", mock_session)
    version = await adapter.get_version()
    
    assert version.service_version == "1.0.0"
    assert version.contracts_version == "1.0.0"

@pytest.mark.asyncio
async def test_gateway_payload_too_large():
    mock_resp = AsyncMock(spec=ClientResponse)
    mock_resp.status = 200
    mock_resp.content_length = 2_000_000 # > 1MB limit
    
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    
    adapter = HttpGatewayAdapter("http://test", mock_session)
    
    with pytest.raises(TuiError) as exc:
        await adapter.get_version()
    
    assert exc.value.kind == "PAYLOAD_TOO_LARGE"

@pytest.mark.asyncio
async def test_gateway_bad_status():
    mock_resp = AsyncMock(spec=ClientResponse)
    mock_resp.status = 500
    
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    
    adapter = HttpGatewayAdapter("http://test", mock_session)
    
    with pytest.raises(TuiError) as exc:
        await adapter.get_health()
        
    assert exc.value.kind == "BAD_RESPONSE"
    assert exc.value.retryable is True
