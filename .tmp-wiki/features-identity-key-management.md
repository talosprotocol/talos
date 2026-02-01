---
status: Implemented
audience: Developer, Operator
---

# Key Management

> **Problem**: Keys require careful lifecycle management.  
> **Guarantee**: Guidance for key types, rotation, and storage.  
> **Non-goal**: HSM implementation details.

---

## Key Types

| Key Type | Algorithm | Lifetime | Purpose |
|----------|-----------|----------|---------|
| **Identity Key** | Ed25519 | Years | Sign messages, prove identity |
| **Encryption Key** | X25519 | Years | Derive shared secrets |
| **Signed Prekey** | X25519 | Weeks-Months | Session establishment |
| **One-Time Prekeys** | X25519 | Single use | Perfect forward secrecy |
| **Ratchet Keys** | X25519 | Per-message | Forward secrecy |
| **Chain Keys** | Symmetric | Per-message | Message key derivation |
| **Message Keys** | Symmetric | Single use | Encrypt one message |

---

## Key Generation

### Identity Keys

```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate identity keypair
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()
```

### Encryption Keys

```python
from cryptography.hazmat.primitives.asymmetric import x25519

# Generate encryption keypair
private_key = x25519.X25519PrivateKey.generate()
public_key = private_key.public_key()
```

### Randomness

All keys generated using `secrets` module (OS-level CSPRNG):

```python
import secrets

# Talos uses this internally
random_bytes = secrets.token_bytes(32)
```

---

## Key Storage

### Encrypted Storage (Default)

```python
client = await TalosClient.create(
    "agent",
    data_dir="/secure/path",
    password=os.environ["TALOS_KEY_PASSWORD"]
)
```

**Encryption**: AES-256-GCM with Argon2id key derivation

### Storage Format

```
data_dir/
├── identity.key.enc      # Encrypted identity private key
├── encryption.key.enc    # Encrypted X25519 private key
├── prekeys/
│   ├── signed_prekey.enc
│   └── otpk_*.enc
└── metadata.json         # Non-sensitive metadata
```

### Permissions

```bash
chmod 700 /secure/path
chmod 600 /secure/path/*.enc
```

---

## Key Rotation

### Rotation Schedule

| Key Type | Recommended Frequency | Trigger |
|----------|----------------------|---------|
| Identity | Annually | Or on compromise |
| Signed Prekey | Monthly | Automatic |
| One-Time Prekeys | Replenish when < 10 | Automatic |
| Ratchet | Every message | Automatic |

### Prekey Rotation

```python
# Rotate signed prekey
await client.rotate_signed_prekey()

# Replenish one-time prekeys
await client.replenish_one_time_prekeys(count=100)
```

### Identity Rotation (Rare)

```python
# Planned rotation with migration period
new_identity = await client.rotate_identity(
    migration_days=7,
    notify_peers=True
)
```

**Process**:
1. Generate new keypair
2. Sign new key with old key (continuity proof)
3. Notify peers of rotation
4. Accept messages to both keys during migration
5. Revoke old key after migration

---

## Key Backup

### Encrypted Backup

```python
# Create encrypted backup
await client.export_keys(
    path="/backup/agent_keys.enc",
    password=backup_password
)
```

### Backup Best Practices

| Practice | Rationale |
|----------|-----------|
| Different password than runtime | Limits exposure |
| Store offline | Protection from online attacks |
| Multiple copies | Disaster recovery |
| Test restoration | Verify backups work |

### Restoration

```python
# Restore from backup
client = await TalosClient.recover(
    backup_path="/backup/agent_keys.enc",
    password=backup_password
)
```

---

## HSM/TPM Integration (Planned)

### Design Principles

1. **Key never leaves HSM**: Only public key exported
2. **Signing in HSM**: Private operations in hardware
3. **Attestation**: Prove keys are hardware-bound

### Planned Interface

```python
# Future HSM integration
client = await TalosClient.create(
    "agent",
    key_backend="hsm",
    hsm_config={
        "type": "pkcs11",
        "module": "/usr/lib/softhsm/libsofthsm2.so",
        "slot": 0,
        "pin": os.environ["HSM_PIN"]
    }
)
```

### TPM (Trusted Platform Module)

```python
# Future TPM integration
client = await TalosClient.create(
    "agent",
    key_backend="tpm",
    tpm_config={
        "device": "/dev/tpm0"
    }
)
```

---

## Secure Enclaves (Planned)

### Intel SGX

```python
# Future SGX integration
client = await TalosClient.create(
    "agent",
    key_backend="sgx",
    enclave_path="/path/to/enclave.signed.so"
)
```

### AWS Nitro Enclaves

```python
# Future Nitro integration
client = await TalosClient.create(
    "agent",
    key_backend="nitro",
    enclave_cid=16
)
```

---

## Key Compromise Response

### Detection

Monitor for:
- Unexpected key usage patterns
- Failed signature verifications
- Duplicate message IDs
- Concurrent usage from multiple locations

### Immediate Response

```python
# Emergency rotation
await client.emergency_rotate(
    reason="suspected compromise",
    revoke_old=True,
    notify_peers=True
)
```

### Post-Compromise

1. Rotate all keys immediately
2. Revoke old identity
3. Notify all peers
4. Audit for unauthorized actions
5. Investigate root cause

---

## Key Derivation

### HKDF Usage

```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def derive_key(ikm: bytes, info: bytes, length: int = 32) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info
    ).derive(ikm)
```

### Key Hierarchy

```
identity_key
    └── signed_prekey (derived context)
            └── session_secret (DH)
                    └── root_key
                            ├── sending_chain_key
                            │       └── message_key_1
                            │       └── message_key_2
                            └── receiving_chain_key
                                    └── message_key_1
```

---

## Security Considerations

### Key Handling

| Do | Don't |
|----|-------|
| Zero memory after use | Leave keys in memory |
| Use constant-time comparison | Use `==` for key comparison |
| Encrypt at rest | Store plaintext keys |
| Use hardware RNG | Use predictable RNG |
| Validate key material | Trust input blindly |

### Constant-Time Comparison

```python
import hmac

def secure_compare(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)
```

### Memory Zeroing

```python
import ctypes

def zero_bytes(data: bytearray):
    ctypes.memset(ctypes.addressof((ctypes.c_char * len(data)).from_buffer(data)), 0, len(data))
```

---

**See also**: [Cryptography](security-cryptography) | [Agent Lifecycle](business-agent-lifecycle) | [Hardening Guide](guides-hardening-guide)
