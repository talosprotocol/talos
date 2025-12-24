#!/usr/bin/env python3
"""
Example 10: SDK Quick Start

This example demonstrates the high-level Talos SDK API.
It corresponds to the "Quick Start" section in the documentation.
"""

import asyncio
import os
import shutil
from talos import TalosClient, SecureChannel, TalosConfig

async def main():
    print("=" * 50)
    print("Example 10: SDK Quick Start")
    print("=" * 50)
    
    # Clean up previous run artifacts for this example loop
    # (Optional, but good for demo clarity)
    
    print("\n[1] Creating Clients...")
    # Create two clients simulating two different agents
    # The config automatically namespaces their key files based on name
    alice = TalosClient.create("alice")
    bob = TalosClient.create("bob")
    
    await alice.start()
    await bob.start()
    
    print(f"  Alice: {alice.address[:16]}...")
    print(f"  Bob:   {bob.address[:16]}...")
    
    print("\n[2] Exchanging Connection Info...")
    # In a real app, this happens via the Registry or out-of-band
    bob_bundle = bob.get_prekey_bundle()
    
    print("\n[3] Establishing Secure Session...")
    # Alice initiates session with Bob
    session = await alice.establish_session(bob.address, bob_bundle)
    print(f"  Session established with: {session.peer_id[:8]}...")
    
    print("\n[4] Sending Encrypted Message...")
    # Use SecureChannel context manager for cleaner resource handling
    async with SecureChannel(alice, bob.address, bob_bundle) as channel:
        message_id = await channel.send(b"Hello from the SDK!")
        print(f"  Sent message: {message_id}")
        
        # Note: Bob needs to be listening to 'receive' this.
        # Since we run in one process, we can't easily await bob.receive() 
        # while blocked on channel.send() unless we use concurrent tasks.
        # For this quickstart, 'send' success proves the encryption worked.
    
    print("\n[5] Cleanup...")
    await alice.stop()
    await bob.stop()
    print("  Clients stopped.")
    
    print("\n" + "=" * 50)
    print("Example 10 Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
