#!/usr/bin/env python3
"""
Test Script: API Demo

Demonstrates the core Talos API functionality:
- Blockchain operations
- Double Ratchet sessions
- Validation engine
- ACL system

Usage:
    python scripts/test_api_demo.py
"""

import asyncio
import tempfile
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.blockchain import Blockchain, Block
from src.core.crypto import (
    generate_signing_keypair,
    generate_encryption_keypair,
    sign_message,
    verify_signature,
    derive_shared_secret,
    encrypt_message,
    decrypt_message,
)
from src.core.session import (
    SessionManager,
    PrekeyBundle,
    Session,
)
from src.core.validation import (
    ValidationEngine,
    ValidationLevel,
    generate_audit_report,
)
from src.mcp_bridge.acl import (
    ACLManager,
    PeerPermissions,
    RateLimit,
)


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_crypto():
    """Demonstrate cryptographic primitives."""
    separator("Cryptographic Primitives")
    
    # Key generation
    signing_keys = generate_signing_keypair()
    encryption_keys = generate_encryption_keypair()
    
    print(f"✓ Generated signing keypair (Ed25519)")
    print(f"  Public: {signing_keys.public_key[:8].hex()}...")
    
    print(f"✓ Generated encryption keypair (X25519)")
    print(f"  Public: {encryption_keys.public_key[:8].hex()}...")
    
    # Signing
    message = b"Hello, Talos!"
    signature = sign_message(message, signing_keys.private_key)
    valid = verify_signature(message, signature, signing_keys.public_key)
    
    print(f"✓ Signed message: {signature[:8].hex()}...")
    print(f"  Verified: {valid}")
    
    # Key exchange
    alice_keys = generate_encryption_keypair()
    bob_keys = generate_encryption_keypair()
    
    alice_secret = derive_shared_secret(alice_keys.private_key, bob_keys.public_key)
    bob_secret = derive_shared_secret(bob_keys.private_key, alice_keys.public_key)
    
    print(f"✓ Derived shared secret")
    print(f"  Secrets match: {alice_secret == bob_secret}")
    
    # Encryption
    plaintext = b"Top secret message!"
    nonce, ciphertext = encrypt_message(plaintext, alice_secret)
    decrypted = decrypt_message(ciphertext, bob_secret, nonce)
    
    print(f"✓ Encrypted: {ciphertext[:8].hex()}...")
    print(f"  Decrypted: {decrypted.decode()}")


def demo_blockchain():
    """Demonstrate blockchain operations."""
    separator("Blockchain Operations")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create blockchain
        bc = Blockchain(difficulty=1)  # Low difficulty for demo
        print(f"✓ Created blockchain")
        print(f"  Difficulty: {bc.difficulty}")
        print(f"  Chain length: {len(bc.chain)}")
        
        # Add data
        bc.add_data({"sender": "alice", "message": "Hello!"})
        bc.add_data({"sender": "bob", "message": "Hi back!"})
        print(f"✓ Added 2 messages")
        print(f"  Pending data: {len(bc.pending_data)}")
        
        # Mine block
        bc.mine_pending()
        print(f"✓ Mined block")
        print(f"  Chain length: {len(bc.chain)}")
        print(f"  Latest hash: {bc.chain[-1].hash[:16]}...")
        
        # Validate chain
        is_valid = bc.validate_chain(bc.chain)
        print(f"✓ Chain valid: {is_valid}")
        
        # Save and load
        path = Path(tmpdir) / "chain.json"
        bc.save(path)
        print(f"✓ Saved to {path}")
        
        loaded_bc = Blockchain.load(path)
        print(f"✓ Loaded: {len(loaded_bc.chain)} blocks")


