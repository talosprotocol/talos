# Talos Protocol Examples

Copy-paste ready examples demonstrating every API.

## Quick Start

```bash
# Run any example
python examples/01_crypto.py
python examples/02_blockchain.py
# ... etc
```

## Examples

| File | Topic | Key APIs |
|------|-------|----------|
| `01_crypto.py` | Cryptography | `Wallet`, `sign_message`, `encrypt_message`, `derive_shared_secret` |
| `02_blockchain.py` | Blockchain | `Blockchain`, `Block`, `mine_pending`, `validate_chain` |
| `03_acl.py` | Access Control | `ACLManager`, `PeerPermissions`, `RateLimit` |
| `04_light_client.py` | SPV Client | `LightBlockchain`, `BlockHeader`, `SPVProof` |
| `05_did.py` | Decentralized ID | `DIDDocument`, `DIDManager`, `validate_did` |
| `06_dht.py` | Peer Discovery | `DHTNode`, `RoutingTable`, `DIDResolver` |
| `07_validation.py` | Block Validation | `ValidationEngine`, `generate_audit_report` |
| `08_full_demo.py` | **Full Demo** | All APIs + Ollama + In-Memory DB |

## Example 1: Crypto

```python
from src.core.crypto import Wallet, sign_message, verify_signature

# Create wallet
alice = Wallet.generate("alice")

# Sign and verify
msg = b"Hello!"
sig = alice.sign(msg)
valid = verify_signature(msg, sig, alice.signing_keys.public_key)
```

## Example 2: Blockchain

```python
from src.core.blockchain import Blockchain

bc = Blockchain(difficulty=1)
bc.add_data({"msg": "Hello"})
block = bc.mine_pending()
print(f"Mined: {block.hash[:16]}...")
```

## Example 3: ACL

```python
from src.mcp_bridge.acl import ACLManager, PeerPermissions

acl = ACLManager(default_allow=False)
acl.add_peer(PeerPermissions(
    peer_id="user-001",
    allow_tools=["read_*"],
    deny_tools=["delete_*"],
))

result = acl.check("user-001", "tools/call", {"name": "read_data"})
```

## Example 4: Light Client

```python
from src.core.light import LightBlockchain, BlockHeader

light = LightBlockchain(difficulty=1)
header = BlockHeader.from_block(block, difficulty=1)
light.add_header(header)
```

## Example 5: DIDs

```python
from src.core.did import DIDManager

manager = DIDManager(signing_keypair)
did = manager.did
doc = manager.create_document(service_endpoint="wss://...")
```

## Example 6: DHT

```python
from src.network.dht import DHTNode, DIDResolver

node = DHTNode(host="127.0.0.1", port=8468)
await node.store("key", {"data": "value"})
value = await node.get("key")
```

## Example 7: Validation

```python
from src.core.validation import ValidationEngine

engine = ValidationEngine(difficulty=1)
result = engine.validate_block(block, prev_block)
print(f"Valid: {result.is_valid}")
```

## Full Demo

The `secure_chat/` folder contains a complete demo integrating all APIs:
- Ollama AI integration
- In-memory database
- ACL-secured MCP tools
- Blockchain audit trail

```bash
python -m examples.secure_chat.main
```
