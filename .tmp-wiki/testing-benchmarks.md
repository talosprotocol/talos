# Performance Benchmarks

This document details the performance characteristics of the Talos Protocol, specifically focusing on cryptographic primitives, message throughput, and MCP tunneling latency.

> **Hardware Context**: Tests performed on a MacBook Pro (M4 Max, 36GB RAM).

## 1. Cryptographic Primitives

Talos uses `cryptography.hazmat` (OpenSSL backend) for high-performance primitives.

| Operation         | Algorithm          | Avg Time (ms) | Throughput (ops/sec) |
| ----------------- | ------------------ | ------------- | -------------------- |
| **Signing**       | Ed25519            | 0.1331 ms     | 7,515                |
| **Verification**  | Ed25519            | 0.1451 ms     | 6,893                |
| **Batch Verify**  | Ed25519 (Parallel) | 0.1616 ms     | 6,190                |
| **Encryption**    | ChaCha20-Poly1305  | 0.0035 ms     | 289,345              |
| **Block Hashing** | SHA-256            | 0.0030 ms     | ~380,000             |

_Table 1: Microbenchmarks of core security functions._

## 2. Message Throughput (Chain Processing)

The internal lightweight blockchain processes blocks sequentially, but validation is parallelized.

- **Block Validation (Standard)**: 0.2626 ms per block
- **Block Validation (Parallel)**: 0.3034 ms per block
- **Hash Calculation (SHA-256)**: < 0.01ms per message
- **End-to-End Latency** (Localhost): ~4-6ms

## 3. MCP Tunneling Performance

This section measures the overhead added by Talos when tunneling JSON-RPC traffic compared to a raw stdio pipe.

### Test Setup

- **Agent**: Mock MCP Client sending `ping` requests.
- **Tool**: Mock MCP Server echoing responses.
- **Transport**: Talos P2P Loopback (Client Proxy -> Server Proxy).

### Results

| Metric                    | Raw Stdio | Talos Tunnel | Overhead |
| ------------------------- | --------- | ------------ | -------- |
| **Round Trip Time (RTT)** | 0.2 ms    | 12.5 ms      | +12.3 ms |
| **Max Requests/Sec**      | ~5000     | ~80          | High     |

**Analysis**:
The overhead comes from:

1. **Encryption/Signing**: Every JSON-RPC frame is encrypted and signed.
2. **Network Framing**: `aiohttp`/WebSocket framing.
3. **Process Context Switching**: Agent -> ClientProxy -> Network -> ServerProxy -> Tool.

> **Note**: For MCP workloads (e.g., FileSystem reads, Database queries), a 12ms latency add-on is negligible compared to the tool's execution time (often 100ms+), making Talos highly viable for real-world agentic workflows.

## 4. File Transfer (Binaries)

| File Size | Transfer Time | Speed |
| :--- | :--- | :--- |
| 10 MB | 0.8s | 12.5 MB/s |
| 100 MB | 9.2s | 10.8 MB/s |
| 1 GB | 110s | 9.1 MB/s |

_Benchmarks ran over local loopback._

## 5. Storage Performance (LMDB)

Talos uses LMDB (Lightning Memory-Mapped Database) for high-performance storage.

| Operation | Latency (ms) | Throughput (ops/sec) |
| :--- | :--- | :--- |
| **Write (Batch)** | 0.0004 ms | 2,519,394 |
| **Read (Random)** | 0.0003 ms | 3,617,236 |

### Table 2: Storage Backend Benchmarks

## 6. Serialization Performance

All data models are Pydantic v2 `BaseModel`, optimized for speed.

| Operation | Latency (ms) | Throughput (ops/sec) |
| :--- | :--- | :--- |
| **Serialize (JSON)** | 0.0008 ms | 1,266,558 |
| **Deserialize (JSON)** | 0.0009 ms | 1,091,480 |

## 7. Automated Benchmarks

<!-- PERF-AUTO:BEGIN -->

## Python SDK Benchmarks

### Latest Results (2026-01-30)

**Hardware:** Apple M4 Max, 14 cores, 36GB RAM
**Environment:** Local, Power: normal, Thermal: unknown
> ⚠️ **Note:** Results marked as non-baseline (battery or thermal throttling detected)
**Git SHA:** `HEAD`

| Operation | Median (ms) | p95 (ms) | Throughput (ops/sec) |
| :--- | :--- | :--- | :--- |
| RatchetFrameCrypto roundtrip | 1.6710 | 1.6710 | 599 |
| RatchetFrameCrypto.encrypt() | 0.0270 | 0.0270 | 37,127 |
| SHA256 digest | 0.0000 | 0.0000 | 2,667,358 |
| Session create pair (X3DH) | 1.5600 | 1.5600 | 641 |
| Session roundtrip(35B) | 1.5680 | 1.5680 | 638 |
| Session.encrypt(10KB) | 0.0570 | 0.0570 | 17,571 |
| Session.encrypt(35B) | 0.0220 | 0.0220 | 44,898 |
| Session.from_dict() | 0.0040 | 0.0040 | 284,484 |
| Session.to_dict() | 0.0030 | 0.0030 | 372,524 |
| Wallet.from_seed() | 0.0750 | 0.0750 | 13,291 |
| Wallet.generate() | 0.2130 | 0.2130 | 4,704 |
| Wallet.sign(10KB) | 0.1040 | 0.1040 | 9,618 |
| Wallet.sign(64B) | 0.0720 | 0.0720 | 13,844 |
| Wallet.to_did() | 0.0040 | 0.0040 | 248,103 |
| Wallet.verify() | 0.1530 | 0.1530 | 6,542 |
| canonical_json_bytes() | 0.0040 | 0.0040 | 272,195 |
| json.dumps(session) | 0.0060 | 0.0060 | 167,268 |
| json.loads(session) | 0.0030 | 0.0030 | 386,543 |

## Go SDK Benchmarks

### Latest Results (2026-01-24)

**Hardware:** Apple M4 Max, 14 cores, 36GB RAM
**Environment:** Local, Power: normal, Thermal: unknown
> ⚠️ **Note:** Results marked as non-baseline (battery or thermal throttling detected)
**Git SHA:** `0f158955`

| Operation | Median (ms) | p95 (ms) | Throughput (ops/sec) |
| :--- | :--- | :--- | :--- |
| BenchmarkCanonicalJSON | 0.0010 | 0.0010 | 957,854 |
| BenchmarkCryptoSign10KB | 0.0247 | 0.0247 | 40,445 |
| BenchmarkCryptoSign64B | 0.0134 | 0.0134 | 74,878 |
| BenchmarkCryptoVerify | 0.0290 | 0.0290 | 34,435 |
| BenchmarkSHA256 | 0.0000 | 0.0000 | 24,055,809 |
| BenchmarkWalletFromSeed | 0.0106 | 0.0106 | 94,482 |
| BenchmarkWalletGenerate | 0.0110 | 0.0110 | 91,241 |

<!-- PERF-AUTO:END -->

---

> **Run benchmarks**: `./scripts/perf/run_all.sh`
