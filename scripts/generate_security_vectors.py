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
    
    # 5. Audit Event Vectors (Hardened Phase 5.1)
    # RFC 8785 JCS + HMAC-SHA256
    import hashlib
    import hmac
    
    def jcs_serialize(data):
        # Strict JCS emulation for simple types: sort_keys=True, separators=(',', ':')
        # Ensure unicode is not escaped (ensure_ascii=False) - RFC 8785
        return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    
    def ip_hmac(key, ip):
        key_bytes = key.encode('utf-8')
        ip_bytes = ip.encode('utf-8')
        return hmac.new(key_bytes, ip_bytes, hashlib.sha256).hexdigest()
    
    audit_vectors = {
        "description": "Hardened Audit Event Vectors (RFC 8785 + HMAC)",
        "tests": []
    }
    
    ip_key = "test-ip-key-secret"
    ip_key_id = "test-ip-key-v1"
    
    # Vector 1: Success (Bearer, IPv4)
    # Construct base event
    event_1 = {
        "schema_id": "talos.audit_event",
        "schema_version": "v1",
        "event_id": "01945533-3158-7c85-992d-9865f1715694", 
        "ts": "2026-01-11T18:00:00.000Z",
        "request_id": "req-1",
        "surface_id": "llm.invoke",
        "action": "llm.invoke",
        "status": "success",
        "data_classification": "public",
        "principal": {
            "principal_id": "p-1",
            "team_id": "t-1",
            "org_id": "org-1",
            "auth_mode": "bearer"
        },
        "http": {
            "method": "POST",
            "path": "/v1/chat/completions",
            "status_code": 200,
            "client_ip_hash": ip_hmac(ip_key, "192.168.1.1"),
            "client_ip_hash_alg": "HMAC-SHA256",
            "client_ip_hash_key_id": ip_key_id
        },
        "meta": {
            "model": "gpt-4",
            "tokens": 100
        }
    }
    
    # Serialize (JCS)
    jcs_1 = jcs_serialize(event_1)
    hash_1 = hashlib.sha256(jcs_1).hexdigest()
    
    audit_vectors["tests"].append({
        "name": "success_bearer_ipv4",
        "event_without_hash": event_1,
        "input_context": {
            "client_ip": "192.168.1.1",
            "ip_hmac_key": ip_key,
            "ip_hmac_key_id": ip_key_id
        },
        "canonical_bytes_hex": jcs_1.hex(),
        "event_hash": hash_1
    })
    
    # Vector 2: Denied (Signed, IPv6)
    event_2 = {
        "schema_id": "talos.audit_event",
        "schema_version": "v1",
        "event_id": "01945533-3158-7c85-992d-9865f1715695",
        "ts": "2026-01-11T18:00:01.000Z",
        "request_id": "req-2",
        "surface_id": "admin.write",
        "action": "admin.write",
        "status": "denied",
        "data_classification": "sensitive",
        "principal": {
            "principal_id": "p-2",
            "team_id": "t-2",
            "auth_mode": "signed",
            "signer_key_id": "key-sig-1"
        },
        "http": {
            "method": "PUT",
            "path": "/v1/policy",
            "status_code": 403,
            "client_ip_hash": ip_hmac(ip_key, "2001:db8::1"),
            "client_ip_hash_alg": "HMAC-SHA256",
            "client_ip_hash_key_id": ip_key_id
        },
        "meta": {}
    }
    
    jcs_2 = jcs_serialize(event_2)
    hash_2 = hashlib.sha256(jcs_2).hexdigest()
    
    audit_vectors["tests"].append({
        "name": "denied_signed_ipv6",
        "event_without_hash": event_2,
        "input_context": {
            "client_ip": "2001:db8::1",
            "ip_hmac_key": ip_key,
            "ip_hmac_key_id": ip_key_id
        },
        "canonical_bytes_hex": jcs_2.hex(),
        "event_hash": hash_2
    })
    
    # Vector 3: Missing IP (Unknown)
    event_3 = {
        "schema_id": "talos.audit_event",
        "schema_version": "v1",
        "event_id": "01945533-3158-7c85-992d-9865f1715696",
        "ts": "2026-01-11T18:00:02.000Z",
        "request_id": "req-3",
        "surface_id": "a2a.rpc",
        "action": "a2a.invoke",
        "status": "success",
        "data_classification": "sensitive",
        "principal": {
            "principal_id": "p-3",
            "team_id": "t-3",
            "auth_mode": "service"
            # No signer_key_id
        },
        "http": {
            "method": "POST",
            "path": "/a2a/v1/",
            "status_code": 200
            # No IP fields
        },
        "meta": {"task_id": "task-1"}
    }
    
    jcs_3 = jcs_serialize(event_3)
    hash_3 = hashlib.sha256(jcs_3).hexdigest()
    
    audit_vectors["tests"].append({
        "name": "success_missing_ip",
        "event_without_hash": event_3,
        "input_context": {
            "client_ip": None
        },
        "canonical_bytes_hex": jcs_3.hex(),
        "event_hash": hash_3
    })
    
    with open('deploy/repos/talos-contracts/test_vectors/audit_event_vectors.json', 'w') as f:
        json.dump(audit_vectors, f, indent=2)

    print("Generated audit vectors.")

if __name__ == "__main__":
    generate_vectors()
