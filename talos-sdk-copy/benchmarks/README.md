# Talos SDK Benchmarks

Run benchmarks: `PYTHONPATH=src python benchmarks/bench_crypto.py`

## Latest Results (2026-01-16)

### Wallet Operations

| Operation          | Latency  | Throughput      |
| ------------------ | -------- | --------------- |
| Wallet.generate()  | 0.095 ms | 10,563 ops/sec  |
| Wallet.from_seed() | 0.066 ms | 15,089 ops/sec  |
| Wallet.sign(64B)   | 0.065 ms | 15,442 ops/sec  |
| Wallet.sign(10KB)  | 0.076 ms | 13,216 ops/sec  |
| Wallet.verify()    | 0.145 ms | 6,877 ops/sec   |
| Wallet.to_did()    | 0.004 ms | 269,101 ops/sec |

### Double Ratchet Operations

| Operation                  | Latency  | Throughput     |
| -------------------------- | -------- | -------------- |
| Session create pair (X3DH) | 1.494 ms | 669 ops/sec    |
| Session.encrypt(35B)       | 0.020 ms | 50,729 ops/sec |
| Session.encrypt(10KB)      | 0.057 ms | 17,456 ops/sec |
| Session roundtrip(35B)     | 1.496 ms | 669 ops/sec    |

### RatchetFrameCrypto Operations

| Operation                    | Latency  | Throughput     |
| ---------------------------- | -------- | -------------- |
| RatchetFrameCrypto.encrypt() | 0.027 ms | 36,619 ops/sec |
| RatchetFrameCrypto roundtrip | 1.517 ms | 659 ops/sec    |

### Canonical JSON & Digest Operations

| Operation              | Latency  | Throughput        |
| ---------------------- | -------- | ----------------- |
| canonical_json_bytes() | 0.003 ms | 296,864 ops/sec   |
| SHA256 digest          | 0.000 ms | 2,616,860 ops/sec |

### Session Serialization

| Operation           | Latency  | Throughput      |
| ------------------- | -------- | --------------- |
| Session.to_dict()   | 0.003 ms | 391,526 ops/sec |
| json.dumps(session) | 0.006 ms | 172,637 ops/sec |
| json.loads(session) | 0.002 ms | 410,385 ops/sec |
| Session.from_dict() | 0.003 ms | 301,073 ops/sec |

## Summary by Category

| Category  | Avg ops/sec |
| --------- | ----------- |
| Wallet    | 55,048      |
| Ratchet   | 17,381      |
| Frame     | 18,639      |
| Canonical | 1,456,862   |
| Serialize | 318,905     |

## Environment

- Python: 3.13
- Platform: macOS (Apple Silicon)
- cryptography: ChaCha20-Poly1305
- Ed25519: native implementation
