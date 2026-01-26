import json
import hashlib
import hmac
import uuid

def jcs(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def hmac_sha256(key, message):
    return hmac.new(key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

tests = []

# 1. Success Bearer IPv4
ev1 = {
    "schema_id": "talos.audit_event",
    "schema_version": "v1",
    "event_id": "01945533-3158-7c85-992d-9865f1715694",
    "ts": "2026-01-11T18:00:00.000Z",
    "request_id": "req-1",
    "surface_id": "llm.invoke",
    "outcome": "success",
    "principal": {
        "auth_mode": "bearer",
        "principal_id": "p-1",
        "team_id": "t-1"
    },
    "http": {
        "method": "POST",
        "path": "/v1/chat/completions",
        "status_code": 200,
        "client_ip_hash": hmac_sha256("test-ip-key-secret", "192.168.1.1"),
        "client_ip_hash_alg": "HMAC-SHA256",
        "client_ip_hash_key_id": "test-ip-key-v1"
    },
    "meta": {
        "model": "gpt-4",
        "tokens": 100
    }
}
tests.append({
    "name": "success_bearer_ipv4",
    "event_without_hash": ev1,
    "input_context": {
        "client_ip": "192.168.1.1",
        "ip_hmac_key": "test-ip-key-secret",
        "ip_hmac_key_id": "test-ip-key-v1"
    },
    "canonical_bytes_hex": jcs(ev1).hex(),
    "event_hash": hashlib.sha256(jcs(ev1)).hexdigest()
})

# 2. Denied Signed IPv6
ev2 = {
    "schema_id": "talos.audit_event",
    "schema_version": "v1",
    "event_id": "01945533-3158-7c85-992d-9865f1715695",
    "ts": "2026-01-11T18:00:01.000Z",
    "request_id": "req-2",
    "surface_id": "admin.write",
    "outcome": "denied",
    "principal": {
        "auth_mode": "signed",
        "principal_id": "p-2",
        "team_id": "t-2",
        "signer_key_id": "key-sig-1"
    },
    "http": {
        "method": "PUT",
        "path": "/v1/policy",
        "status_code": 403,
        "client_ip_hash": hmac_sha256("test-ip-key-secret", "2001:db8::1"),
        "client_ip_hash_alg": "HMAC-SHA256",
        "client_ip_hash_key_id": "test-ip-key-v1"
    },
    "meta": {}
}
tests.append({
    "name": "denied_signed_ipv6",
    "event_without_hash": ev2,
    "input_context": {
        "client_ip": "2001:db8::1",
        "ip_hmac_key": "test-ip-key-secret",
        "ip_hmac_key_id": "test-ip-key-v1"
    },
    "canonical_bytes_hex": jcs(ev2).hex(),
    "event_hash": hashlib.sha256(jcs(ev2)).hexdigest()
})

# 3. Anonymous No IP (Omitted Fields)
ev3 = {
    "schema_id": "talos.audit_event",
    "schema_version": "v1",
    "event_id": "01945533-3158-7c85-992d-9865f1715696",
    "ts": "2026-01-11T18:00:02.000Z",
    "request_id": "req-3",
    "surface_id": "public.read",
    "outcome": "success",
    "principal": {
        "auth_mode": "anonymous",
        "principal_id": "anonymous"
    },
    "http": {
        "method": "GET",
        "path": "/v1/health",
        "status_code": 200
    },
    "meta": {}
}
tests.append({
    "name": "anonymous_no_ip",
    "event_without_hash": ev3,
    "input_context": {
        "client_ip": None
    },
    "canonical_bytes_hex": jcs(ev3).hex(),
    "event_hash": hashlib.sha256(jcs(ev3)).hexdigest()
})

# 4. Failure with Meta Filtering (Disallowed keys should be filtered out BEFORE hashing)
# Testing that we ONLY hash the final filtered object.
ev4 = {
    "schema_id": "talos.audit_event",
    "schema_version": "v1",
    "event_id": "01945533-3158-7c85-992d-9865f1715697",
    "ts": "2026-01-11T18:00:03.000Z",
    "request_id": "req-4",
    "surface_id": "llm.invoke",
    "outcome": "failure",
    "principal": {
        "auth_mode": "bearer",
        "principal_id": "p-1",
        "team_id": "t-1"
    },
    "http": {
        "method": "POST",
        "path": "/v1/chat/completions",
        "status_code": 500
    },
    "meta": {
        "error": "Timeout",
        "tokens": 0
    }
}
tests.append({
    "name": "failure_meta_filtered",
    "event_without_hash": ev4,
    "input_context": {
        "client_ip": "unknown",
        "unfiltered_meta": {
            "error": "Timeout",
            "tokens": 0,
            "secret_key": "REMOVE_ME"
        }
    },
    "canonical_bytes_hex": jcs(ev4).hex(),
    "event_hash": hashlib.sha256(jcs(ev4)).hexdigest()
})

output = {
    "description": "Normative Audit Event Vectors (Phase 5.1 Hardened)",
    "tests": tests
}

print(json.dumps(output, indent=2))
