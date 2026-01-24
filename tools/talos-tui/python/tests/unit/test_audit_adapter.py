import pytest
from unittest.mock import AsyncMock
from aiohttp import ClientSession, ClientResponse
from talos_tui.adapters.audit_http import HttpAuditAdapter
from talos_tui.ports.errors import TuiError

@pytest.mark.asyncio
async def test_audit_list_events_success():
    mock_resp = AsyncMock(spec=ClientResponse)
    mock_resp.status = 200
    mock_resp.content_length = 1000
    mock_resp.json.return_value = {
        "items": [
            {
                "id": "evt_1",
                "ts": "2023-01-01T00:00:00Z",
                "event_type": "login",
                "payload": {"user": "alice"}
            }
        ],
        "next_cursor": "cur_123",
        "has_more": True
    }
    
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    
    adapter = HttpAuditAdapter("http://test", mock_session)
    page = await adapter.list_events(limit=10, before=None)
    
    assert len(page.items) == 1
    assert page.items[0].id == "evt_1"
    assert page.next_cursor == "cur_123"
    assert page.has_more is True

@pytest.mark.asyncio
async def test_audit_redaction_applied():
    """Verify secrets are redacted before domain model creation."""
    mock_resp = AsyncMock(spec=ClientResponse)
    mock_resp.status = 200
    mock_resp.content_length = 1000
    mock_resp.json.return_value = {
        "items": [
            {
                "id": "evt_2",
                "ts": "2023-01-01T00:00:00Z",
                "event_type": "secret_op",
                "payload": {"token": "sensitive_value"} # Should be redacted
            }
        ]
    }
    
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.return_value.__aenter__.return_value = mock_resp
    
    adapter = HttpAuditAdapter("http://test", mock_session)
    page = await adapter.list_events(limit=10, before=None)
    
    assert page.items[0].payload["token"] == "***REDACTED***"
