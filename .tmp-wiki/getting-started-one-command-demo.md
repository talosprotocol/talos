---
status: Implemented
audience: Developer
---

# One-Command Demo

> **Problem**: Developers need to see Talos work in under 60 seconds.  
> **Guarantee**: Two agents exchange an encrypted message with verifiable proof.  
> **Non-goal**: This is not production configuration.

## The Demo

```bash
# Start two agents, exchange a message, verify the audit proof
talos demo
```

**What happens:**

1. **Agent Alice** is created with a fresh identity keypair
2. **Agent Bob** is created with a fresh identity keypair
3. Alice and Bob exchange prekey bundles
4. A Double Ratchet session is established
5. Alice sends: `"Hello from Alice with forward secrecy!"`
6. Bob receives and decrypts the message
7. Both sides commit to the audit log
8. Merkle proof is generated and verified

## Expected Output

```
🔐 Talos Demo - Secure Agent Communication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/8] Creating Agent Alice...
      Identity: did:talos:alice_7f3k2m
      Public Key: 0x7f3k...2m4n

[2/8] Creating Agent Bob...
      Identity: did:talos:bob_9x2p1q
      Public Key: 0x9x2p...1q3r

[3/8] Exchanging prekey bundles...
      ✓ Alice → Bob bundle sent
      ✓ Bob → Alice bundle sent

[4/8] Establishing Double Ratchet session...
      ✓ Session established with forward secrecy

[5/8] Alice sends encrypted message...
      Plaintext: "Hello from Alice with forward secrecy!"
      Ciphertext: 0xa3f2...encrypted...8b1c

[6/8] Bob decrypts message...
      ✓ Decrypted: "Hello from Alice with forward secrecy!"
      ✓ Signature verified

[7/8] Committing to audit log...
      ✓ Message hash: 0x4d2e...
      ✓ Block height: 1

[8/8] Verifying Merkle proof...
      ✓ Proof valid
      ✓ Root: 0x8a3f...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Demo complete! Two agents communicated securely.
   Audit proof verified. Forward secrecy maintained.
```

## What This Proves

| Property | Demonstrated |
|----------|--------------|
| **Identity** | Each agent has a unique keypair |
| **Confidentiality** | Message encrypted end-to-end |
| **Forward Secrecy** | Double Ratchet session |
| **Authenticity** | Signature verified |
| **Auditability** | Merkle proof generated |
| **Verifiability** | Proof independently checked |

## Run It Yourself

### Prerequisites

```bash
pip install talos-protocol
```

### Execute

```bash
talos demo
```

### Verbose Mode

```bash
talos demo --verbose
```

Shows cryptographic details: key derivations, ratchet state, proof construction.

## Code Equivalent

If you prefer Python:

```python
import asyncio
from talos import TalosClient

async def demo():
    # Create two agents
    async with TalosClient.create("alice") as alice:
        async with TalosClient.create("bob") as bob:
            # Exchange bundles
            alice_bundle = alice.get_prekey_bundle()
            bob_bundle = bob.get_prekey_bundle()
            
            # Establish sessions
            await alice.establish_session(bob.peer_id, bob_bundle)
            await bob.establish_session(alice.peer_id, alice_bundle)
            
            # Send message
            await alice.send(bob.peer_id, b"Hello with forward secrecy!")
            
            # Verify audit
            proof = alice.get_merkle_proof(message_hash)
            assert alice.verify_proof(proof)
            
            print("✅ Demo complete!")

asyncio.run(demo())
```

## Next Steps

- [Quickstart](quickstart) - Build your first Talos agent
- [SDK Ergonomics](sdk-sdk-ergonomics) - Learn the API patterns
- [Audit Explorer](features-observability-audit-explorer) - Inspect proofs in detail

---

> ⚠️ **Demo only**. For production, see [Hardening Guide](guides-hardening-guide).
