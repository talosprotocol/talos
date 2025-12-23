# Architecture Overview

## High-Level Design

BMP follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │     CLI      │  │   Client     │  │   Future: GUI/Web    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                         Engine Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Transmission │  │    Media     │  │       Chunker        │  │
│  │    Engine    │  │   Handler    │  │    / Reassembler     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      MCP Bridge                          │  │
│  │         (ClientProxy / ServerProxy)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Protocol Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Message    │  │    Crypto    │  │    Serialization     │  │
│  │   Protocol   │  │  Primitives  │  │    (JSON/MsgPack)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Network Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   P2P Node   │  │   Registry   │  │   Connection Pool    │  │
│  │  (WebSocket) │  │    Client    │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Blockchain  │  │    Indexes   │  │    Chain Sync        │  │
│  │   (Blocks)   │  │  (Hash/Msg)  │  │   (Longest Chain)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Application Layer

**CLI (`src/client/cli.py`)**
- Click-based command interface
- Commands: `init`, `register`, `send`, `listen`, `peers`, `status`

**Client (`src/client/client.py`)**
- High-level API for application developers
- Manages wallet, connection, and engine lifecycle

### 2. Engine Layer

**TransmissionEngine (`src/engine/engine.py`)**
- Core message handling logic
- Encryption/decryption pipeline
- Callback management for received data

**Media Handler (`src/engine/media.py`)**
- File validation and MIME detection
- Transfer state management
- Progress tracking

**Chunker (`src/engine/chunker.py`)**
- Data segmentation for large payloads
- Chunk reassembly with ordering
- Hash verification

**MCP Bridge (`src/mcp_bridge/proxy.py`)**
- `MCPClientProxy`: Bridges local stdin -> BMP Network
- `MCPServerProxy`: Bridges BMP Network -> local subprocess
- Handles JSON-RPC tunneling and process management

### 3. Protocol Layer

**Message Protocol (`src/core/message.py`)**
- Message type definitions (TEXT, FILE, ACK, etc.)
- Payload structure with signatures
- Serialization formats

**Crypto (`src/core/crypto.py`)**
- Ed25519 signatures
- X25519 key exchange
- ChaCha20-Poly1305 encryption

### 4. Network Layer

**P2P Node (`src/network/p2p.py`)**
- WebSocket server/client
- Peer discovery and management
- Message routing

**Connection Pool (`src/network/pool.py`)**
- Connection reuse
- Health checking
- Automatic cleanup

### 5. Storage Layer

**Blockchain (`src/core/blockchain.py`)**
- Block creation and mining
- Chain validation
- Atomic persistence

**Indexes**
- O(1) lookup by hash, height, message ID
- Rebuilt on load

**Chain Sync (`src/core/sync.py`)**
- Peer status exchange
- Longest-chain rule
- Fork resolution

## Data Flow

### Sending a Message

```
User Input → Client → TransmissionEngine
                          │
                          ▼
                    ┌─────────────┐
                    │ Get Shared  │
                    │   Secret    │
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Encrypt    │
                    │  Content    │
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │    Sign     │
                    │  Payload    │
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │ Add to      │
                    │ Blockchain  │
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │ Send via    │
                    │   P2P       │
                    └─────────────┘
```

### Receiving a Message

```
P2P Layer → TransmissionEngine
                   │
                   ▼
             ┌─────────────┐
             │   Verify    │
             │  Signature  │
             └─────────────┘
                   │
                   ▼
             ┌─────────────┐
             │  Decrypt    │
             │  Content    │
             └─────────────┘
                   │
                   ▼
             ┌─────────────┐
             │ Record to   │
             │ Blockchain  │
             └─────────────┘
                   │
                   ▼
             ┌─────────────┐
             │   Invoke    │
             │  Callbacks  │
             └─────────────┘
                   │
                   ▼
             ┌─────────────┐
             │  Send ACK   │
             └─────────────┘
```

## File Structure

```
blockchain-messaging-protocol/
├── src/
│   ├── core/
│   │   ├── blockchain.py    # Blockchain + Block + MerkleProof
│   │   ├── crypto.py        # Cryptographic primitives
│   │   ├── message.py       # Message types and payload
│   │   └── sync.py          # Chain synchronization
│   ├── engine/
│   │   ├── engine.py        # TransmissionEngine
│   │   ├── chunker.py       # Data chunking
│   │   └── media.py         # File transfer
│   ├── network/
│   │   ├── p2p.py           # P2P networking
│   │   └── pool.py          # Connection pooling
│   ├── client/
│   │   ├── client.py        # High-level client
│   │   └── cli.py           # Command-line interface
│   └── server/
│       └── registry.py      # Registry server
├── tests/                   # 122 unit tests
├── benchmarks/              # Performance benchmarks
└── docs/                    # Documentation
```

## Design Decisions

### Why WebSocket over TCP?

- Bidirectional communication without polling
- Built-in framing (no manual packet handling)
- Easy upgrade path to WebRTC for real-time media

### Why Lightweight PoW?

- Prevents spam without expensive consensus
- Each node maintains local chain (no global agreement needed)
- Configurable difficulty for different use cases

### Why Ed25519 + X25519?

- Modern curves with 128-bit security
- Small keys (32 bytes) and signatures (64 bytes)
- Fast operations (~8k ops/s for sign+verify)

### Why ChaCha20-Poly1305?

- Same cipher as TLS 1.3
- 450 MB/s+ encryption speed
- Authenticated encryption (integrity + confidentiality)
