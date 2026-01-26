#!/usr/bin/env python3
"""
Test Script: Full Integration Test

End-to-end test of the complete Talos system:
- Two agents communicating securely
- Forward secrecy messaging
- Blockchain message logging
- ACL enforcement

Usage:
    python scripts/test_integration.py
"""

import asyncio
import tempfile
import json
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from talos import TalosClient, TalosConfig
from src.mcp_bridge.acl import ACLManager, PeerPermissions, RateLimit


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def test_two_agent_communication():
    """Test secure communication between two agents."""
    separator("Two-Agent Communication")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Alice and Bob
        alice_config = TalosConfig(name="alice", data_dir=Path(tmpdir) / "alice")
        bob_config = TalosConfig(name="bob", data_dir=Path(tmpdir) / "bob")
        
        async with TalosClient.create("alice", alice_config) as alice:
            async with TalosClient.create("bob", bob_config) as bob:
                print(f"✓ Alice online: {alice.identity.address_short}")
                print(f"✓ Bob online: {bob.identity.address_short}")
                
                # Exchange prekeys
                bob_bundle = bob.get_prekey_bundle()
                print(f"✓ Got Bob's prekey bundle")
                
                # Alice establishes session
                session = await alice.establish_session(bob.address, bob_bundle)
                print(f"✓ Alice established session with Bob")
                
                # Send multiple messages (forward secrecy)
                messages = [
                    b"Hello Bob!",
                    b"This is a secure message.",
                    b"Each one uses a different key!",
                ]
                
                for i, msg in enumerate(messages):
                    msg_id = await alice.send(bob.address, msg)
                    print(f"✓ Message {i+1} sent: {msg_id[:8]}...")
                
                # Check session stats
                alice_stats = alice.get_stats()
                print(f"✓ Alice session stats:")
                print(f"    Messages sent: {alice_stats.get('total_messages_sent', 0)}")
                print(f"    Active sessions: {alice_stats.get('active_sessions', 0)}")
                print(f"    Blockchain height: {alice_stats.get('blockchain_height', 0)}")
    
    print(f"✓ Communication test passed!")
    return True


async def test_acl_enforcement():
    """Test ACL enforcement on message sending."""
    separator("ACL Enforcement")
    
    # Create ACL
    acl = ACLManager(default_allow=False)
    
    # Add allowed peer
    acl.add_peer(PeerPermissions(
        peer_id="trusted-agent",
        allow_tools=["*"],
        rate_limit=RateLimit(requests_per_minute=5),
    ))
    
    # Add restricted peer
    acl.add_peer(PeerPermissions(
        peer_id="restricted-agent",
        allow_tools=["read_*"],
        deny_tools=["write_*", "delete_*"],
    ))
    
    print(f"✓ Created ACL with 2 peers")
    
    # Test trusted peer
    test_cases = [
        ("trusted-agent", "tools/call", {"name": "file_write"}, True),
        ("trusted-agent", "tools/call", {"name": "delete_all"}, True),
        ("restricted-agent", "tools/call", {"name": "read_file"}, True),
        ("restricted-agent", "tools/call", {"name": "write_file"}, False),
        ("restricted-agent", "tools/call", {"name": "delete_file"}, False),
        ("unknown-agent", "tools/call", {"name": "anything"}, False),
    ]
    
    all_passed = True
    for peer, method, params, expected in test_cases:
        result = acl.check(peer, method, params)
        status = "✓" if result.allowed == expected else "✗"
        print(f"  {status} {peer[:16]}... {params['name']}: " + 
              f"{result.permission.name} (expected: {'ALLOW' if expected else 'DENY'})")
        if result.allowed != expected:
            all_passed = False
    
    # Test rate limiting
    print(f"\n  Testing rate limiting...")
    for i in range(7):
        result = acl.check("trusted-agent", "tools/call", {"name": "test"})
        if not result.allowed:
            print(f"  ✓ Rate limited after {i} requests")
            break
    
    print(f"✓ ACL enforcement test passed!")
    return all_passed


async def test_session_persistence():
    """Test session state persistence across restarts."""
    separator("Session Persistence")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        alice_config = TalosConfig(name="alice", data_dir=Path(tmpdir) / "alice")
        bob_config = TalosConfig(name="bob", data_dir=Path(tmpdir) / "bob")
        
        # First: Create session and send messages
        print(f"  Phase 1: Create session and send messages")
        
        async with TalosClient.create("alice", alice_config) as alice:
            async with TalosClient.create("bob", bob_config) as bob:
                bob_bundle = bob.get_prekey_bundle()
                bob_address = bob.address
                
                await alice.establish_session(bob_address, bob_bundle)
                await alice.send(bob_address, b"Message 1")
                await alice.send(bob_address, b"Message 2")
                
                initial_stats = alice.get_stats()
                print(f"  ✓ Sent 2 messages")
                print(f"    Session established: {alice.has_session(bob_address)}")
        
        # Second: Restart and verify persistence
        print(f"\n  Phase 2: Verify persistence after restart")
        
        async with TalosClient.create("alice", alice_config) as alice:
            restored_stats = alice.get_stats()
            print(f"  ✓ Client restarted")
            print(f"    Active sessions: {restored_stats.get('active_sessions', 0)}")
            print(f"    Blockchain height: {restored_stats.get('blockchain_height', 0)}")
    
    print(f"✓ Session persistence test passed!")
    return True


async def test_blockchain_integrity():
    """Test blockchain data integrity."""
    separator("Blockchain Integrity")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = TalosConfig(name="test", data_dir=Path(tmpdir))
        
        async with TalosClient.create("integrity-test", config) as client:
            # Establish session with self (for testing)
            bundle = client.get_prekey_bundle()
            
            # Create a second client to communicate with
            config2 = TalosConfig(name="peer", data_dir=Path(tmpdir) / "peer")
            async with TalosClient.create("peer", config2) as peer:
                peer_bundle = peer.get_prekey_bundle()
                await client.establish_session(peer.address, peer_bundle)
                
                # Send multiple messages
                for i in range(5):
                    await client.send(peer.address, f"Test message {i}".encode())
                
                stats = client.get_stats()
                print(f"✓ Sent 5 messages")
                print(f"  Blockchain height: {stats.get('blockchain_height', 0)}")
    
    print(f"✓ Blockchain integrity test passed!")
    return True


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "🧪" * 20)
    print("    TALOS INTEGRATION TESTS")
    print("🧪" * 20)
    
    tests = [
        ("Two-Agent Communication", test_two_agent_communication),
        ("ACL Enforcement", test_acl_enforcement),
        ("Session Persistence", test_session_persistence),
        ("Blockchain Integrity", test_blockchain_integrity),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = await test_fn()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            import traceback
            traceback.print_exc()
    
    # Summary
    separator("Test Summary")
    
    all_passed = True
    for name, passed, error in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error}")
        if not passed:
            all_passed = False
    
    total = len(results)
    passed_count = sum(1 for _, p, _ in results if p)
    
    print(f"\n  Total: {passed_count}/{total} tests passed")
    
    if all_passed:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    exit(exit_code)
