#!/usr/bin/env python3
"""
Talos Protocol Demo - Capability Authorization System.

This demo showcases:
1. Cryptographic identity creation
2. Capability token issuance
3. Session-cached authorization (<1ms)
4. Audit plane integration
5. Rate limiting
"""

import secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.capability import CapabilityManager
from src.core.audit_plane import AuditAggregator
from src.core.rate_limiter import SessionRateLimiter, RateLimitConfig


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    print_section("TALOS PROTOCOL DEMO - Phase 1-3 Features")
    
    # ========================================
    # 1. IDENTITY SETUP
    # ========================================
    print_section("1. Cryptographic Identity")
    
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    manager = CapabilityManager(
        issuer_id="did:talos:issuer",
        private_key=private_key,
        public_key=public_key,
    )
    
    print("✓ Created CapabilityManager")
    print("  Issuer: did:talos:issuer")
    print("  Key type: Ed25519")
    
    # ========================================
    # 2. CAPABILITY ISSUANCE
    # ========================================
    print_section("2. Capability Token Issuance")
    
    cap = manager.grant(
        subject="did:talos:agent",
        scope="tool:filesystem/method:read",
        constraints={"paths": ["/data/*"]},
        expires_in=3600,
        delegatable=True,
    )
    
    print(f"✓ Granted capability: {cap.id}")
    print(f"  Subject: {cap.subject}")
    print(f"  Scope: {cap.scope}")
    print(f"  Delegatable: {cap.delegatable}")
    print(f"  Expires: {cap.expires_at}")
    
    # ========================================
    # 3. AUTHORIZATION - FULL PATH
    # ========================================
    print_section("3. Full Authorization")
    
    result = manager.authorize(
        capability=cap,
        tool="filesystem",
        method="read",
    )
    
    print(f"✓ Authorization result: {'ALLOWED' if result.allowed else 'DENIED'}")
    print(f"  Capability ID: {result.capability_id}")
    
    # ========================================
    # 4. SESSION-CACHED AUTHORIZATION
    # ========================================
    print_section("4. Session-Cached Authorization (<1ms)")
    
    session_id = secrets.token_bytes(16)
    manager.cache_session(session_id, cap)
    
    print(f"✓ Cached session: {session_id.hex()[:16]}...")
    
    # Run 100 authorizations
    latencies = []
    for _ in range(100):
        fast_result = manager.authorize_fast(session_id, "filesystem", "read")
        latencies.append(fast_result.latency_us)
    
    avg_latency = sum(latencies) / len(latencies)
    p99_latency = sorted(latencies)[99]
    
    print("\n  Authorize Fast (100 calls):")
    print(f"  ├─ Average: {avg_latency:.1f}μs")
    print(f"  ├─ p99: {p99_latency}μs")
    print(f"  └─ Status: {'✓ PASS' if p99_latency < 1000 else '✗ FAIL'} (<1ms target)")
    
    # ========================================
    # 5. AUDIT PLANE
    # ========================================
    print_section("5. Audit Plane Integration")
    
    agg = AuditAggregator()
    
    # Record some events
    agg.record_authorization("did:talos:agent", "filesystem", "read", cap.id, True, latency_us=5)
    agg.record_authorization("did:talos:agent", "filesystem", "write", None, False, "SCOPE_MISMATCH")
    agg.record_revocation("did:talos:issuer", cap.id, "demo complete")
    
    stats = agg.get_stats()
    
    print("✓ Audit events recorded:")
    print(f"  ├─ Total: {stats['total_events']}")
    print(f"  ├─ Denials: {stats['denial_count']}")
    print(f"  └─ Approval rate: {stats['approval_rate']:.0%}")
    
    # Export sample
    print("\n  CSV Export (header + 3 rows):")
    csv = agg.export_csv()
    for line in csv.split("\n")[:4]:
        print(f"  │ {line[:70]}...")
    
    # ========================================
    # 6. RATE LIMITING
    # ========================================
    print_section("6. Rate Limiting")
    
    limiter = SessionRateLimiter(RateLimitConfig(burst_size=5, requests_per_second=10))
    
    test_session = secrets.token_bytes(16)
    allowed_count = 0
    blocked_count = 0
    
    for _ in range(10):
        if limiter.allow(test_session):
            allowed_count += 1
        else:
            blocked_count += 1
    
    print("✓ Rate limiter test (burst=5, 10 calls):")
    print(f"  ├─ Allowed: {allowed_count}")
    print(f"  └─ Blocked: {blocked_count}")
    
    # ========================================
    # SUMMARY
    # ========================================
    print_section("DEMO COMPLETE")
    print("Features demonstrated:")
    print("  ✓ Ed25519 identity and signatures")
    print("  ✓ Capability tokens with scope and constraints")
    print("  ✓ Full authorization path")
    print("  ✓ Session-cached authorization (<1ms)")
    print("  ✓ Audit plane with export")
    print("  ✓ Per-session rate limiting")
    print()
    print("Run 'pytest tests/' to see all 551 tests pass.")
    print()


if __name__ == "__main__":
    main()
