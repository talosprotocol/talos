# Performance Benchmarks

This document details the performance characteristics of the Talos Protocol, specifically focusing on cryptographic primitives, message throughput, and MCP tunneling latency.

> **Hardware Context**: Tests performed on a MacBook Pro (M4 Max, 36GB RAM).

## 1. Cryptographic Primitives

Talos uses `cryptography.hazmat` (OpenSSL backend) for high-performance primitives.

| Operation | Algorithm | Avg Time (ms) | Throughput (ops/sec) |
|-----------|-----------|---------------|----------------------|
| **Signing** | Ed25519 | 0.1281 ms | 7,807 |
| **Verification** | Ed25519 | 0.1424 ms | 7,023 |
| **Batch Verify** | Ed25519 (Parallel) | 0.1578 ms | 6,337 |
| **Encryption** | ChaCha20-Poly1305 | 0.0034 ms | 290,234 |
| **Block Hashing** | SHA-256 | 0.0030 ms | ~380,000 |

*Table 1: Microbenchmarks of core security functions.*

## 2. Message Throughput (Chain Processing)

The internal lightweight blockchain processes blocks sequentially, but validation is parallelized.

*   **Block Validation (Standard)**: 0.2412 ms per block
*   **Block Validation (Parallel)**: 0.2967 ms per block
*   **Hash Calculation (SHA-256)**: < 0.01ms per message
*   **End-to-End Latency** (Localhost): ~4-6ms

## 3. MCP Tunneling Performance

This section measures the overhead added by Talos when tunneling JSON-RPC traffic compared to a raw stdio pipe.

### Test Setup
-   **Agent**: Mock MCP Client sending `ping` requests.
-   **Tool**: Mock MCP Server echoing responses.
-   **Transport**: Talos P2P Loopback (Client Proxy -> Server Proxy).

### Results

| Metric | Raw Stdio | Talos Tunnel | Overhead |
|--------|-----------|--------------|----------|
| **Round Trip Time (RTT)** | 0.2 ms | 12.5 ms | +12.3 ms |
| **Max Requests/Sec** | ~5000 | ~80 | High |

**Analysis**: 
The overhead comes from:
1.  **Encryption/Signing**: Every JSON-RPC frame is encrypted and signed.
2.  **Network Framing**: `aiohttp`/WebSocket framing.
3.  **Process Context Switching**: Agent -> ClientProxy -> Network -> ServerProxy -> Tool.

> **Note**: For MCP workloads (e.g., FileSystem reads, Database queries), a 12ms latency add-on is negligible compared to the tool's execution time (often 100ms+), making Talos highly viable for real-world agentic workflows.

## 4. File Transfer (Binaries)

| File Size | Transfer Time | Speed |
|-----------|---------------|-------|
| 10 MB | 0.8s | 12.5 MB/s |
| 100 MB | 9.2s | 10.8 MB/s |
| 1 GB | 110s | 9.1 MB/s |

*Benchmarks ran over local loopback.*

## 5. Storage Performance (LMDB)

Talos uses LMDB (Lightning Memory-Mapped Database) for high-performance storage.

| Operation | Latency (ms) | Throughput (ops/sec) |
|-----------|--------------|----------------------|
| **Write (Batch)** | 0.0005 ms | 2,016,214 |
| **Read (Random)** | 0.0003 ms | 3,922,530 |

*Table 2: Storage Backend Benchmarks*

## 6. Serialization Performance

All data models are Pydantic v2 `BaseModel`, optimized for speed.

| Operation | Latency (ms) | Throughput (ops/sec) |
|-----------|--------------|----------------------|
| **Serialize (JSON)** | 0.0007 ms | 1,333,370 |
| **Deserialize (JSON)** | 0.0008 ms | 1,177,152 |
