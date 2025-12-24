#!/usr/bin/env python3
"""
Example 1: Cryptographic Primitives

This example demonstrates:
- Key generation (Ed25519 signing, X25519 encryption)
- Digital signatures
- Key exchange and encryption

Copy-paste ready!
"""

from src.core.crypto import (
    KeyPair,
    Wallet,
    generate_signing_keypair,
    generate_encryption_keypair,
    sign_message,
    verify_signature,
    derive_shared_secret,
    encrypt_message,
    decrypt_message,
    hash_data,
)


def main():
    print("=" * 50)
    print("Example 1: Cryptographic Primitives")
    print("=" * 50)
    
    # ========================================
    # 1. Generate Wallet (Full Identity)
    # ========================================
    print("\n[1] Creating Wallet...")
    
    alice = Wallet.generate("alice")
    bob = Wallet.generate("bob")
    
    print(f"  Alice: {alice.address_short}")
    print(f"  Bob: {bob.address_short}")
    
    # ========================================
    # 2. Digital Signatures (Ed25519)
    # ========================================
    print("\n[2] Digital Signatures...")
    
    message = b"Hello, Bob!"
    
    # Alice signs
    signature = alice.sign(message)
    print(f"  Message: {message.decode()}")
    print(f"  Signature: {signature.hex()[:32]}...")
    
    # Anyone can verify with Alice's public key
    is_valid = verify_signature(
        message, 
        signature, 
        alice.signing_keys.public_key
    )
    print(f"  Valid: {is_valid}")
    
    # Tampered message fails
    tampered = b"Hello, Evil!"
    is_valid_tampered = verify_signature(
        tampered, 
        signature, 
        alice.signing_keys.public_key
    )
    print(f"  Tampered valid: {is_valid_tampered}")
    
    # ========================================
    # 3. Key Exchange (X25519)
    # ========================================
    print("\n[3] Key Exchange (X25519)...")
    
    # Alice computes shared secret with Bob's public key
    alice_shared = derive_shared_secret(
        alice.encryption_keys.private_key,
        bob.encryption_keys.public_key
    )
    
    # Bob computes shared secret with Alice's public key
    bob_shared = derive_shared_secret(
        bob.encryption_keys.private_key,
        alice.encryption_keys.public_key
    )
    
    print(f"  Alice's shared: {alice_shared.hex()[:16]}...")
    print(f"  Bob's shared:   {bob_shared.hex()[:16]}...")
    print(f"  Match: {alice_shared == bob_shared}")
    
    # ========================================
    # 4. Encryption (ChaCha20-Poly1305)
    # ========================================
    print("\n[4] Symmetric Encryption...")
    
    plaintext = b"Secret message for Bob!"
    
    # Alice encrypts with shared secret
    nonce, ciphertext = encrypt_message(plaintext, alice_shared)
    print(f"  Plaintext: {plaintext.decode()}")
    print(f"  Ciphertext: {ciphertext.hex()[:24]}...")
    print(f"  Nonce: {nonce.hex()}")
    
    # Bob decrypts with same shared secret
    decrypted = decrypt_message(ciphertext, bob_shared, nonce)
    print(f"  Decrypted: {decrypted.decode()}")
    
    # ========================================
    # 5. Hashing (SHA-256)
    # ========================================
    print("\n[5] Hashing...")
    
    data = b"Important data to hash"
    hash_hex = hash_data(data)
    print(f"  Data: {data.decode()}")
    print(f"  SHA-256: {hash_hex[:32]}...")
    
    # ========================================
    # 6. Wallet Serialization
    # ========================================
    print("\n[6] Wallet Serialization...")
    
    # Save wallet
    wallet_dict = alice.model_dump()
    print(f"  Saved keys: {list(wallet_dict.keys())}")
    
    # Load wallet
    alice_loaded = Wallet.model_validate(wallet_dict)
    print(f"  Loaded: {alice_loaded.address_short}")
    print(f"  Match: {alice.address == alice_loaded.address}")
    
    print("\n" + "=" * 50)
    print("Example 1 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
