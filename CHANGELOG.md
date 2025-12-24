# Changelog

All notable changes to the Talos Protocol project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.5] - 2025-12-24

### Added
- **MCP CLI Integration**: Native `talos mcp-connect` and `talos mcp-serve` commands.
- **MCP Examples**: `examples/mcp_connect_demo.py` and `examples/mcp_serve_demo.py`.
- **Comprehensive Testing**:
  - `tests/test_sync_coverage.py`: 83% coverage for Chain Synchronizer.
  - `tests/test_cli_coverage.py`: 82% coverage for CLI.
  - `tests/test_p2p_coverage.py`: 77% coverage for P2P Networking.
  - `tests/test_engine_coverage.py`: 47% coverage for Transmission Engine.

### Changed
- **Pydantic Refactor**: Migration of core data structures (`ChainStatus`, `MediaInfo`) to Pydantic v2.
- **Code Coverage**: Improved overall project coverage from 64% to 79%.
- **Versioning**: Synchronized project version to 2.0.5 across `pyproject.toml` and `talos/__init__.py`.

### Fixed
- Resolved `RuntimeWarning`s in async tests.
- Fixed `MediaInfo` validation schemas.

## [2.0.0-alpha.1] - 2025-12-24

### Added

#### Block Validation Engine (Phase 1)
- **`src/core/validation/`** - Complete multi-layer validation package
  - `engine.py` - Main `ValidationEngine` class with async validation
  - `layers.py` - Structural, Cryptographic, Consensus, Semantic validators
  - `proofs.py` - Cryptographic proof verification (hash, Merkle, PoW)
  - `report.py` - Audit report generation with JSON/HTML export
- **19 tests** covering all validation scenarios

#### Double Ratchet Protocol (Phase 2)
- **`src/core/session.py`** - Signal Double Ratchet implementation
  - X3DH (Extended Triple Diffie-Hellman) handshake
  - Symmetric ratchet with per-message keys
  - DH ratchet for forward secrecy and break-in recovery
  - Session persistence to disk
  - `SessionManager` for multi-peer session handling
- **16 tests** covering encryption, decryption, and ratcheting

#### Fine-Grained ACLs (Phase 3)
- **`src/mcp_bridge/acl.py`** - Access Control List manager
  - Glob pattern matching for tools and resources
  - Per-peer rate limiting with configurable windows
  - Audit logging for all access decisions
  - Integration with `proxy.py` for MCP request filtering
- **`config/permissions.example.yaml`** - Sample ACL configuration
- **16 tests** covering ACL enforcement and rate limiting

#### Python SDK (Phase 4)
- **`talos/`** - Complete Python SDK package
  - `__init__.py` - Clean public API exports
  - `client.py` - `TalosClient` high-level client
  - `channel.py` - `SecureChannel` async context manager
  - `identity.py` - Key management and prekey bundles
  - `config.py` - Configuration with environment overrides
  - `exceptions.py` - Error hierarchy with codes
- **19 tests** covering client lifecycle and sessions

#### Test Scripts
- **`scripts/test_sdk_demo.py`** - SDK functionality demonstration
- **`scripts/test_api_demo.py`** - Core API demonstration
- **`scripts/test_integration.py`** - End-to-end integration tests

#### Wiki Documentation
- **`docs/wiki/Double-Ratchet.md`** - Forward secrecy protocol guide
- **`docs/wiki/Python-SDK.md`** - SDK usage documentation
- **`docs/wiki/Access-Control.md`** - ACL configuration guide
- **`docs/wiki/Validation-Engine.md`** - Block validation documentation

### Changed
- Updated `src/network/p2p.py` to use modern websockets API
- Updated `docs/wiki/Testing.md` with accurate test counts (196 total)
- Updated `docs/wiki/Home.md` with new feature links

### Fixed
- Fixed websockets deprecation warnings
- Fixed `generate_audit_report` interface for proper usage

### Security
- **Perfect Forward Secrecy**: Every message encrypted with unique key
- **Break-in Recovery**: Sessions heal after key compromise
- **Rate Limiting**: Prevent DoS through configurable limits
- **Audit Logging**: Complete trail of all security decisions

---

## [1.0.0] - Initial Release

### Features
- Blockchain-based message integrity
- Ed25519 signing and X25519 key exchange
- ChaCha20-Poly1305 authenticated encryption
- P2P networking with WebSockets
- MCP bridge for AI tool access
- CLI client for messaging
- File transfer with chunked streaming
