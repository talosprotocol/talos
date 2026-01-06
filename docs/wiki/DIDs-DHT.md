# Decentralized Identity (DIDs) and DHT

> **Self-sovereign identity with decentralized peer discovery**

## Overview

Talos implements [W3C DID Core](https://www.w3.org/TR/did-core/) for self-sovereign identity, eliminating reliance on centralized registry servers. DIDs are resolved via a Kademlia Distributed Hash Table (DHT).

---

## DID Format

```
did:talos:<32-char-hex-pubkey-hash>
```

Example: `did:talos:a1b2c3d4e5f6789012345678abcdef01`

---

## Quick Start

### Create DID

```python
from src.core.did import DIDManager
from src.core.crypto import generate_signing_keypair

# Generate identity
keypair = generate_signing_keypair()

# Create DID manager
manager = DIDManager(keypair)

# Get DID
did = manager.did  # did:talos:...

# Create document
doc = manager.create_document(
    service_endpoint="wss://my-agent.com:8765"
)

print(doc.to_json())
```

### Publish to DHT

```python
from src.network.dht import DHTNode, DIDResolver

# Create DHT node
node = DHTNode(host="0.0.0.0", port=8468)
await node.start()

# Bootstrap into network
await node.bootstrap(bootstrap_nodes)

# Publish DID document
resolver = DIDResolver(node)
await resolver.publish(did, doc.to_dict())
```

### Resolve DID

```python
# Resolve DID to document
document = await resolver.resolve("did:talos:abc123...")

if document:
    # Get messaging endpoint
    for svc in document.get("service", []):
        if svc["type"] == "TalosMessaging":
            endpoint = svc["serviceEndpoint"]
```

---

## DID Document Structure

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:talos:abc123...",
  "verificationMethod": [
    {
      "id": "did:talos:abc123...#key-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:talos:abc123...",
      "publicKeyMultibase": "z..."
    }
  ],
  "authentication": ["did:talos:abc123...#key-1"],
  "keyAgreement": ["did:talos:abc123...#key-2"],
  "service": [
    {
      "id": "did:talos:abc123...#messaging",
      "type": "TalosMessaging",
      "serviceEndpoint": "wss://agent.example.com:8765"
    }
  ]
}
```

---

## DHT Architecture

### Kademlia Protocol

| Parameter | Value | Description |
|-----------|-------|-------------|
| **k** | 20 | Bucket size (max contacts per bucket) |
| **α** | 3 | Parallelism factor |
| **ID bits** | 256 | Node ID size (SHA-256) |

### XOR Distance

Nodes are organized by XOR distance in the 256-bit ID space:

```
distance(A, B) = A ⊕ B
```

### K-Buckets

Each node maintains 256 buckets, organized by XOR distance prefix:

```
Bucket 0: Nodes at distance 2^0 - 2^1
Bucket 1: Nodes at distance 2^1 - 2^2
...
Bucket 255: Nodes at distance 2^255 - 2^256
```

---

## RPC Messages

| Message | Purpose |
|---------|---------|
| `PING` | Check node liveness |
| `FIND_NODE` | Find k closest nodes to ID |
| `FIND_VALUE` | Get value or closest nodes |
| `STORE` | Store key-value pair |

---

## Design Patterns (SOLID)

### Single Responsibility
- `DIDDocument` - Document structure only
- `DIDManager` - Document lifecycle management
- `DHTStorage` - Local storage only
- `RoutingTable` - Contact organization only
- `DIDResolver` - High-level resolution API

### Open/Closed
- Abstract `VerificationMethod` supports new key types
- `ServiceEndpoint` extensible for new service types

### Interface Segregation
- `DHTNode` exposes minimal public API
- Internal RPC handlers are private

### Dependency Inversion
- `DIDResolver` depends on abstract `DHTNode` interface
- Storage layer is pluggable

---

## API Reference

### DIDDocument

| Method | Description |
|--------|-------------|
| `add_verification_method()` | Add key with purposes |
| `add_service()` | Add service endpoint |
| `get_verification_method()` | Get key by ID |
| `get_service()` | Get service by ID |
| `to_json()` / `from_json()` | Serialization |

### DIDManager

| Method | Description |
|--------|-------------|
| `create_did()` | Generate DID from keys |
| `create_document()` | Create full document |
| `update_service_endpoint()` | Update messaging URL |
| `save()` / `load()` | Persistence |

### DHTNode

| Method | Description |
|--------|-------------|
| `start()` / `stop()` | Lifecycle |
| `bootstrap()` | Join network |
| `store()` | Store value |
| `get()` | Retrieve value |
| `lookup_node()` | Find closest nodes |

### DIDResolver

| Method | Description |
|--------|-------------|
| `publish()` | Store DID document |
| `resolve()` | Lookup DID document |

---

## Security Considerations

| Threat | Mitigation |
|--------|------------|
| Sybil attack | PoW for node IDs (future) |
| Eclipse attack | Multiple bootstrap nodes |
| Stale data | TTL on stored values |
| Impersonation | DID bound to signing key |

---

## See Also

- [Python SDK](Python-SDK.md) - High-level client
- [Cryptography](Cryptography.md) - Key generation
- [Architecture](Architecture.md) - System design
