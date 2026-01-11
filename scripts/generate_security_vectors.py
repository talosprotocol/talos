import json
import base64
import time
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_vectors():
    # 1. Ed25519 Signatures
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    pub_bytes = public_key.public_bytes_raw()
    pk_b64 = base64.b64encode(pub_bytes).decode()
    
    # Canonical payload example: {"nonce": "...", "timestamp": ...}
    payload = {"nonce": "nonce123", "timestamp": int(time.time()), "type": "HANDSHAKE"}
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    signature = private_key.sign(payload_bytes)
    sig_b64 = base64.b64encode(signature).decode()
    
    vectors = {
        "description": "Ed25519 Test Vectors for Talos Protocol",
        "key_pair": {
            "public_key_b64": pk_b64,
            "key_type": "ed25519"
        },
        "tests": [
            {
                "name": "valid_signature",
                "payload": payload,
                "signature_b64": sig_b64,
                "key_id": pk_b64,
                "expected": "valid"
            },
            {
                "name": "tampered_payload",
                "payload": {**payload, "timestamp": payload["timestamp"] + 1},
                "signature_b64": sig_b64,
                "key_id": pk_b64,
                "expected": "invalid"
            },
            {
                "name": "wrong_key",
                "payload": payload,
                "signature_b64": sig_b64,
                "key_id": "another-key-id",
                "expected": "invalid"
            }
        ]
    }
    
    with open('deploy/repos/talos-contracts/test_vectors/crypto/ed25519_signatures.json', 'w') as f:
        json.dump(vectors, f, indent=2)

    # 2. Replay Nonce Vectors
    replay_vectors = {
        "description": "Replay Nonce Test Vectors",
        "tests": [
            {
                "nonce": "nonce-used-1",
                "timestamp": int(time.time()),
                "status": "first_seen",
                "expected": "accept"
            },
            {
                "nonce": "nonce-used-1",
                "timestamp": int(time.time()) + 1,
                "status": "replayed",
                "expected": "reject"
            }
        ]
    }
    with open('deploy/repos/talos-contracts/test_vectors/crypto/replay_nonce.json', 'w') as f:
        json.dump(replay_vectors, f, indent=2)

    # 3. Canonical Hash Vectors
    canonical_vectors = {
        "description": "Deterministic Serialization Vectors",
        "tests": [
            {
                "name": "key_sorting",
                "input": {"z": 1, "a": 2, "m": 3},
                "expected_json": "{\"a\":2,\"m\":3,\"z\":1}"
            },
            {
                "name": "whitespace_removal",
                "input": {"key": "value"},
                "expected_json": "{\"key\":\"value\"}"
            }
        ]
    }
    with open('deploy/repos/talos-contracts/test_vectors/crypto/canonical_hash.json', 'w') as f:
        json.dump(canonical_vectors, f, indent=2)

    # 4. RBAC Deny-by-Default Vectors
    mkdir_cmd = "mkdir -p deploy/repos/talos-contracts/test_vectors/rbac"
    import os
    os.system(mkdir_cmd)
    
    rbac_vectors = {
        "description": "RBAC Deny-by-Default Test Vectors",
        "tests": [
            {
                "name": "no_identity",
                "identity": None,
                "action": "llm.invoke",
                "expected": "deny"
            },
            {
                "name": "missing_scope",
                "identity": {"principal_id": "p1", "scopes": []},
                "action": "admin.write",
                "expected": "deny"
            },
            {
                "name": "revoked_key",
                "identity": {"principal_id": "p1", "status": "revoked"},
                "action": "llm.invoke",
                "expected": "deny"
            }
        ]
    }
    with open('deploy/repos/talos-contracts/test_vectors/rbac/deny_by_default.json', 'w') as f:
        json.dump(rbac_vectors, f, indent=2)

    print("Generated all security test vectors.")

if __name__ == "__main__":
    generate_vectors()
