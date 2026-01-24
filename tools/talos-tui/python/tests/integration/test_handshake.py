import pytest
from unittest.mock import AsyncMock, MagicMock
from talos_tui.app import TalosTuiApp
from talos_tui.domain.models import VersionInfo

@pytest.mark.asyncio
async def test_handshake_success():
    # Mock Adapters
    app = TalosTuiApp()
    app.gateway = AsyncMock()
    app.audit = AsyncMock()
    
    app.gateway.get_version.return_value = VersionInfo(
        service_version="1.0.0", git_sha="abc", contracts_version="1.0.0", api_version="v1"
    )
    app.audit.get_version.return_value = VersionInfo(
        service_version="1.0.0", git_sha="abc", contracts_version="1.0.0", api_version="v1"
    )
    
    # Run logic directly (bypassing full UI loop for unit test speed)
    await app.perform_handshake()
    
    # Verify strict check passed (no exception would be raised, and success logic hit)
    # In a real Textual harness we'd check `app.screen`
    assert app.sub_title == "GW: 1.0.0 | Audit: 1.0.0"

@pytest.mark.asyncio
async def test_handshake_incompatible():
    app = TalosTuiApp()
    app.gateway = AsyncMock()
    app.audit = AsyncMock()
    
    # Major version mismatch
    app.gateway.get_version.return_value = VersionInfo(
        service_version="1.0.0", git_sha="abc", contracts_version="2.0.0", api_version="v1"
    )
    app.audit.get_version.return_value = VersionInfo(
        service_version="1.0.0", git_sha="abc", contracts_version="2.0.0", api_version="v1"
    )
    
    # We expect the error screen logic to be triggered
    # Mock push_screen to capture the error
    app.push_screen = MagicMock()
    
    await app.perform_handshake()
    
    # Assert ErrorScreen was pushed
    app.push_screen.assert_called()
    call_args = app.push_screen.call_args[0][0]
    assert "INCOMPATIBLE CONTRACTS" in call_args.message
