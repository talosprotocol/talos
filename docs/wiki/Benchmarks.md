# Performance Benchmarks

This document details the performance characteristics of the Talos Protocol, specifically focusing on cryptographic primitives, message throughput, and MCP tunneling latency.

> **Hardware Context**: Tests performed on a MacBook Pro (M1 Pro, 16GB RAM).

7: ## 1. Cryptographic Primitives
8: 
9: Talos uses `cryptography.hazmat` (OpenSSL backend) for high-performance primitives.
10: 
11: | Operation | Algorithm | Avg Time (ms) | Throughput (ops/sec) |
12: |-----------|-----------|---------------|----------------------|
13: | **Signing** | Ed25519 | 0.127 ms | ~7,870 |
14: | **Verification** | Ed25519 | 0.141 ms | ~7,100 |
15: | **Batch Verify** | Ed25519 (Parallel) | 0.158 ms | ~6,300 |
16: | **Encryption** | ChaCha20-Poly1305 | 0.003 ms | ~300,000 |
17: | **Block Hashing** | SHA-256 | 0.003 ms | ~380,000 |
18: 
19: *Table 1: Microbenchmarks of core security functions.*
20: 
21: ## 2. Message Throughput (Chain Processing)
22: 
23: The internal lightweight blockchain processes blocks sequentially, but validation is parallelized.
24: 
25: *   **Block Validation (Standard)**: ~0.25ms per block
26: *   **Block Validation (Parallel)**: ~0.30ms per block
27: *   **Hash Calculation (SHA-256)**: < 0.01ms per message
28: *   **End-to-End Latency** (Localhost): ~4-6ms
29: 
30: ## 3. MCP Tunneling Performance
31: 
32: This section measures the overhead added by Talos when tunneling JSON-RPC traffic compared to a raw stdio pipe.
33: 
34: ### Test Setup
35: -   **Agent**: Mock MCP Client sending `ping` requests.
36: -   **Tool**: Mock MCP Server echoing responses.
37: -   **Transport**: Talos P2P Loopback (Client Proxy -> Server Proxy).
38: 
39: ### Results
40: 
41: | Metric | Raw Stdio | Talos Tunnel | Overhead |
42: |--------|-----------|--------------|----------|
43: | **Round Trip Time (RTT)** | 0.2 ms | 12.5 ms | +12.3 ms |
44: | **Max Requests/Sec** | ~5000 | ~80 | High |
45: 
46: **Analysis**: 
47: The overhead comes from:
48: 1.  **Encryption/Signing**: Every JSON-RPC frame is encrypted and signed.
49: 2.  **Network Framing**: `aiohttp`/WebSocket framing.
50: 3.  **Process Context Switching**: Agent -> ClientProxy -> Network -> ServerProxy -> Tool.
51: 
52: > **Note**: For MCP workloads (e.g., FileSystem reads, Database queries), a 12ms latency add-on is negligible compared to the tool's execution time (often 100ms+), making Talos highly viable for real-world agentic workflows.
53: 
54: ## 4. File Transfer (Binaries)
55: 
56: | File Size | Transfer Time | Speed |
57: |-----------|---------------|-------|
58: | 10 MB | 0.8s | 12.5 MB/s |
59: | 100 MB | 9.2s | 10.8 MB/s |
60: | 1 GB | 110s | 9.1 MB/s |
61: 
62: *Benchmarks ran over local loopback.*
63: 
64: ## 5. Storage Performance (LMDB)
65: 
66: Talos uses LMDB (Lightning Memory-Mapped Database) for high-performance storage.
67: 
68: | Operation | Latency (ms) | Throughput (ops/sec) |
69: |-----------|--------------|----------------------|
70: | **Write (Batch)** | 0.0005 ms | ~2,200,000 |
71: | **Read (Random)** | 0.0003 ms | ~3,400,000 |
72: 
73: *Table 2: Storage Backend Benchmarks*
74: 
75: ## 6. Serialization Performance
76: 
77: All data models are Pydantic v2 `BaseModel`, optimized for speed.
78: 
79: | Operation | Latency (ms) | Throughput (ops/sec) |
80: |-----------|--------------|----------------------|
81: | **Serialize** | 0.0007 ms | ~1,390,000 |
82: | **Deserialize** | 0.0009 ms | ~1,150,000 |
