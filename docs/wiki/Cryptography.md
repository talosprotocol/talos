# Cryptography Guide

## Overview

Talos implements a modern cryptographic stack designed for:
- **128-bit security level**
- **Forward secrecy** (compromised keys don't expose past messages)
- **Non-repudiation** (messages are signed and cannot be denied)
- **Authenticated encryption** (integrity + confidentiality)

## Cryptographic Primitives

### Digital Signatures: Ed25519

**Purpose**: Message authentication and non-repudiation

| Property | Value |
|----------|-------|
| Algorithm | Ed25519 (Curve25519 + EdDSA) |
| Security | 128-bit |
| Private Key | 32 bytes |
| Public Key | 32 bytes |
| Signature | 64 bytes |
| Sign Time | ~0.13ms |
| Verify Time | ~0.27ms |

**Usage**:
```python
from src.core.crypto import generate_signing_keypair, sign_message, verify_signature

# Generate keys
keys = generate_signing_keypair()

# Sign
message = b"Hello, World!"
signature = sign_message(message, keys.private_key)

# Verify
is_valid = verify_signature(message, signature, keys.public_key)
```

**Why Ed25519?**
- Faster than RSA/ECDSA
- Deterministic (same message + key = same signature)
- Resistant to timing attacks
- Used by Signal, SSH, TLS 1.3

---

### Key Exchange: X25519

**Purpose**: Establish shared secret between peers

| Property | Value |
|----------|-------|
| Algorithm | X25519 (ECDH on Curve25519) |
| Security | 128-bit |
| Private Key | 32 bytes |
| Public Key | 32 bytes |
| Shared Secret | 32 bytes |
| Exchange Time | ~0.19ms |

**Usage**:
```python
from src.core.crypto import generate_encryption_keypair, derive_shared_secret

# Each peer generates keys
alice_keys = generate_encryption_keypair()
bob_keys = generate_encryption_keypair()

# Exchange public keys, then derive shared secret
# (Both get the same secret!)
alice_secret = derive_shared_secret(alice_keys.private_key, bob_keys.public_key)
bob_secret = derive_shared_secret(bob_keys.private_key, alice_keys.public_key)

assert alice_secret == bob_secret  # True!
```

**Flow**:
```
Alice                              Bob
  │                                  │
  │──── alice_public_key ───────────▶│
  │◀─── bob_public_key ─────────────│
  │                                  │
  │ shared = ECDH(alice_priv, bob_pub)
  │                                  │ shared = ECDH(bob_priv, alice_pub)
  │                                  │
  │    (Both have same shared secret)
```

---

### Symmetric Encryption: ChaCha20-Poly1305

**Purpose**: Message confidentiality and integrity

| Property | Value |
|----------|-------|
| Algorithm | ChaCha20-Poly1305 (AEAD) |
| Key Size | 256 bits (32 bytes) |
| Nonce Size | 96 bits (12 bytes) |
| Auth Tag | 128 bits (16 bytes) |
| Encrypt Time | ~0.003ms (1.4KB) |
| Decrypt Time | ~0.005ms (1.4KB) |

**Usage**:
```python
from src.core.crypto import encrypt_message, decrypt_message

# Encrypt
nonce, ciphertext = encrypt_message(plaintext, shared_secret)

# Decrypt
plaintext = decrypt_message(ciphertext, shared_secret, nonce)
```

**Why ChaCha20-Poly1305?**
- Same cipher as TLS 1.3
- 300K+ encryptions/sec
- Authenticated: tampering is detected
- No padding oracle attacks
- Software-friendly (no AES-NI required)

---

### Hashing: SHA-256

**Purpose**: Data integrity, block hashing, Merkle trees

| Property | Value |
|----------|-------|
| Algorithm | SHA-256 |
| Output | 256 bits (32 bytes / 64 hex chars) |
| Hash Time | ~0.001ms (1KB) |

**Usage**:
```python
from src.core.crypto import hash_data, hash_string

digest = hash_data(b"binary data")
digest = hash_string("text data")
```

---

## Security Model

### End-to-End Encryption Flow

```
Sender                                           Recipient
  │                                                   │
  │  1. Generate ephemeral X25519 key pair            │
  │  2. Derive shared secret with recipient's pubkey  │
  │  3. Encrypt message with ChaCha20-Poly1305        │
  │  4. Sign encrypted payload with Ed25519           │
  │  5. Send: [signature, nonce, ciphertext]          │
  │                                                   │
  │─────────────────────────────────────────────────▶│
  │                                                   │
  │          6. Verify signature with sender's pubkey │
  │          7. Derive shared secret with own privkey │
  │          8. Decrypt with ChaCha20-Poly1305        │
  │                                                   │
```

### Trust Model

1. **Identity = Public Key**: Your Ed25519 public key IS your address
2. **Registry Bootstrap**: Initial peer discovery via registry (can be replaced)
3. **P2P Verification**: All messages are signature-verified
4. **No Central Authority**: Keys are self-generated, no certificates

### Threat Model

| Threat | Protection |
|--------|------------|
| Eavesdropping | ChaCha20-Poly1305 encryption |
| Message tampering | Poly1305 authentication tag |
| Impersonation | Ed25519 signature verification |
| Replay attacks | Unique message IDs + timestamps |
| Man-in-the-middle | Out-of-band key verification (future: TOFU) |

### Key Management

**Wallet Storage** (`~/.talos/wallet.json`):
```json
{
  "name": "Alice",
  "signing_keys": {
    "private_key": "base64...",
    "public_key": "base64..."
  },
  "encryption_keys": {
    "private_key": "base64...",
    "public_key": "base64..."
  }
}
```

**Best Practices**:
- [ ] Protect wallet file with filesystem permissions
- [ ] Consider encrypting wallet with passphrase (future work)
- [ ] Backup wallet securely
- [ ] Rotate keys periodically (future work)

---

## Comparison with Other Systems

| System | Signing | Key Exchange | Encryption |
|--------|---------|--------------|------------|
| **Talos** | Ed25519 | X25519 | ChaCha20-Poly1305 |
| Signal | Ed25519 | X3DH + Double Ratchet | AES-256-GCM |
| WhatsApp | Ed25519 | X3DH | AES-256-GCM |
| PGP/GPG | RSA/ECDSA | RSA/ECDH | AES-256-CBC |
| TLS 1.3 | Various | X25519/ECDHE | ChaCha20-Poly1305/AES-GCM |

BMP uses the same primitives as modern TLS 1.3, ensuring strong security without legacy baggage.
