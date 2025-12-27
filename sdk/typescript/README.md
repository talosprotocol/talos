# Talos Protocol TypeScript SDK

> **Implementation-Safe, Interop-Safe, V1 Canonical SDK**

This monorepo contains the TypeScript implementation of the Talos Protocol v1.

## Packages

| Package | Description | Version |
|---------|-------------|---------|
| [`@talos-protocol/sdk`](packages/sdk) | Core primitives (Crypto, Canonical JSON, Frames) | v0.1.0 |
| [`@talos-protocol/client`](packages/client) | High-level Identity Agent & Transport | v0.1.0 |

## Installation

```bash
npm install @talos-protocol/client @talos-protocol/sdk
```

## Usage

See [Wiki: SDK Integration](../../docs/wiki/SDK-Integration.md) for full documentation.

### Quick Example

```typescript
import { TalosAgent, InMemoryKeyProvider, signMcpRequest } from '@talos-protocol/client';

// Initialize
const agent = new TalosAgent("did:key:...", new InMemoryKeyProvider());

// Sign Request
const frame = await signMcpRequest(agent, request, "session-1", "corr-1", "tool", "method");
```

## Development

```bash
# Install dependencies
npm install

# Build all packages
npm run build

# Run tests (including vector compliance)
npm test

# Run E2E Example
npm run example:e2e -w @talos-protocol/client
```
