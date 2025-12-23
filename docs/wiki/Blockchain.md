# Blockchain Design

## Overview

BMP uses a local blockchain for:
- **Message integrity**: Cryptographic proof that messages weren't altered
- **Non-repudiation**: Signed records that can't be denied
- **Audit trail**: Complete history of communications
- **Ordering**: Guaranteed message sequence

Unlike global blockchains (Bitcoin, Ethereum), each node maintains its own chain without requiring global consensus.

## Block Structure

```python
@dataclass
class Block:
    index: int           # Block height (0 = genesis)
    timestamp: float     # Unix timestamp
    data: dict           # {"messages": [...]}
    previous_hash: str   # Link to previous block
    nonce: int           # PoW solution
    hash: str            # SHA-256 of block
    merkle_root: str     # Merkle root of messages
```

### Visualization

```
┌─────────────────────────────────────────────────────┐
│                    Block #42                         │
├─────────────────────────────────────────────────────┤
│ Previous Hash: 0000abc123...                        │
│ Timestamp: 1703289600.123                           │
│ Nonce: 12847                                        │
│ Merkle Root: def456...                              │
├─────────────────────────────────────────────────────┤
│ Messages:                                           │
│   [0] {id: "msg_1", type: "TEXT", ...}             │
│   [1] {id: "msg_2", type: "FILE", ...}             │
│   [2] {id: "msg_3", type: "ACK", ...}              │
├─────────────────────────────────────────────────────┤
│ Hash: 00009f8e7d...                                 │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│                    Block #43                         │
├─────────────────────────────────────────────────────┤
│ Previous Hash: 00009f8e7d...                        │
│ ...                                                 │
```

## Proof of Work

### How It Works

1. Block data is serialized to JSON
2. SHA-256 hash is computed
3. If hash doesn't start with `difficulty` zeros, increment nonce
4. Repeat until valid hash found

```python
def mine(self, difficulty: int = 2) -> None:
    target = "0" * difficulty
    while not self.hash.startswith(target):
        self.nonce += 1
        self.hash = self.calculate_hash()
```

### Difficulty Levels

| Difficulty | Expected Hashes | Avg Time |
|------------|-----------------|----------|
| 1 | ~16 | 0.15ms |
| 2 | ~256 | 1.8ms |
| 3 | ~4,096 | ~30ms |
| 4 | ~65,536 | ~500ms |

**Recommendation**: Use difficulty=2 for production (fast enough for messaging, hard enough to prevent spam).

## Indexing

### O(1) Lookups

Three indexes are maintained:

```python
# Hash → Block (for chain verification)
_block_index: dict[str, Block] = {}

# Height → Block (for sync requests)
_height_index: dict[int, Block] = {}

# Message ID → Height (for proof generation)
_message_index: dict[str, int] = {}
```

### Performance

| Operation | Time | Complexity |
|-----------|------|------------|
| Lookup by hash | <0.001ms | O(1) |
| Lookup by height | <0.001ms | O(1) |
| Find message block | <0.001ms | O(1) |
| Full chain scan | ~0.06ms/block | O(n) |

## Merkle Proofs

### Purpose

Prove a message exists in a block without sharing the entire block.

### Structure

```
                    Root Hash
                   /         \
              Hash01          Hash23
             /     \         /     \
          Hash0   Hash1   Hash2   Hash3
            │       │       │       │
          Msg0    Msg1    Msg2    Msg3
```

### Proof Example

To prove `Msg1` exists:

```python
proof = {
    "block_hash": "abc123...",
    "block_height": 42,
    "data_hash": hash(Msg1),
    "merkle_root": "root...",
    "proof_path": [
        ("Hash0", "left"),     # Sibling of Msg1
        ("Hash23", "right")    # Sibling of Hash01
    ]
}
```

### Verification

```python
current = hash(Msg1)
for sibling, position in proof_path:
    if position == "left":
        current = hash(sibling + current)
    else:
        current = hash(current + sibling)

assert current == merkle_root  # Proof is valid!
```

## Chain Synchronization

### When to Sync

Sync when a peer has:
1. Same genesis block (same network)
2. More total work (longer valid chain)

### Sync Protocol

```
Node A                                Node B
  │                                     │
  │─── CHAIN_STATUS ───────────────────▶│
  │    (height=100, work=1024)          │
  │                                     │
  │◀─── CHAIN_STATUS ──────────────────│
  │    (height=150, work=1536)          │
  │                                     │
  │  [A sees B has more work, starts sync]
  │                                     │
  │─── CHAIN_REQUEST ──────────────────▶│
  │    (start=101, end=150)             │
  │                                     │
  │◀─── CHAIN_RESPONSE ─────────────────│
  │    (blocks 101-150)                 │
  │                                     │
  │  [A validates and replaces chain]   │
```

### Fork Resolution

```python
def should_accept_chain(self, remote: ChainStatus) -> bool:
    # Must have same genesis
    if remote.genesis_hash != self.genesis_hash:
        return False
    
    # Must have more total work
    if remote.total_work <= self.total_work:
        return False
    
    return True
```

## Persistence

### Atomic Saves

```python
def save(self, path: Path) -> None:
    # Write to temp file first
    fd, tmp_path = tempfile.mkstemp(...)
    with os.fdopen(fd, 'w') as f:
        json.dump(self.to_dict(), f)
    
    # Atomic rename (POSIX guarantees atomicity)
    os.replace(tmp_path, path)
```

**Benefits**:
- Crash-safe: interrupted writes don't corrupt data
- No partial files: either old or new, never in-between

### File Format

```json
{
  "version": 2,
  "difficulty": 2,
  "chain": [
    {
      "index": 0,
      "timestamp": 1703289600.0,
      "data": {"message": "Genesis Block"},
      "previous_hash": "0000...0000",
      "nonce": 847,
      "hash": "00ab3f...",
      "merkle_root": "e3b0c4..."
    }
  ],
  "pending_data": []
}
```

## Size Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| Max Block Size | 1 MB | Prevent bloat |
| Max Item Size | 100 KB | Prevent oversized messages |
| Max Mempool | 10,000 items | Bound memory usage |

### Block Splitting

If pending data exceeds block size, it's automatically split:

```python
for item in self.pending_data:
    if current_size + item_size <= max_block_size:
        block_data.append(item)
    else:
        remaining.append(item)  # Mine in next block
```
