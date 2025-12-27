#!/usr/bin/env python3
"""
Example 14: Gateway

This example demonstrates the Phase 3 gateway for multi-tenant authorization:
- Registering tenants with separate capability managers
- Per-tenant rate limiting
- Tool allowlists
- Health monitoring
"""

import secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.gateway import (
    Gateway,
    GatewayRequest,
    TenantConfig,
)
from src.core.capability import CapabilityManager
from src.core.rate_limiter import RateLimitConfig


def create_manager(issuer_id: str) -> CapabilityManager:
    """Create a capability manager for a tenant."""
    private_key = Ed25519PrivateKey.generate()
    return CapabilityManager(issuer_id, private_key, private_key.public_key())


def main():
    print("=" * 50)
    print("Example 14: Gateway")
    print("=" * 50)
    
    # Create gateway
    print("\n[1] Creating Gateway...")
    gateway = Gateway()
    print(f"  Status: {gateway.status.value}")
    
    # Register tenants
    print("\n[2] Registering Tenants...")
    
    tenant1_mgr = create_manager("did:talos:tenant1")
    gateway.register_tenant(TenantConfig(
        tenant_id="tenant1",
        capability_manager=tenant1_mgr,
        rate_limit_config=RateLimitConfig(burst_size=10, requests_per_second=5),
        allowed_tools=["filesystem", "database"],
    ))
    print("  ✓ tenant1: filesystem, database tools")
    
    tenant2_mgr = create_manager("did:talos:tenant2")
    gateway.register_tenant(TenantConfig(
        tenant_id="tenant2",
        capability_manager=tenant2_mgr,
        allowed_tools=["api"],
    ))
    print("  ✓ tenant2: api tool only")
    
    # Start gateway
    print("\n[3] Starting Gateway...")
    gateway.start()
    print(f"  Status: {gateway.status.value}")
    
    # Create sessions with capabilities
    print("\n[4] Setting Up Sessions...")
    
    cap1 = tenant1_mgr.grant("did:talos:agent1", "tool:filesystem/method:read", expires_in=3600)
    session1 = secrets.token_bytes(16)
    tenant1_mgr.cache_session(session1, cap1)
    print(f"  Tenant1 session: {session1.hex()[:8]}...")
    
    # Authorize through gateway
    print("\n[5] Authorization - Success...")
    response = gateway.authorize(GatewayRequest(
        request_id="req1",
        tenant_id="tenant1",
        session_id=session1,
        tool="filesystem",
        method="read",
    ))
    print(f"  Allowed: {response.allowed}")
    print(f"  Latency: {response.latency_us}μs")
    
    # Tool not in allowlist
    print("\n[6] Authorization - Tool Blocked...")
    response = gateway.authorize(GatewayRequest(
        request_id="req2",
        tenant_id="tenant1",
        session_id=session1,
        tool="admin",  # Not in allowlist
        method="delete",
    ))
    print(f"  Allowed: {response.allowed}")
    print(f"  Error: {response.error}")
    
    # Unknown tenant
    print("\n[7] Authorization - Unknown Tenant...")
    response = gateway.authorize(GatewayRequest(
        request_id="req3",
        tenant_id="unknown",
        session_id=secrets.token_bytes(16),
        tool="test",
        method="ping",
    ))
    print(f"  Allowed: {response.allowed}")
    print(f"  Error: {response.error}")
    
    # Health check
    print("\n[8] Health Check...")
    health = gateway.get_health()
    print(f"  Status: {health['status']}")
    print(f"  Tenants: {health['tenants']}")
    print(f"  Requests: {health['requests_processed']}")
    
    # Tenant stats
    print("\n[9] Tenant Stats...")
    stats = gateway.get_tenant_stats("tenant1")
    print(f"  Tenant: {stats['tenant_id']}")
    print(f"  Tools: {stats['allowed_tools']}")
    
    print("\n" + "=" * 50)
    print("Example 14 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
