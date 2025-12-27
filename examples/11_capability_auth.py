#!/usr/bin/env python3
"""
Example 11: Capability Authorization

This example demonstrates the Phase 1 capability-based authorization system:
- Creating a CapabilityManager with Ed25519 keys
- Granting capabilities with scope and constraints
- Session-cached authorization (<1ms)
- Delegation with depth limits
"""

import secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.capability import (
    CapabilityManager,
    MAX_DELEGATION_DEPTH,
)


def main():
    print("=" * 50)
    print("Example 11: Capability Authorization")
    print("=" * 50)
    
    # Create issuer identity
    print("\n[1] Creating CapabilityManager...")
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    manager = CapabilityManager(
        issuer_id="did:talos:issuer",
        private_key=private_key,
        public_key=public_key,
    )
    print("  Issuer: did:talos:issuer")
    print("  Key type: Ed25519")
    
    # Grant a capability
    print("\n[2] Granting Capability...")
    cap = manager.grant(
        subject="did:talos:agent",
        scope="tool:filesystem/method:read",
        constraints={"paths": ["/data/*"]},
        expires_in=3600,
        delegatable=True,
    )
    print(f"  ID: {cap.id}")
    print(f"  Scope: {cap.scope}")
    print(f"  Delegatable: {cap.delegatable}")
    
    # Authorize a request
    print("\n[3] Authorizing Request...")
    result = manager.authorize(cap, "filesystem", "read")
    print(f"  Allowed: {result.allowed}")
    print(f"  Capability ID: {result.capability_id}")
    
    # Session-cached authorization
    print("\n[4] Session-Cached Authorization...")
    session_id = secrets.token_bytes(16)
    manager.cache_session(session_id, cap)
    
    # Run 100 authorizations
    latencies = []
    for _ in range(100):
        fast_result = manager.authorize_fast(session_id, "filesystem", "read")
        latencies.append(fast_result.latency_us)
    
    avg = sum(latencies) / len(latencies)
    p99 = sorted(latencies)[99]
    print(f"  100 calls: avg={avg:.1f}μs, p99={p99}μs")
    
    # Delegation
    print("\n[5] Delegation...")
    delegated = manager.delegate(
        parent_capability=cap,
        new_subject="did:talos:subagent",
        narrowed_scope="tool:filesystem/method:read",
    )
    print(f"  Delegated ID: {delegated.id}")
    print(f"  To: {delegated.subject}")
    print(f"  Chain depth: {len(delegated.delegation_chain)}")
    
    # Show depth limit
    print("\n[6] Delegation Depth Limit...")
    print(f"  MAX_DELEGATION_DEPTH = {MAX_DELEGATION_DEPTH}")
    
    print("\n" + "=" * 50)
    print("Example 11 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
