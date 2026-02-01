# API Reference

## Core Modules

> **Note**: JSON Schemas for all core models are available in [Schemas](schemas).

### `src.core.blockchain`

#### Class: `Blockchain`

Production-ready blockchain for message storage.

```python
from src.core.blockchain import Blockchain

# Create blockchain
bc = Blockchain(
    difficulty=2,              # PoW difficulty (leading zeros)
    validator=None,            # Optional data validation function
    max_block_size=1_000_000,  # 1MB max block
    max_pending=10_000         # Max mempool size
)
```

##### Blockchain Properties

| Property | Type | Description |
| :--- | :--- | :--- |
| `height` | `int` | Current chain height (blocks - 1) |
| `latest_block` | `Block` | Most recent block |
| `total_work` | `int` | Cumulative proof-of-work |
| `genesis_hash` | `str` | Genesis block hash |

##### Blockchain Methods

| Method | Returns | Description |
| :--- | :--- | :--- |
| `add_data(data: dict)` | `bool` | Add data to mempool |
| `mine_pending()` | `Optional[Block]` | Mine pending data into block |
| `is_chain_valid()` | `bool` | Validate entire chain |
| `get_block_by_hash(hash: str)` | `Optional[Block]` | O(1) lookup by hash |
| `get_block_by_height(height: int)` | `Optional[Block]` | O(1) lookup by height |
| `get_message_block(msg_id: str)` | `Optional[Block]` | Find block containing message |
| `get_merkle_proof(msg_id: str)` | `Optional[MerkleProof]` | Generate existence proof |
| `save(path: Path)` | `None` | Atomically save to disk |
| `load(path: Path)` | `Blockchain` | Load from disk (classmethod) |
| `get_status()` | `ChainStatus` | Get chain status for sync |
| `should_accept_chain(status)` | `bool` | Check if remote chain is better |
| `replace_chain(chain: list)` | `bool` | Replace with new chain |

##### Example

```python
from src.core.blockchain import Blockchain

# Create and populate
bc = Blockchain(difficulty=2)
bc.add_data({"id": "msg_1", "content": "Hello"})
bc.add_data({"id": "msg_2", "content": "World"})
block = bc.mine_pending()

# Query
print(f"Height: {bc.height}")
print(f"Block: {bc.get_block_by_hash(block.hash)}")
proof = bc.get_merkle_proof("msg_1")

# Persist
bc.save("~/.talos/blockchain.json")
loaded = Blockchain.load("~/.talos/blockchain.json")
```

---

#### Class: `Block`

Individual blockchain block.

```python
from src.core.blockchain import Block

block = Block(
    index=1,
    timestamp=time.time(),
    data={"messages": [...]},
    previous_hash="abc123..."
)
block.mine(difficulty=2)
```

##### Block Properties

| Property | Type | Description |
| :--- | :--- | :--- |
| `hash` | `str` | SHA-256 hash (64 hex chars) |
| `merkle_root` | `str` | Merkle root of data |
| `size` | `int` | Approximate size in bytes |

##### Block Methods

| Method | Returns | Description |
| :--- | :--- | :--- |
| `calculate_hash()` | `str` | Compute block hash |
| `mine(difficulty: int)` | `None` | Mine with PoW |
| `validate(difficulty: int)` | `bool` | Validate PoW |
| `to_dict()` | `dict` | Serialize to dict |
| `from_dict(data)` | `Block` | Deserialize (classmethod) |

---

### `src.core.crypto`

#### Class: `Wallet`

User identity container.

```python
from src.core.crypto import Wallet

# Generate new wallet
wallet = Wallet.generate(name="Alice")

# Access keys
print(wallet.address)       # Public key hex (64 chars)
print(wallet.address_short) # First 16 chars

# Sign data
signature = wallet.sign(b"Hello, World!")

# Serialize
data = wallet.to_dict()
restored = Wallet.from_dict(data)
```

#### Functions

| Function | Signature | Description |
| :--- | :--- | :--- |
| `generate_signing_keypair()` | `-> KeyPair` | Ed25519 key pair |
| `generate_encryption_keypair()` | `-> KeyPair` | X25519 key pair |
| `sign_message(msg, private_key)` | `-> bytes` | Ed25519 signature |
| `verify_signature(msg, sig, public_key)` | `-> bool` | Verify signature |
| `derive_shared_secret(private, peer_public)` | `-> bytes` | ECDH secret |
| `encrypt_message(plaintext, key)` | `-> (nonce, ciphertext)` | ChaCha20-Poly1305 |
| `decrypt_message(ciphertext, key, nonce)` | `-> bytes` | Decrypt |

