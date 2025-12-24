# Getting Started

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/nileshchakraborty/talos-protocol.git
cd talos-protocol

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .
```

### Dependencies

```
cryptography>=41.0.0    # Cryptographic primitives
websockets>=12.0        # WebSocket support
click>=8.1.0            # CLI framework
msgpack>=1.0.0          # Binary serialization
pyyaml>=6.0             # Configuration files
```

---

## Quick Start with Python SDK

The recommended way to use Talos is through the Python SDK.

### 1. Create a Client

```python
from talos import TalosClient

# Create client (auto-generates or loads identity)
client = TalosClient.create("my-agent")
```

### 2. Start and Connect

```python
import asyncio

async def main():
    # Start client
    await client.start()
    
    # Your client is ready
    print(f"Address: {client.address}")
    print(f"Prekey bundle: {client.get_prekey_bundle()}")
    
    # Cleanup
    await client.stop()

asyncio.run(main())
```

### 3. Establish Secure Session

```python
from talos import TalosClient, SecureChannel

async def communicate():
    async with TalosClient.create("alice") as alice:
        async with TalosClient.create("bob") as bob:
            # Get Bob's prekey bundle
            bob_bundle = bob.get_prekey_bundle()
            
            # Alice establishes session with Bob
            await alice.establish_session(bob.address, bob_bundle)
            
            # Send encrypted message
            await alice.send(bob.address, b"Hello, Bob!")
```

---

## Quick Start with CLI

### 1. Initialize Your Identity

```bash
talos init --name "Alice"
```

This creates:
- Ed25519 signing key pair
- X25519 encryption key pair
- Wallet stored in `~/.talos/wallet.json`

### 2. Start the Registry Server

```bash
# In a separate terminal
talos-server
```

### 3. Register and Listen

```bash
# Register with the network
talos register --server localhost:8765

# Listen for messages
talos listen --port 8766
```

### 4. Send a Message

```bash
# From another terminal (as a different user)
talos send --port 8767 <recipient-address> "Hello, World!"
```

---

## Configuration

Default configuration in `~/.talos/`:

```
~/.talos/
├── wallet.json       # Your identity (keys)
├── sessions.json     # Active sessions (Double Ratchet)
├── blockchain.json   # Message history
├── config.json       # Settings
└── downloads/        # Received files
```

### Environment Variables

Override config via environment:

```bash
export TALOS_NAME="my-agent"
export TALOS_DIFFICULTY=4
export TALOS_LOG_LEVEL="DEBUG"
```

### Configuration Presets

```python
from talos import TalosConfig

# Development (relaxed settings)
config = TalosConfig.development()

# Production (strict settings)
config = TalosConfig.production()
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test modules
pytest tests/test_sdk.py -v
pytest tests/test_session.py -v
```

---

## Test Scripts

Three demo scripts are provided:

```bash
# SDK demonstration
python scripts/test_sdk_demo.py

# Core API demonstration
python scripts/test_api_demo.py

# End-to-end integration tests
python scripts/test_integration.py
```

---

## Next Steps

- [Python SDK](Python-SDK) - Complete SDK documentation
- [Double Ratchet](Double-Ratchet) - Forward secrecy protocol
- [Access Control](Access-Control) - ACL configuration
- [Architecture](Architecture) - System design
- [Cryptography](Cryptography) - Security model
- [API Reference](API-Reference) - Build integrations
