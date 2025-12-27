"""
Tests for Gateway (Phase 3).
"""

import secrets
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.gateway import (
    Gateway,
    GatewayStatus,
    GatewayRequest,
    TenantConfig,
)
from src.core.capability import CapabilityManager
from src.core.rate_limiter import RateLimitConfig


@pytest.fixture
def manager():
    """Create test capability manager."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return CapabilityManager("did:talos:issuer", private_key, public_key)


@pytest.fixture
def gateway():
    """Create test gateway."""
    return Gateway()


class TestGatewayBasics:
    """Basic gateway functionality tests."""

    def test_start_stop(self, gateway):
        """Test gateway lifecycle."""
        assert gateway.status == GatewayStatus.STOPPED
        
        gateway.start()
        assert gateway.status == GatewayStatus.RUNNING
        
        gateway.stop()
        assert gateway.status == GatewayStatus.STOPPED

    def test_register_tenant(self, gateway, manager):
        """Test tenant registration."""
        config = TenantConfig(
            tenant_id="tenant1",
            capability_manager=manager,
        )
        
        gateway.register_tenant(config)
        
        assert gateway.tenant_count == 1

    def test_duplicate_tenant_rejected(self, gateway, manager):
        """Test that duplicate tenant registration fails."""
        config = TenantConfig(tenant_id="tenant1", capability_manager=manager)
        
        gateway.register_tenant(config)
        
        with pytest.raises(ValueError, match="already registered"):
            gateway.register_tenant(config)

    def test_unregister_tenant(self, gateway, manager):
        """Test tenant unregistration."""
        config = TenantConfig(tenant_id="tenant1", capability_manager=manager)
        gateway.register_tenant(config)
        
        result = gateway.unregister_tenant("tenant1")
        
        assert result is True
        assert gateway.tenant_count == 0

    def test_unregister_nonexistent_tenant(self, gateway):
        """Test unregistering unknown tenant."""
        assert gateway.unregister_tenant("nonexistent") is False


class TestGatewayAuthorization:
    """Authorization flow tests."""

    def test_authorize_requires_running(self, gateway, manager):
        """Test that authorization requires running gateway."""
        config = TenantConfig(tenant_id="tenant1", capability_manager=manager)
        gateway.register_tenant(config)
        
        request = GatewayRequest(
            request_id="req1",
            tenant_id="tenant1",
            session_id=secrets.token_bytes(16),
            tool="test",
            method="ping",
        )
        
        response = gateway.authorize(request)
        
        assert response.allowed is False
        assert "not running" in response.error

    def test_authorize_unknown_tenant(self, gateway):
        """Test authorization for unknown tenant."""
        gateway.start()
        
        request = GatewayRequest(
            request_id="req1",
            tenant_id="unknown",
            session_id=secrets.token_bytes(16),
            tool="test",
            method="ping",
        )
        
        response = gateway.authorize(request)
        
        assert response.allowed is False
        assert "Unknown tenant" in response.error

    def test_authorize_with_cached_session(self, gateway, manager):
        """Test authorization with session cache."""
        # Setup
        cap = manager.grant("did:talos:agent", "tool:test/method:ping", expires_in=3600)
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)
        
        config = TenantConfig(tenant_id="tenant1", capability_manager=manager)
        gateway.register_tenant(config)
        gateway.start()
        
        # Request
        request = GatewayRequest(
            request_id="req1",
            tenant_id="tenant1",
            session_id=session_id,
            tool="test",
            method="ping",
        )
        
        response = gateway.authorize(request)
        
        assert response.allowed is True
        assert response.latency_us >= 0

    def test_rate_limit_enforcement(self, gateway, manager):
        """Test rate limiting through gateway."""
        config = TenantConfig(
            tenant_id="tenant1",
            capability_manager=manager,
            rate_limit_config=RateLimitConfig(burst_size=2, requests_per_second=1),
        )
        gateway.register_tenant(config)
        gateway.start()
        
        session_id = secrets.token_bytes(16)
        
        # First two should pass (burst)
        for i in range(2):
            response = gateway.authorize(GatewayRequest(
                request_id=f"req{i}",
                tenant_id="tenant1",
                session_id=session_id,
                tool="test",
                method="ping",
            ))
            # May fail on auth but not rate limit
        
        # Third should be rate limited
        response = gateway.authorize(GatewayRequest(
            request_id="req3",
            tenant_id="tenant1",
            session_id=session_id,
            tool="test",
            method="ping",
        ))
        
        assert response.allowed is False
        assert "Rate limit" in response.error

    def test_tool_allowlist(self, gateway, manager):
        """Test tool allowlist enforcement."""
        config = TenantConfig(
            tenant_id="tenant1",
            capability_manager=manager,
            allowed_tools=["filesystem", "database"],
        )
        gateway.register_tenant(config)
        gateway.start()
        
        # Allowed tool
        response = gateway.authorize(GatewayRequest(
            request_id="req1",
            tenant_id="tenant1",
            session_id=secrets.token_bytes(16),
            tool="filesystem",
            method="read",
        ))
        # May fail on auth, but not tool check
        
        # Disallowed tool
        response = gateway.authorize(GatewayRequest(
            request_id="req2",
            tenant_id="tenant1",
            session_id=secrets.token_bytes(16),
            tool="admin",
            method="delete",
        ))
        
        assert response.allowed is False
        assert "not allowed" in response.error


class TestGatewayHealth:
    """Health and stats tests."""

    def test_health_endpoint(self, gateway, manager):
        """Test health status."""
        config = TenantConfig(tenant_id="tenant1", capability_manager=manager)
        gateway.register_tenant(config)
        gateway.start()
        
        health = gateway.get_health()
        
        assert health["status"] == "RUNNING"
        assert health["tenants"] == 1
        assert health["requests_processed"] == 0
        assert health["started_at"] is not None

    def test_tenant_stats(self, gateway, manager):
        """Test tenant statistics."""
        config = TenantConfig(
            tenant_id="tenant1",
            capability_manager=manager,
            allowed_tools=["tool1", "tool2"],
            max_concurrent_sessions=500,
        )
        gateway.register_tenant(config)
        
        stats = gateway.get_tenant_stats("tenant1")
        
        assert stats["tenant_id"] == "tenant1"
        assert stats["allowed_tools"] == ["tool1", "tool2"]
        assert stats["max_concurrent_sessions"] == 500

    def test_tenant_stats_unknown(self, gateway):
        """Test stats for unknown tenant."""
        assert gateway.get_tenant_stats("unknown") is None
