#!/usr/bin/env python3
"""
Test Script: SDK Demo

Demonstrates the Talos SDK functionality:
- Identity creation and management
- Client lifecycle
- Session establishment
- Encrypted messaging

Usage:
    python scripts/test_sdk_demo.py
"""

import asyncio
import tempfile
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from talos import TalosClient, TalosConfig, Identity
from talos.channel import SecureChannel


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def demo_identity():
    """Demonstrate identity management."""
    separator("Identity Management")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create new identity
        identity = Identity.create("demo-agent")
        print(f"✓ Created identity: {identity.name}")
        print(f"  Address: {identity.address[:32]}...")
        print(f"  Short: {identity.address_short}")
        
        # Sign data
        data = b"Hello, Talos!"
        signature = identity.sign(data)
        print(f"✓ Signed data: {signature[:16].hex()}...")
        
        # Save and load
        path = Path(tmpdir) / "keys.json"
        identity.save(path)
        print(f"✓ Saved identity to {path}")
        
        loaded = Identity.load(path)
        print(f"✓ Loaded identity: {loaded.address_short}")
        
        # Get prekey bundle
        bundle = identity.get_prekey_bundle()
        print(f"✓ Generated prekey bundle")
        print(f"  Identity key: {bundle.identity_key[:8].hex()}...")
        print(f"  Verified: {bundle.verify()}")


async def demo_config():
    """Demonstrate configuration options."""
    separator("Configuration")
    
    # Default config
    config = TalosConfig()
    print(f"✓ Default config:")
    print(f"  Name: {config.name}")
    print(f"  Difficulty: {config.difficulty}")
    print(f"  Forward Secrecy: {config.forward_secrecy}")
    
    # Development config
    dev_config = TalosConfig.development()
    print(f"\n✓ Development preset:")
    print(f"  Difficulty: {dev_config.difficulty}")
    print(f"  Log Level: {dev_config.log_level}")
    
    # Production config
    prod_config = TalosConfig.production()
    print(f"\n✓ Production preset:")
    print(f"  Difficulty: {prod_config.difficulty}")
    print(f"  Log Level: {prod_config.log_level}")


async def demo_client():
    """Demonstrate client lifecycle."""
    separator("Client Lifecycle")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = TalosConfig(name="test", data_dir=Path(tmpdir))
        
        # Create client
        client = TalosClient.create("demo-client", config)
        print(f"✓ Created client: {client}")
        print(f"  Running: {client.is_running}")
        
        # Start client
        await client.start()
        print(f"✓ Started client")
        print(f"  Running: {client.is_running}")
        
        # Get stats
        stats = client.get_stats()
        print(f"✓ Stats: {stats}")
        
        # Get prekey bundle
        bundle = client.get_prekey_bundle()
        print(f"✓ Prekey bundle ready: {len(bundle)} fields")
        
        # Stop client
        await client.stop()
        print(f"✓ Stopped client")
        print(f"  Running: {client.is_running}")


async def demo_session():
    """Demonstrate session establishment between two agents."""
    separator("Session Establishment")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two clients
        config_alice = TalosConfig(name="alice", data_dir=Path(tmpdir) / "alice")
        config_bob = TalosConfig(name="bob", data_dir=Path(tmpdir) / "bob")
        
        alice = TalosClient.create("alice", config_alice)
        bob = TalosClient.create("bob", config_bob)
        
        print(f"✓ Created Alice: {alice.identity.address_short}")
        print(f"✓ Created Bob: {bob.identity.address_short}")
        
        # Start both
        await alice.start()
        await bob.start()
        print(f"✓ Both clients started")
        
        # Get Bob's prekey bundle
        bob_bundle = bob.get_prekey_bundle()
        print(f"✓ Got Bob's prekey bundle")
        
        # Alice establishes session with Bob
        session = await alice.establish_session(bob.address, bob_bundle)
        print(f"✓ Alice established session with Bob")
        print(f"  Session peer: {session.peer_id[:32]}...")
        
        # Check session status
        print(f"✓ Alice has session with Bob: {alice.has_session(bob.address)}")
        
        # Cleanup
        await alice.stop()
        await bob.stop()
        print(f"✓ Both clients stopped")


async def demo_messaging():
    """Demonstrate encrypted messaging."""
    separator("Encrypted Messaging")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        config_alice = TalosConfig(name="alice", data_dir=Path(tmpdir) / "alice")
        config_bob = TalosConfig(name="bob", data_dir=Path(tmpdir) / "bob")
        
        async with TalosClient.create("alice", config_alice) as alice:
            async with TalosClient.create("bob", config_bob) as bob:
                print(f"✓ Alice and Bob online")
                
                # Establish session
                bob_bundle = bob.get_prekey_bundle()
                await alice.establish_session(bob.address, bob_bundle)
                print(f"✓ Session established")
                
                # Send message
                message = b"Hello, Bob! This is encrypted with forward secrecy."
                msg_id = await alice.send(bob.address, message)
                print(f"✓ Alice sent message: {msg_id[:8]}...")
                
                # Check stats
                alice_stats = alice.get_stats()
                print(f"✓ Alice stats: {alice_stats}")


async def demo_context_manager():
    """Demonstrate async context manager usage."""
    separator("Context Manager Usage")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = TalosConfig(name="ctx", data_dir=Path(tmpdir))
        
        # Using client as context manager
        async with TalosClient.create("context-demo", config) as client:
            print(f"✓ Client running: {client.is_running}")
            print(f"  Address: {client.address[:32]}...")
            
            stats = client.get_stats()
            print(f"  Blockchain height: {stats.get('blockchain_height', 'N/A')}")
        
        print(f"✓ Client automatically stopped")


async def main():
    """Run all demos."""
    print("\n" + "🚀" * 20)
    print("       TALOS SDK DEMO")
    print("🚀" * 20)
    
    try:
        await demo_identity()
        await demo_config()
        await demo_client()
        await demo_session()
        await demo_messaging()
        await demo_context_manager()
        
        separator("All Demos Complete! ✅")
        print("\nThe Talos SDK is working correctly.")
        print("See docs/wiki/Python-SDK.md for full documentation.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
