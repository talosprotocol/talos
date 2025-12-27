#!/usr/bin/env python3
"""
Example 10: SDK Quick Start

This example demonstrates the high-level Talos API:
- Wallet generation
- Cryptographic operations
- Blockchain basics
"""


from src.core.crypto import Wallet, verify_signature
from src.core.blockchain import Blockchain


def main():
    print("=" * 50)
    print("Example 10: SDK Quick Start")
    print("=" * 50)
    
    print("\n[1] Creating Wallets...")
    
    alice = Wallet.generate("alice")
    bob = Wallet.generate("bob")
    
    print(f"  Alice: {alice.address_short}")
    print(f"  Bob:   {bob.address_short}")
    
    print("\n[2] Cryptographic Operations...")
    
    # Sign a message
    message = b"Hello from Alice!"
    signature = alice.sign(message)
    print(f"  Message: {message.decode()}")
    print(f"  Signature: {signature.hex()[:32]}...")
    
    # Verify signature
    is_valid = verify_signature(message, signature, alice.signing_keys.public_key)
    print(f"  Signature valid: {is_valid}")
    
    print("\n[3] Blockchain Operations...")
    
    # Create a blockchain
    blockchain = Blockchain(difficulty=1)
    print("  Blockchain created")
    print(f"  Height: {blockchain.height}")
    print(f"  Genesis hash: {blockchain.chain[0].hash[:16]}...")
    
    print("\n[4] Wallet Serialization...")
    
    # Save and load
    wallet_dict = alice.model_dump()
    alice_restored = Wallet.model_validate(wallet_dict)
    print(f"  Saved keys: {list(wallet_dict.keys())}")
    print(f"  Restored: {alice_restored.address_short}")
    print(f"  Match: {alice.address == alice_restored.address}")
    
    print("\n" + "=" * 50)
    print("Example 10 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
