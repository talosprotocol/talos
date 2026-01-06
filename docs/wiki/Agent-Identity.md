# Agent Identity

> **Status**: Implemented | **Code**: `src/core/did.py`, `talos/identity.py` | **Version**: 2.0.6

> **The Foundation: Every Agent Action Starts with Proven Identity**

This page defines how Talos handles cryptographic identity—the foundation that all other features (capabilities, audit, sessions) depend on.

---

## Overview

In Talos, an **identity** is:

1. A **key pair** (Ed25519 for signing, X25519 for encryption)
2. A **DID** (Decentralized Identifier) derived from the public key
3. Optional **metadata** (name, organization, creation time)

```
did:talos:a1b2c3d4e5f6...
         └─────────────────────┘
         Base58-encoded Ed25519 public key
```

---

## Identity Types

| Type | Description | Key Material |
|------|-------------|--------------|
| **Agent** | An autonomous AI agent | Generated per-agent |
| **User** | Human operator | Hardware key or secure enclave |
| **Tool** | MCP tool provider | Generated per-tool instance |
| **Organization** | Signing authority | Root key (HSM recommended) |

### Hierarchy

```
Organization Identity
       │
       ├── User Identity (human admin)
       │       │
       │       └── Agent Identity (user's agent)
       │
       └── Tool Identity (org-hosted tool)
```

---

## Key Material

Each identity has two key pairs:

| Key Type | Algorithm | Purpose |
|----------|-----------|---------|
| **Signing** | Ed25519 | Messages, capabilities, proofs |
| **Encryption** | X25519 | Session key exchange |

```python
@dataclass
class KeyPair:
    public_key: bytes   # 32 bytes
    private_key: bytes  # 32 bytes (never exported)
```

### Key Derivation

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Generate new identity
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# DID is derived from public key
did = f"did:talos:{base58_encode(public_key_bytes)}"
```

---

## DID Document

Each identity is represented as a W3C DID Document:

```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:talos:a1b2c3d4e5f6...",
  "verificationMethod": [
    {
      "id": "did:talos:a1b2c3...#key-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:talos:a1b2c3...",
      "publicKeyMultibase": "z6Mkf5rGMoatrSj1f..."
    }
  ],
  "keyAgreement": [
    {
      "id": "did:talos:a1b2c3...#key-2",
      "type": "X25519KeyAgreementKey2020",
      "publicKeyMultibase": "z6LShxJc8afWK..."
    }
  ],
  "service": [
    {
      "id": "did:talos:a1b2c3...#talos",
      "type": "TalosEndpoint",
      "serviceEndpoint": "talos://peer.example.com:8765"
    }
  ]
}
```

---

## Identity vs Capability

| Concept | What It Is | Analogy |
|---------|------------|---------|
| **Identity** | Who you are | Passport |
| **Capability** | What you're allowed to do | Visa stamp |

Identity proves you exist. Capabilities prove you have permission.

```
Agent presents: Identity (DID) + Capability (signed token)
                    │                    │
                    ▼                    ▼
             "I am Agent X"    "Owner Y granted me access to Z"
```

---

## Creating an Identity

### CLI

```bash
# Create new identity
talos init --name "my-agent"

# View identity
talos status
# Output:
#   DID: did:talos:a1b2c3d4e5f6...
#   Public Key: a1b2c3d4e5f6...
#   Created: 2024-12-24T08:00:00Z
```

### SDK

```python
from talos import Identity

# Create new identity
identity = Identity.create(name="my-agent")

# Or load existing
identity = Identity.load("~/.talos/wallet.json")

# Access DID
print(identity.did)  # did:talos:a1b2c3...
```

---

## Key Rotation

Keys should be rotated periodically or immediately on suspected compromise.

### Rotation Process

1. Generate new key pair
2. Publish new DID Document (via DHT)
3. Sign rotation announcement with old key
4. Keep old key for a grace period (verify old signatures)
5. Revoke old key

```python
# Rotate identity keys
new_identity = identity.rotate()

# Old key signs the rotation
rotation_proof = identity.sign_rotation(new_identity)

# Publish to DHT
await dht.publish_did(new_identity.did_document)
```

---

## Identity Resolution

How to look up an identity from its DID:

### 1. DHT Lookup (Decentralized)

```python
from talos.network import DHTResolver

resolver = DHTResolver(bootstrap_nodes)
did_document = await resolver.resolve("did:talos:a1b2c3...")
```

### 2. Registry Lookup (Centralized, Legacy)

```python
# Deprecated - use DHT instead
from talos.network import RegistryClient

client = RegistryClient("https://registry.example.com")
peer_info = await client.lookup("did:talos:a1b2c3...")
```

---

## Security Properties

| Property | Guarantee |
|----------|-----------|
| **Self-sovereign** | No authority can revoke your identity |
| **Cryptographic** | Identity is the key, not a username |
| **Non-transferable** | Private key never leaves device |
| **Verifiable offline** | No network needed to verify signatures |

---

## Storage

Identity key material is stored locally:

```
~/.talos/
├── wallet.json       # Encrypted identity
├── prekeys/          # One-time prekeys for sessions
└── sessions/         # Active session states
```

### Encryption at Rest

```python
# wallet.json is encrypted with PBKDF2 + ChaCha20-Poly1305
{
  "version": 2,
  "kdf": "pbkdf2",
  "iterations": 100000,
  "salt": "...",
  "ciphertext": "..."  # Encrypted key material
}
```

---

## See Also

- [Agent Capabilities](Agent-Capabilities) - What actions are authorized
- [Agent Lifecycle](Agent-Lifecycle) - Provisioning and rotation
- [DIDs & DHT](DIDs-DHT) - Decentralized identity resolution
- [Key Management](Key-Management) - Operational key handling