async def demo_double_ratchet():
    """Demonstrate Double Ratchet sessions."""
    separator("Double Ratchet Protocol")
    
    # Create Alice and Bob
    alice_identity = generate_signing_keypair()
    bob_identity = generate_signing_keypair()
    
    alice_manager = SessionManager(alice_identity)
    bob_manager = SessionManager(bob_identity)
    
    print(f"✓ Created session managers")
    print(f"  Alice: {alice_identity.public_key_short}")
    print(f"  Bob: {bob_identity.public_key_short}")
    
    # Get Bob's prekey bundle
    bob_bundle = bob_manager.get_prekey_bundle()
    print(f"✓ Got Bob's prekey bundle")
    print(f"  Verified: {bob_bundle.verify()}")
    
    # Alice creates session
    alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
    print(f"✓ Alice created session with Bob")
    
    # Encrypt message
    plaintext = b"Hello Bob! This uses forward secrecy."
    encrypted = alice_session.encrypt(plaintext)
    print(f"✓ Encrypted: {len(encrypted)} bytes")
    
    # Multiple messages (keys ratchet)
    msg2 = alice_session.encrypt(b"Second message")
    msg3 = alice_session.encrypt(b"Third message")
    print(f"✓ Sent 3 messages (keys ratcheted)")
    print(f"  Messages sent: {alice_session.messages_sent}")
    
    # Session stats
    stats = alice_manager.get_stats()
    print(f"✓ Session stats: {stats}")


async def demo_validation():
    """Demonstrate validation engine."""
    separator("Validation Engine")
    
    # Create blockchain with blocks
    bc = Blockchain(difficulty=1)
    bc.add_data({"test": "data"})
    bc.mine_pending()
    
    print(f"✓ Created blockchain with {len(bc.chain)} blocks")
    
    # Create validation engine
    engine = ValidationEngine(difficulty=1)
    print(f"✓ Created validation engine")
    
    # Validate latest block
    block = bc.chain[-1]
    previous = bc.chain[-2] if len(bc.chain) > 1 else None
    
    result = await engine.validate_block(block, previous)
    print(f"✓ Validated block")
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    
    # Validate whole chain
    chain_result = await engine.validate_chain(bc.chain)
    print(f"✓ Validated chain")
    print(f"  Valid: {chain_result.is_valid}")
    
    # Get metrics
    metrics = engine.get_metrics()
    print(f"✓ Metrics: {metrics}")
    
    # Generate audit report (with correct interface)
    report = generate_audit_report(block, result)
    print(f"✓ Generated audit report")
    print(f"  Report ID: {report.report_id[:8]}...")
    print(f"  Block valid: {report.is_valid}")
    print(f"  Hash verified: {report.hash_verified}")
    print(f"  PoW verified: {report.pow_verified}")


def demo_acl():
    """Demonstrate ACL system."""
    separator("Access Control (ACL)")
    
    # Create ACL manager
    acl = ACLManager(default_allow=False)
    print(f"✓ Created ACL manager (default deny)")
    
    # Add peer with permissions
    perms = PeerPermissions(
        peer_id="agent-123",
        allow_tools=["file_read", "git_*"],
        deny_tools=["rm_*", "delete_*"],
        allow_resources=["//localhost/repo/**"],
        rate_limit=RateLimit(requests_per_minute=10),
    )
    acl.add_peer(perms)
    print(f"✓ Added peer permissions")
    print(f"  Allowed tools: {perms.allow_tools}")
    print(f"  Denied tools: {perms.deny_tools}")
    
    # Check permissions
    result1 = acl.check("agent-123", "tools/call", {"name": "file_read"})
    print(f"✓ file_read: {result1.permission.name} ({result1.reason})")
    
    result2 = acl.check("agent-123", "tools/call", {"name": "git_status"})
    print(f"✓ git_status: {result2.permission.name} ({result2.reason})")
    
    result3 = acl.check("agent-123", "tools/call", {"name": "rm_file"})
    print(f"✓ rm_file: {result3.permission.name} ({result3.reason})")
    
    result4 = acl.check("unknown", "tools/call", {"name": "anything"})
    print(f"✓ unknown peer: {result4.permission.name} ({result4.reason})")
    
    # Rate limiting
    print(f"\n  Testing rate limiting (10/min)...")
    for i in range(12):
        result = acl.check("agent-123", "tools/call", {"name": "file_read"})
        if not result.allowed:
            print(f"  Request {i+1}: {result.permission.name}")
            break
    
    # Audit log
    log = acl.get_audit_log(limit=5)
    print(f"✓ Audit log: {len(log)} entries")


async def main():
    """Run all demos."""
    print("\n" + "🔐" * 20)
    print("       TALOS API DEMO")
    print("🔐" * 20)
    
    try:
        demo_crypto()
        demo_blockchain()
        await demo_double_ratchet()
        await demo_validation()
        demo_acl()
        
        separator("All Demos Complete! ✅")
        print("\nThe Talos API is working correctly.")
        print("See docs/wiki/ for full documentation.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
