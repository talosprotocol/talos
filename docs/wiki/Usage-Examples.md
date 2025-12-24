# Usage & Examples

> **Copy-paste ready examples for every Talos API**

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/talos-protocol.git
cd talos-protocol
pip install -e .

# Run any example
python examples/01_crypto.py
```

---

## Examples Overview

| Example | Topic | Run Command |
|---------|-------|-------------|
| [01_crypto.py](file:///examples/01_crypto.py) | Cryptography | `python examples/01_crypto.py` |
| [02_blockchain.py](file:///examples/02_blockchain.py) | Blockchain | `python examples/02_blockchain.py` |
| [03_acl.py](file:///examples/03_acl.py) | Access Control | `python examples/03_acl.py` |
| [04_light_client.py](file:///examples/04_light_client.py) | SPV Client | `python examples/04_light_client.py` |
| [05_did.py](file:///examples/05_did.py) | DIDs | `python examples/05_did.py` |
| [06_dht.py](file:///examples/06_dht.py) | DHT | `python examples/06_dht.py` |
| [07_validation.py](file:///examples/07_validation.py) | Validation | `python examples/07_validation.py` |
| [08_full_demo.py](file:///examples/08_full_demo.py) | **Full Demo** | `python examples/08_full_demo.py` |

---

## 1. Cryptography

```python
from src.core.crypto import (
    Wallet,
    sign_message,
    verify_signature,
    derive_shared_secret,
    encrypt_message,
    decrypt_message,
)

# Create identity
alice = Wallet.generate("alice")
bob = Wallet.generate("bob")

# Sign message
msg = b"Hello!"
sig = alice.sign(msg)

# Verify signature
valid = verify_signature(msg, sig, alice.signing_keys.public_key)

# Key exchange
shared = derive_shared_secret(
    alice.encryption_keys.private_key,
    bob.encryption_keys.public_key
)

# Encrypt
nonce, ciphertext = encrypt_message(b"Secret", shared)

# Decrypt
plaintext = decrypt_message(ciphertext, shared, nonce)
```

---

## 2. Blockchain

```python
from src.core.blockchain import Blockchain

# Create blockchain
bc = Blockchain(difficulty=2)

# Add data
bc.add_data({"sender": "alice", "msg": "Hello"})
bc.add_data({"sender": "bob", "msg": "Hi!"})

# Mine block
block = bc.mine_pending()
print(f"Mined: {block.hash[:16]}...")

# Validate chain
is_valid = bc.validate_chain(bc.chain)

# Serialize
data = bc.to_dict()
bc2 = Blockchain.from_dict(data)
```

---

## 3. Access Control (ACL)

```python
from src.mcp_bridge.acl import ACLManager, PeerPermissions, Permission, RateLimit

# Create ACL manager
acl = ACLManager(default_allow=False)

# Add peer with permissions
acl.add_peer(PeerPermissions(
    peer_id="user-001",
    allow_tools=["read_*", "query_*"],
    deny_tools=["delete_*"],
    allow_resources=["public/*"],
    rate_limit=RateLimit(requests_per_minute=60),
))

# Check access
result = acl.check("user-001", "tools/call", {"name": "read_data"})
if result.permission == Permission.ALLOW:
    print("Access granted")
```

---

## 4. Light Client (SPV)

```python
from src.core.light import LightBlockchain, BlockHeader, SPVProof
from src.core.blockchain import Blockchain

# Full node
full = Blockchain(difficulty=1)
full.add_data({"msg": "test"})
full.mine_pending()

# Light client - headers only
light = LightBlockchain(difficulty=1)

# Sync headers
for block in full.chain:
    header = BlockHeader.from_block(block, difficulty=1)
    light.add_header(header)

# Verify SPV proof
proof = SPVProof(
    data_hash=block.merkle_root,
    block_hash=block.hash,
    block_height=block.index,
    merkle_root=block.merkle_root,
    merkle_path=[],
)
is_valid = light.verify_spv_proof(proof)
```

---

## 5. Decentralized Identity (DID)

```python
from src.core.did import DIDDocument, DIDManager, validate_did
from dataclasses import dataclass

@dataclass
class KeyPair:
    public_key: bytes

# Create DID
signing = KeyPair(public_key=b"x" * 32)
manager = DIDManager(signing)

did = manager.did  # did:talos:abc123...

# Create document
doc = manager.create_document(
    service_endpoint="wss://agent.example.com:8765"
)

