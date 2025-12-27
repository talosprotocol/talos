# SDK & Client Integration (Phase 4.1)

The Talos TypeScript SDK provides secure, canonicalized implementation of the Talos Protocol v1 for JavaScript/TypeScript environments (Node.js & Browser). It allows agents to generate signed "Envelopes" (MCP Frames) that are cryptographically verified by the Talos Blockchain Gateway/Proxy.

## Installation

```bash
npm install @talos-protocol/client @talos-protocol/sdk
```

## Quick Start (Client)

The Client package simplifies secure communication by handling Identity (DIDs), Key Management, and Frame Signing.

```typescript
import { TalosAgent, InMemoryKeyProvider, signMcpRequest } from '@talos-protocol/client';

// 1. Initialize Agent
const agent = new TalosAgent(
    "did:key:z6Mk...", 
    new InMemoryKeyProvider(seed)
);

// 2. Prepare MCP Request (JSON-RPC)
const request = {
    jsonrpc: "2.0",
    id: 1,
    method: "files/read",
    params: { path: "/etc/hosts" }
};

// 3. Sign & Wrap in Envelope
const frame = await signMcpRequest(
    agent,
    request,
    "session-123", // session_id
    "corr-456",    // correlation_id
    "files",       // tool
    "read"         // method
);

// 4. Send `frame` to Talos Gateway (or Peer)
console.log(JSON.stringify(frame));
```

## Core SDK (`@talos-protocol/sdk`)

For advanced usage or building custom transports, the Core SDK provides pure functional primitives.

### Features
*   **Canonicalization**: RFC 8785 strict implementation (no floats, no duplicates).
*   **Crypto**: Ed25519 signing and SHA-256 hashing (WebCrypto optimized).
*   **Strict Frames**: Validates and rejects unknown fields in `MCP_MESSAGE` / `MCP_RESPONSE`.

### Example: Manual Signing

```typescript
import { canonicalize, sign, fromSeed } from '@talos-protocol/sdk';

const kp = fromSeed(seed);
const payload = { ... };
const canonicalBytes = canonicalize(payload);
const signature = await sign(canonicalBytes, kp.privateKey);
```

## Verification

The SDK includes a strict verification suite ensuring byte-level compatibility with the Python Core.

*   **Test Vectors**: Validated against `test_vectors/` (Positive, Negative, Replay).
*   **Cross-Language**: Python verification scripts confirm SDK signatures are valid.

## Usage in Browser

The SDK is `sideEffects: false` and tree-shakable. It relies on `Global.crypto` (WebCrypto API) which is available in all modern browsers and Node.js 19+.

## Reference

*   [NPM: @talos-protocol/sdk](https://www.npmjs.com/package/@talos-protocol/sdk)
*   [NPM: @talos-protocol/client](https://www.npmjs.com/package/@talos-protocol/client)
