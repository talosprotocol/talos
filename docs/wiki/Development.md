# Development Guide

## Project Structure

```
talos-protocol/
├── src/
│   ├── core/                 # Core functionality
│   │   ├── blockchain.py     # Blockchain implementation
│   │   ├── crypto.py         # Cryptographic primitives
│   │   ├── session.py        # Double Ratchet sessions
│   │   ├── message.py        # Message protocol
│   │   └── validation/       # Block validation engine
│   │       ├── engine.py     # ValidationEngine
│   │       ├── layers.py     # Validation layers
│   │       ├── proofs.py     # Cryptographic proofs
│   │       └── report.py     # Audit reports
│   ├── network/              # Networking
│   │   ├── p2p.py            # P2P node
│   │   ├── peer.py           # Peer management
│   │   └── protocol.py       # Wire protocol
│   ├── mcp_bridge/           # MCP integration
│   │   ├── proxy.py          # MCP proxy
│   │   └── acl.py            # Access control
│   └── server/               # Registry server
├── talos/                    # Python SDK
│   ├── __init__.py           # Public API
│   ├── client.py             # TalosClient
│   ├── channel.py            # SecureChannel
│   ├── identity.py           # Identity management
│   ├── config.py             # Configuration
│   └── exceptions.py         # Error hierarchy
├── tests/                    # Test suite
├── scripts/                  # Demo scripts
├── docs/                     # Documentation
│   ├── wiki/                 # Wiki pages
│   └── ROADMAP_v2.md         # Development roadmap
└── config/                   # Configuration examples
```

---

## Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/nileshchakraborty/talos-protocol.git
cd talos-protocol

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

---

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ --cov=src --cov=talos --cov-report=html
open htmlcov/index.html
```

### Specific Modules
```bash
pytest tests/test_sdk.py -v           # SDK tests
pytest tests/test_session.py -v       # Double Ratchet
pytest tests/test_validation.py -v    # Validation engine
pytest tests/test_acl.py -v           # ACL tests
```

### Demo Scripts
```bash
python scripts/test_sdk_demo.py       # SDK demonstration
python scripts/test_api_demo.py       # Core API demo
python scripts/test_integration.py    # Integration tests
```

---

## Code Style

- **Type hints**: Use type annotations everywhere
- **Docstrings**: Google-style docstrings for public APIs
- **Formatting**: Black + isort (configured in pyproject.toml)
- **Linting**: Ruff for fast linting

```bash
# Format code
black src/ talos/ tests/
isort src/ talos/ tests/

# Lint
ruff check src/ talos/
```

---

## Adding New Features

### 1. Create Feature Branch
```bash
git checkout -b feature/my-feature
```

### 2. Write Tests First
```python
# tests/test_my_feature.py
def test_my_feature():
    # Write test before implementation
    pass
```

### 3. Implement Feature
```python
# src/core/my_feature.py
def my_feature():
    """Document the feature."""
    pass
```

### 4. Update Documentation
- Update relevant wiki page
- Add to CHANGELOG.md
- Update Getting-Started if user-facing

### 5. Submit PR
```bash
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

---

## Module Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `crypto.py` | Ed25519 signing, X25519 key exchange |
| `session.py` | Double Ratchet protocol |
| `blockchain.py` | Message storage and integrity |
| `validation/` | Block validation engine |
| `message.py` | Wire protocol messages |

### SDK Modules

| Module | Purpose |
|--------|---------|
| `client.py` | High-level client API |
| `channel.py` | Peer communication |
| `identity.py` | Key management |
| `config.py` | Configuration handling |

---

## Testing Patterns

### Unit Tests
```python
def test_encrypt_decrypt():
    """Test should be self-contained."""
    key = generate_key()
    plaintext = b"hello"
    ciphertext = encrypt(plaintext, key)
    assert decrypt(ciphertext, key) == plaintext
```

### Async Tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    client = TalosClient.create("test")
    await client.start()
    assert client.is_running
    await client.stop()
```

### Integration Tests
```python
async def test_two_client_communication():
    async with TalosClient.create("alice") as alice:
        async with TalosClient.create("bob") as bob:
            # Test end-to-end flow
            pass
```

---

## Debugging

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export TALOS_LOG_LEVEL=DEBUG
```

### Interactive Session
```python
from talos import TalosClient, TalosConfig

config = TalosConfig.development()
client = TalosClient.create("debug", config)
```

---

## Release Process

1. Update version in `talos/__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Tag release: `git tag v2.0.0-alpha.1`
5. Push tags: `git push --tags`

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Implement feature
5. Update docs
6. Submit PR

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.