# Add service
doc.add_service("#backup", "BackupService", "https://backup.com")

# Validate
is_valid = validate_did(did)

# Serialize
json_str = doc.to_json()
```

---

## 6. DHT (Peer Discovery)

```python
import asyncio
from src.network.dht import DHTNode, DIDResolver, NodeInfo

async def main():
    # Create node
    node = DHTNode(host="127.0.0.1", port=8468)
    
    # Store/retrieve
    await node.store("key", {"data": "value"})
    value = await node.get("key")
    
    # DID resolution
    resolver = DIDResolver(node)
    await resolver.publish("did:talos:abc", {"id": "did:talos:abc"})
    doc = await resolver.resolve("did:talos:abc")

asyncio.run(main())
```

---

## 7. Block Validation

```python
import asyncio
from src.core.blockchain import Blockchain
from src.core.validation import ValidationEngine, generate_audit_report

async def main():
    bc = Blockchain(difficulty=1)
    bc.add_data({"msg": "test"})
    bc.mine_pending()
    
    engine = ValidationEngine(difficulty=1)
    
    # Validate block
    result = await engine.validate_block(bc.chain[1], bc.chain[0])
    print(f"Valid: {result.is_valid}")
    print(f"Layers: {result.layers_passed}")
    
    # Audit report
    report = generate_audit_report(bc.chain[1], result)
    print(f"Report: {report.report_id}")

asyncio.run(main())
```

---

## 8. Full Secure Chat Demo

```bash
# Run complete demo
python examples/08_full_demo.py

# With Ollama (optional)
ollama serve  # In separate terminal
python examples/08_full_demo.py
```

Features demonstrated:
- End-to-end encryption
- Digital signatures
- Blockchain audit trail
- ACL-secured MCP tools
- Ollama AI integration

---

## 9. Live MCP POC (Ollama + DB)

Demonstrates a full MCP flow:
1.  **Registry**: Starts a local registry.
2.  **Alice (Host)**: Registers and exposes a Mock Database via `mcp-serve`.
3.  **Bob (Agent)**: Registers and connects to Alice via `mcp-connect`.
4.  **Interaction**: Bob sends JSON-RPC commands to Query Alice's DB over the blockchain tunnel.

```bash
# Run the POC
./examples/poc_ollama_db/run_poc.sh
```

**Expected Output**:
```json
[Agent] 🦅 Calling Tool: query_db(users)...
[Agent] ✅ Database Result:
[
  {
    "id": 1,
    "name": "Alice",
    "role": "engineer"
  },
  {
    "id": 2,
    "name": "Bob",
    "role": "manager"
  }
]
```

---

## Common Patterns

### Pattern 1: Secure Message Exchange

```python
from src.core.crypto import Wallet, derive_shared_secret, encrypt_message, decrypt_message

# Setup
alice = Wallet.generate("alice")
bob = Wallet.generate("bob")

# Alice encrypts for Bob
shared = derive_shared_secret(
    alice.encryption_keys.private_key,
    bob.encryption_keys.public_key
)
nonce, encrypted = encrypt_message(b"Hello Bob!", shared)

# Bob decrypts
bob_shared = derive_shared_secret(
    bob.encryption_keys.private_key,
    alice.encryption_keys.public_key
)
decrypted = decrypt_message(encrypted, bob_shared, nonce)
```

### Pattern 2: Signed Blockchain Entry

```python
from src.core.crypto import Wallet
from src.core.blockchain import Blockchain

wallet = Wallet.generate("agent")
bc = Blockchain(difficulty=1)

# Sign data before adding
data = {"msg": "Important message"}
signature = wallet.sign(str(data).encode())

bc.add_data({
    "data": data,
    "signature": signature.hex(),
    "sender": wallet.address,
})
bc.mine_pending()
```

### Pattern 3: ACL-Protected Tool

```python
from src.mcp_bridge.acl import ACLManager, PeerPermissions, Permission

acl = ACLManager(default_allow=False)

acl.add_peer(PeerPermissions(
    peer_id="trusted-agent",
    allow_tools=["*"],
))

def secure_tool(peer_id: str, tool: str, args: dict):
    result = acl.check(peer_id, "tools/call", {"name": tool})
    if result.permission != Permission.ALLOW:
        raise PermissionError(result.reason)
    # Execute tool...
```

---

## See Also

- [Getting Started](Getting-Started.md)
- [Python SDK](Python-SDK.md)
- [API Reference](API-Reference.md)
- [Development Guide](Development.md)
