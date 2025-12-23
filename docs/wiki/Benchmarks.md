# Performance Benchmarks

This document details the performance characteristics of the Talos Protocol, specifically focusing on cryptographic primitives, message throughput, and MCP tunneling latency.

> **Hardware Context**: Tests performed on a MacBook Pro (M1 Pro, 16GB RAM).

## 1. Cryptographic Primitives

Talos uses `cryptography.hazmat` (OpenSSL backend) for high-performance primitives.

| Operation | Algorithm | Avg Time (ms) | Throughput (ops/sec) |
|-----------|-----------|---------------|----------------------|
| **Signing** | Ed25519 | 0.125 ms | ~7,900 |
| **Verification** | Ed25519 | 0.110 ms | ~9,000 |
| **Key Exchange** | X25519 | 0.194 ms | ~5,150 |
| **Encryption** | ChaCha20-Poly1305 | N/A | ~450 MB/s |
| **Block Hashing** | SHA-256 | 0.003 ms | ~378,000 |

*Table 1: Microbenchmarks of core security functions.*

## 2. Message Throughput (Chain Processing)

The internal lightweight blockchain processes blocks sequentially.

*   **Block Validation**: ~0.5ms per block
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
