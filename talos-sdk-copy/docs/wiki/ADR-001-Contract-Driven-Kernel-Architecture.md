# ADR-001: Contract-Driven Kernel Architecture

## Status
Accepted

## Context
The Talos Security Protocol consists of multiple services (Gateway, Audit, Connectors) written in different languages (Python, TypeScript, Rust). Maintaining consistency in data structures, validation logic, and identifiers (Cursors, UUIDs) across these boundaries is critical for security and interoperability. Ad-hoc implementations in each service lead to "drift," subtle bugs, and security vulnerabilities when different services disagree on the validity of a cursor or hash.

## Decision
We will adopt a **"Contract-Driven Kernel"** architecture where a single repository acts as the Source of Truth for all shared logic.

1.  **Single Source of Truth**: The `talos-contracts` repository is the definitive source for:
    *   **Schemas**: JSON Schemas and OpenAPI definitions.
    *   **Data Types**: TypeScript interfaces and Python Pydantic models generated or manually aligned with schemas.
    *   **Validation Logic**: Critical helper functions like `deriveCursor`, `base64url` encoding (no padding), and `orderingCompare`.
    *   **Test Vectors**: Language-agnostic JSON files defining inputs and expected outputs for all critical operations.

2.  **Polyglot Distribution**: `talos-contracts` publishes artifacts for all supported ecosystems:
    *   **NPM**: `@talosprotocol/contracts` for TypeScript/JavaScript services (Dashboard, SDK-TS).
    *   **PyPI**: `talos-contracts` for Python services (Gateway, MCP Connector, Audit Service).
    *   **Tarballs**: Test vectors are published as artifacts for consumption by any language (e.g., Rust).

3.  **No Re-Implementation**: Consuming services (Dashboard, SDKs) **MUST NOT** re-implement core logic (e.g., manually concatenating strings to make a cursor). They MUST import helper functions from the contracts package.

4.  **Rust Kernel**: `talos-core-rs` serves as the high-performance kernel for cryptographic operations and complex validation, adhering strictly to the test vectors provided by `talos-contracts`.

## Consequences
### Positive
*   **Consistency**: A cursor derived in Python is byte-for-byte identical to one derived in TypeScript.
*   **Safety**: Fixes to validation logic (e.g., rejecting invalid Base64 padding) are deployed centrally.
*   **Interoperability**: Services can trust data shapes validated by the contracts library.

### Negative
*   **Coupling**: All services depend on `talos-contracts`. A breaking change in contracts requires version bumps across the ecosystem.
*   **Build Complexity**: The build pipeline must support multiple toolchains (Node.js, Python) to publish the contracts.