---

### `src.core.session`

#### Class: `SessionManager`

Manages Double Ratchet sessions for forward secrecy.

```python
from src.core.session import SessionManager

manager = SessionManager(wallet)

# Prepare prekeys for others to connect
bundle = manager.get_prekey_bundle()

# Establish session
session = await manager.establish_session(peer_address, peer_bundle)

# Encrypt/Decrypt
ciphertext = session.encrypt(b"Secret message")
plaintext = session.decrypt(ciphertext)
```

---

### `src.core.did`

#### Class: `DIDManager`

W3C Decentralized Identity management.

```python
from src.core.did import DIDManager

did_mgr = DIDManager(wallet.signing_keys)
print(did_mgr.did)  # did:talos:abc123...

# Create DID Document
doc = did_mgr.create_document(service_endpoint="ws://localhost:8765")
```

---

### `src.core.message`

#### Enum: `MessageType`

```python
class MessageType(Enum):
    # Basic
    TEXT = auto()
    ACK = auto()
    
    # File transfer
    FILE = auto()
    FILE_CHUNK = auto()
    FILE_COMPLETE = auto()
    FILE_ERROR = auto()
    
    # Streaming
    STREAM_START = auto()
    STREAM_CHUNK = auto()
    STREAM_END = auto()
    
    # Control
    HANDSHAKE = auto()
    PING = auto()
    PONG = auto()
    
    # Chain sync
    CHAIN_STATUS = auto()
    CHAIN_REQUEST = auto()
    CHAIN_RESPONSE = auto()
```

#### Class: `MessagePayload`

```python
from src.core.message import MessagePayload, MessageType

msg = MessagePayload.create(
    msg_type=MessageType.TEXT,
    sender="abc123...",
    recipient="def456...",
    content=b"encrypted content",
    signature=b"signature",
    nonce=b"12-byte-nonce",
    metadata={"name": "Alice"}
)

# Serialize
json_data = msg.to_dict()
binary = msg.to_bytes()

# Deserialize
restored = MessagePayload.from_dict(json_data)
restored = MessagePayload.from_bytes(binary)
```

---

### `src.engine.engine`

#### Class: `TransmissionEngine`

Main interface for sending/receiving.

```python
from src.engine import TransmissionEngine

engine = TransmissionEngine(
    wallet=wallet,
    p2p_node=p2p_node,
    blockchain=blockchain,
    downloads_dir=Path("~/.talos/downloads")
)

# Register callbacks
engine.on_message(async_message_handler)
engine.on_file(async_file_handler)

# Send text
await engine.send_text(recipient_id, "Hello!")

# Send file
transfer_id = await engine.send_file(recipient_id, "/path/to/file.jpg")

# Get transfers
active = engine.get_active_transfers()
received = engine.get_received_files()
```

---

### `src.engine.media`

#### Class: `MediaFile`

Local file wrapper with validation.

```python
from src.engine.media import MediaFile

file = MediaFile.from_path("/path/to/photo.jpg")
print(file.filename)      # photo.jpg
print(file.size_formatted) # 2.4 MB
print(file.media_type)    # MediaType.IMAGE
print(file.file_hash)     # SHA-256 hash

# Read in chunks
for chunk in file.read_chunks(chunk_size=256*1024):
    process(chunk)
```

#### Class: `TransferManager`

Concurrent transfer tracking.

```python
from src.engine.media import TransferManager

manager = TransferManager(max_concurrent=5)

# Create transfer
transfer = manager.create_send_transfer(
    transfer_id="abc123",
    media_file=media_file,
    peer_id="peer456"
)

# Track progress
print(transfer.progress_percent)  # 0-100
print(transfer.status)            # TransferStatus.IN_PROGRESS
```

---

### `src.client.client`

#### Class: `Client`

High-level client interface.

```python
from src.client import Client, ClientConfig

config = ClientConfig()
client = Client(config)

# Setup
client.load_wallet()  # or create_wallet("Alice")
await client.register()
await client.start()

# Messaging
await client.send_message(recipient, "Hello!")
await client.send_file(recipient, "/path/to/file.pdf")

# Callbacks
client.on_message(handler)
client.on_file(file_handler)

# Cleanup
await client.stop()
```

---

## CLI Reference

```bash
# Identity
talos init --name "Alice"

# Network
talos register --server localhost:8765
talos listen --port 8766
talos peers

# Messaging
talos send <recipient> "Hello!"
talos send-file <recipient> /path/to/file

# Status
talos status
talos history
```
