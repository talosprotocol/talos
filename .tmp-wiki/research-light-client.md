# Light Client Mode

> **Efficient blockchain sync with ~99% storage reduction**

## Overview

Light clients store only block headers instead of full block data, reducing storage requirements by approximately 99%. They use SPV (Simplified Payment Verification) proofs to verify that data exists in blocks without needing the full data.

---

## Quick Start

```python
from src.core.light import LightBlockchain, BlockHeader, SPVProof

# Create light client
light = LightBlockchain(difficulty=2)

# Sync headers from full node
headers = await full_node.get_headers(start=0)
light.add_headers(headers)

# Verify data exists using SPV proof
proof = await full_node.get_merkle_proof(data_hash)
if light.verify_spv_proof(proof):
    print("Data verified!")
```

---

## Components

### BlockHeader

Lightweight block metadata (~200 bytes vs ~1MB full block):

```python
from src.core.light import BlockHeader

header = BlockHeader(
    index=0,
    timestamp=time.time(),
    previous_hash="...",
    merkle_root="...",
    nonce=12345,
    hash="00abc...",
    difficulty=2,
)

# Validate PoW
assert header.validate_pow()

# Create from full block
header = BlockHeader.from_block(block, difficulty=2)
```

### SPVProof

Merkle proof that data exists in a block:

```python
from src.core.light import SPVProof

proof = SPVProof(
    data_hash="abc123...",
    block_hash="def456...",
    block_height=100,
    merkle_root="ghi789...",
    merkle_path=[
        ("sibling1", "left"),
        ("sibling2", "right"),
    ],
)

# Verify locally
if proof.verify():
    print("Data exists in block!")
```

### LightBlockchain

Header-only blockchain with SPV support:

```python
from src.core.light import LightBlockchain
from src.core.blockchain import Blockchain

# Create from full blockchain
full_chain = Blockchain(difficulty=2)
light = LightBlockchain.from_blockchain(full_chain)

# Or sync incrementally
light = LightBlockchain(difficulty=2)
light.add_headers(headers_from_peer)

# Verify proofs
light.verify_spv_proof(proof)

# Check if data verified
light.has_verified_data(data_hash)
```

---

## Sync Protocol

### Request Headers

```python
request = light.get_sync_request(batch_size=100)
# {"type": "GET_HEADERS", "start_height": 100, "count": 100}
```

### Request Proof

```python
request = light.get_proof_request(data_hash)
# {"type": "GET_MERKLE_PROOF", "data_hash": "..."}
```

---

## Storage Comparison

| Type | Storage per Block |
|------|-------------------|
| Full Node | ~1 MB (with transactions) |
| Light Client | ~200 bytes (header only) |
| **Reduction** | **~99.98%** |

---

## Persistence

```python
# Save headers
light.save(Path("~/.talos/light.json"))

# Load headers
light.load(Path("~/.talos/light.json"))
```

---

## Statistics

```python
stats = light.get_stats()
# {
#     "height": 1000,
#     "headers_count": 1001,
#     "header_storage_bytes": 200200,
#     "proofs_verified": 50,
#     "proofs_failed": 2,
#     "cached_proofs": 48,
#     "difficulty": 2,
# }
```

---

## Security Considerations

| Aspect | Full Node | Light Client |
|--------|-----------|--------------|
| Validates transactions | ✅ | ❌ |
| Validates block structure | ✅ | ✅ |
| Validates PoW | ✅ | ✅ |
| Validates SPV proofs | N/A | ✅ |
| Storage requirement | High | Low |
| Bootstrap time | Long | Fast |

> [!NOTE]
> Light clients trust that full nodes provide valid Merkle proofs. They cannot detect invalid transactions within blocks.

---

## API Reference

### BlockHeader

| Method | Description |
|--------|-------------|
| `from_block(block)` | Create from full block |
| `validate_pow()` | Verify proof-of-work |
| `to_dict()` / `from_dict()` | Serialization |

### SPVProof

| Method | Description |
|--------|-------------|
| `verify()` | Verify Merkle proof |
| `to_dict()` / `from_dict()` | Serialization |

### LightBlockchain

| Method | Description |
|--------|-------------|
| `add_header(header)` | Add single header |
| `add_headers(headers)` | Add header batch |
| `get_header(height)` | Get by height |
| `get_header_by_hash(hash)` | Get by hash |
| `verify_spv_proof(proof)` | Verify SPV proof |
| `has_verified_data(hash)` | Check cache |
| `validate_chain()` | Validate headers |
| `save()` / `load()` | Persistence |
| `get_stats()` | Statistics |

---

## See Also

- [Blockchain Design](blockchain) - Full node implementation
- [Validation Engine](security-validation-engine) - Block validation
- [Python SDK](sdk-python-sdk) - High-level API
