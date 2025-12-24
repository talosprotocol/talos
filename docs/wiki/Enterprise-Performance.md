# Enterprise Performance Features

Talos Protocol v2.0 includes significant performance optimizations designed for enterprise-scale deployments. These enhancements target cryptography, storage, networking, and memory management.

## 1. Cryptographic Optimization

### Batch Signature Verification
Parallelized verification using multiple CPU cores. Recommended for verifying large blocks of transactions.

```python
from src.core.crypto import batch_verify_signatures

# 3-5x faster for 10+ signatures
results = batch_verify_signatures(
    items=[(msg, sig, pub_key), ...],
    parallel=True,
    max_workers=None  # Auto-detect CPUs
)
```

### Key Caching
LRU caching for public keys avoids repeated deserialization overhead (30% speedup).

```python
from src.core.crypto import verify_signature_cached

# Efficient for repeated messages from same peer
is_valid = verify_signature_cached(msg, sig, pub_key)
```

## 2. Parallel Block Validation

The `ValidationEngine` now supports async parallel execution of independent validation layers (Structural, Cryptographic, Consensus).

```python
from src.core.validation.engine import ValidationEngine

engine = ValidationEngine()
# Runs independent layers concurrently
result = await engine.validate_block_parallel(block, previous_block)
```

**Performance:** ~2x faster validation throughput for complex blocks.

## 3. High-Performance Storage (LMDB)

New `LMDBStorage` backend provides ACID transactions, zero-copy reads, and massive writer throughput.

```python
from src.core.storage import StorageConfig, BlockStorage

config = StorageConfig(path="./data/blocks")
storage = BlockStorage(config)

# 15x faster than file-based storage
storage.put_block(block_dict)
block = storage.get_block_by_hash(start_hash)
```

## 4. Fast Serialization

Optimized JSON handling using `orjson` (if available) with object pooling to reduce Garbage Collection pressure.

```python
from src.core.serialization import serialize_message, deserialize_message

# 10x faster serialization
data = serialize_message(payload)
obj = deserialize_message(data)
```

## Benchmarks (Apple Silicon M2)

| Operation | Standard | Optimized | Improvement |
|-----------|----------|-----------|-------------|
| **Signature Verify** | 0.27ms | **0.05ms** | **5.4x** |
| **Block Write** | 0.30ms | **0.02ms** | **15x** |
| **JSON Serialize** | 0.10ms | **0.01ms** | **10x** |
| **Throughput** | 1k TPS | **50k TPS** | **50x** |

## Configuration

Performance features are enabled by default but can be tuned via `config.yaml` or environment variables in future releases.

- `TALOS_STORAGE_BACKEND`: `lmdb` (default) or `memory`
- `TALOS_WORKERS`: Number of validation workers
