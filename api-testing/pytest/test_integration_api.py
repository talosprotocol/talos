import httpx
import pytest

pytestmark = pytest.mark.integration

# Service URLs
SERVICES = {
    "gateway": "http://127.0.0.1:8000",
    "ai_gateway": "http://127.0.0.1:8001",
    "audit": "http://127.0.0.1:8002",
    "config": "http://127.0.0.1:8003",
    "mcp": "http://127.0.0.1:8082",
    "tga": "http://127.0.0.1:8083",
    "ucp": "http://127.0.0.1:8084",
    "terminal": "http://127.0.0.1:8085",
    "chat": "http://127.0.0.1:8090",
    "aiops": "http://127.0.0.1:8200"
}

@pytest.mark.asyncio
async def test_health_checks():
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Gateway
        resp = await client.get(f"{SERVICES['gateway']}/health")
        assert resp.status_code == 200
        
        # AI Gateway
        resp = await client.get(f"{SERVICES['ai_gateway']}/health/live")
        assert resp.status_code == 200
        
        # Audit
        resp = await client.get(f"{SERVICES['audit']}/health")
        assert resp.status_code == 200
        
        # Config
        resp = await client.get(f"{SERVICES['config']}/api/config/health")
        assert resp.status_code == 200
        
        # MCP
        resp = await client.get(f"{SERVICES['mcp']}/health")
        assert resp.status_code == 200
        
        # TGA
        resp = await client.get(f"{SERVICES['tga']}/health")
        assert resp.status_code == 200
        
        # UCP - check port is open (it's an SSE stream)
        try:
            # Connect but don't read the whole stream
            async with client.stream("GET", f"{SERVICES['ucp']}/sse") as response:
                assert response.status_code == 200
        except Exception as e:
            pytest.fail(f"UCP connection failed: {e}")
        
        # Terminal
        resp = await client.get(f"{SERVICES['terminal']}/health")
        assert resp.status_code == 200
        
        # AI Chat
        resp = await client.get(f"{SERVICES['chat']}/health")
        assert resp.status_code == 200
        
        # AIOps
        resp = await client.get(f"{SERVICES['aiops']}/health")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_audit_api():
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Correct path for audit events
        resp = await client.get(f"{SERVICES['audit']}/api/events?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

@pytest.mark.asyncio
async def test_ai_gateway_version():
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{SERVICES['ai_gateway']}/version")
        assert resp.status_code == 200
        assert "version" in resp.json()

@pytest.mark.asyncio
async def test_mcp_status():
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Correct path for MCP status
        resp = await client.get(f"{SERVICES['mcp']}/api/mcp/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
