#!/usr/bin/env python3
"""
Example 3: Access Control Lists (ACL)

This example demonstrates:
- Creating ACL manager
- Adding peer permissions
- Checking tool access
- Rate limiting
- Audit logging

Copy-paste ready!
"""

from src.mcp_bridge.acl import (
    ACLManager,
    PeerPermissions,
    Permission,
    RateLimit,
)


def main():
    print("=" * 50)
    print("Example 3: Access Control Lists (ACL)")
    print("=" * 50)
    
    # ========================================
    # 1. Create ACL Manager
    # ========================================
    print("\n[1] Creating ACL Manager...")
    
    acl = ACLManager(default_allow=False)  # Deny by default
    print("  Default: deny")
    
    # ========================================
    # 2. Add Peer Permissions
    # ========================================
    print("\n[2] Adding Peer Permissions...")
    
    # Admin: full access
    admin_perms = PeerPermissions(
        peer_id="admin-001",
        allow_tools=["*"],  # All tools
        allow_resources=["*"],  # All resources
        rate_limit=RateLimit(requests_per_minute=1000),
    )
    acl.add_peer(admin_perms)
    print("  Added: admin-001 (full access)")
    
    # User: limited access
    user_perms = PeerPermissions(
        peer_id="user-002",
        allow_tools=["read_*", "query_*"],  # Read-only tools
        deny_tools=["delete_*", "admin_*"],  # Deny dangerous tools
        allow_resources=["public/*"],
        deny_resources=["private/*"],
        rate_limit=RateLimit(requests_per_minute=60),
    )
    acl.add_peer(user_perms)
    print("  Added: user-002 (read-only)")
    
    # Guest: minimal access
    guest_perms = PeerPermissions(
        peer_id="guest-003",
        allow_tools=["help", "status"],
        rate_limit=RateLimit(requests_per_minute=10),
    )
    acl.add_peer(guest_perms)
    print("  Added: guest-003 (minimal)")
    
    # ========================================
    # 3. Check Tool Access
    # ========================================
    print("\n[3] Checking Tool Access...")
    
    test_cases = [
        ("admin-001", "delete_user"),
        ("user-002", "read_data"),
        ("user-002", "delete_user"),
        ("guest-003", "help"),
        ("guest-003", "read_data"),
        ("unknown", "anything"),
    ]
    
    for peer_id, tool in test_cases:
        result = acl.check(peer_id, "tools/call", {"name": tool})
        status = "✓" if result.permission == Permission.ALLOW else "✗"
        print(f"  {status} {peer_id} -> {tool}: {result.reason[:30]}")
    
    # ========================================
    # 4. Check Resource Access
    # ========================================
    print("\n[4] Checking Resource Access...")
    
    resource_tests = [
        ("user-002", "public/data.json"),
        ("user-002", "private/secrets.json"),
        ("admin-001", "private/secrets.json"),
    ]
    
    for peer_id, resource in resource_tests:
        result = acl.check(peer_id, "resources/read", {"uri": resource})
        status = "✓" if result.permission == Permission.ALLOW else "✗"
        print(f"  {status} {peer_id} -> {resource}")
    
    # ========================================
    # 5. Rate Limiting
    # ========================================
    print("\n[5] Rate Limiting...")
    
    print("  Guest rate limit: 10/min")
    
    # Simulate multiple requests
    for i in range(12):
        result = acl.check("guest-003", "tools/call", {"name": "status"})
        if result.permission == Permission.RATE_LIMITED:
            print(f"  Request {i+1}: RATE LIMITED")
            break
        elif result.permission == Permission.ALLOW:
            if i < 3 or i == 9:
                print(f"  Request {i+1}: allowed")
    
    # ========================================
    # 6. Audit Log
    # ========================================
    print("\n[6] Audit Log (last 3)...")
    
    audit = acl.get_audit_log(limit=3)
    for entry in audit:
        print(f"  {entry.get('peer_id', 'unknown')[:8]}: {entry.get('method', '?')}")
    
    # ========================================
    # 7. Export Configuration
    # ========================================
    print("\n[7] Export Configuration...")
    
    config = acl.to_dict()
    print(f"  Peers configured: {len(config.get('peers', {}))}")
    
    print("\n" + "=" * 50)
    print("Example 3 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
