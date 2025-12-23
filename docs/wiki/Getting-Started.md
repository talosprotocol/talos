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
aiohttp>=3.9.0          # Async HTTP client
```

## Quick Start

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

## Configuration

Default configuration is stored in `~/.talos/`:

```
~/.talos/
├── wallet.json       # Your identity (keys)
├── blockchain.json   # Message history
└── downloads/        # Received files
```
└── downloads/        # Received files
```

## Next Steps

- [Architecture Overview](Architecture) - Understand the system design
- [Cryptography Guide](Cryptography) - Learn about the security model
- [API Reference](API-Reference) - Build integrations
