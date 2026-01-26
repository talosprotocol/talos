#!/usr/bin/env python3
"""
Generate strict test vectors for Talos Protocol Phase 4.1.
sources: PROTOCOL.md, implementation_plan.md
"""

import json
import base64
import hashlib
import os
import shutil
import time
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

# --- Configuration ---
VECTOR_DIR = "test_vectors"
PROTOCOL_VERSION = "1"
# Fixed seed for deterministic keys
SEED_HEX = "00" * 32  # 32 bytes of zeros
PRIVATE_KEY_BYTES = bytes.fromhex(SEED_HEX)
PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(PRIVATE_KEY_BYTES)
PUBLIC_KEY = PRIVATE_KEY.public_key()
PUBLIC_KEY_HEX = PUBLIC_KEY.public_bytes_raw().hex()
PEER_ID = f"did:talos:{PUBLIC_KEY_HEX}"

# --- Helper Functions ---

def canonical_json(obj: Any) -> bytes:
    """
    RFC 8785 strict canonicalization for v1.
    - No floats (implicit in data types used)
    - No duplicate keys (python dict guarantees this for one level, but strict check?)
    - No nulls (we should strict filter or assume input doesn't have them if we strictly construct)
    - UTF-8
    - Sort keys
    - No whitespace
    """
    # Sanity check for types
    def validate(node):
        if isinstance(node, float):
            raise ValueError("Floats not allowed in v1 canonicalization")
        if node is None:
            raise ValueError("Nulls not allowed in v1 canonicalization - omit field instead")
        if isinstance(node, dict):
            for k, v in node.items():
                validate(v)
        elif isinstance(node, list):
            for v in node:
                validate(v)
    
    validate(obj)
    
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':')
    ).encode('utf-8')

def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sign(data: bytes, key: Ed25519PrivateKey) -> str:
    signature = key.sign(data)
    return serialize_bytes(signature) # Return as hex for vectors or base64? 
    # Plan says: capability_signature.hex in positive vectors list.
    # But later says "Binary fields = base64url" for frames.
    # Let's stick to hex for separated files, base64url for inside JSON.
    return signature.hex()

def sign_base64(data: bytes, key: Ed25519PrivateKey) -> str:
    return serialize_bytes(key.sign(data))

def serialize_bytes(data: bytes) -> str:
    """Base64URL no padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def write_vector(path: str, data: Any):
    # If bytes, write raw property
    # If generic obj, write json
    if isinstance(data, bytes):
        with open(path, "wb") as f:
            f.write(data)
    elif isinstance(data, str):
        with open(path, "w") as f:
            f.write(data)
    else:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

def setup_dirs():
    if os.path.exists(VECTOR_DIR):
        shutil.rmtree(VECTOR_DIR)
    os.makedirs(f"{VECTOR_DIR}/positive")
    os.makedirs(f"{VECTOR_DIR}/negative")
    os.makedirs(f"{VECTOR_DIR}/replay")
    os.makedirs(f"{VECTOR_DIR}/session")

# --- Generators ---

def generate_positive():
    print("Generating Positive Vectors...")
    
    # 1. Capability
    # ----------------
    cap_content = {
        "v": "1",
        "iss": PEER_ID,
        "sub": "did:talos:recipient",
        "scope": "tools/call",
        "constraints": {"tool": "weather", "method": "get"},
        "iat": 1700000000,
        "exp": 1700003600
    }
    
    cap_canon_content = canonical_json(cap_content)
    sig_raw = PRIVATE_KEY.sign(cap_canon_content)
    sig_str = serialize_bytes(sig_raw)
    
    cap_token = cap_content.copy()
    cap_token["sig"] = sig_str
    
    cap_canon_token = canonical_json(cap_token)
    cap_hash = sha256_hash(cap_canon_token)
    
    write_vector(f"{VECTOR_DIR}/positive/capability.json", cap_token)
    write_vector(f"{VECTOR_DIR}/positive/capability_content_canonical.bytes", cap_canon_content)
    write_vector(f"{VECTOR_DIR}/positive/capability_signature.hex", sig_raw.hex())
    write_vector(f"{VECTOR_DIR}/positive/capability_token_canonical.bytes", cap_canon_token)
    write_vector(f"{VECTOR_DIR}/positive/capability_hash.hex", cap_hash)
    
    # 2. MCP Request
    # ----------------
    mcp_req = {
        "jsonrpc": "2.0",
        "id": "req-123",
        "method": "tools/call",
        "params": {
            "name": "weather",
            "arguments": {"city": "Paris"}
        }
    }
    mcp_canon = canonical_json(mcp_req)
    req_hash = sha256_hash(mcp_canon)
    
    write_vector(f"{VECTOR_DIR}/positive/mcp_request.json", mcp_req)
    write_vector(f"{VECTOR_DIR}/positive/mcp_request_canonical.bytes", mcp_canon)
    write_vector(f"{VECTOR_DIR}/positive/request_hash.hex", req_hash)

    # 3. Envelope / MCP Proxy Frames
    # ------------------------------
    
    session_id = "sess-uuid-42"
    correlation_id = "corr-uuid-99"
    ts = 1700000100
    
    # MCP_MESSAGE Frame
    mcp_msg_content = {
        "type": "MCP_MESSAGE",
        "protocol_version": PROTOCOL_VERSION,
        "session_id": session_id,
        "correlation_id": correlation_id,
        "peer_id": PEER_ID,
        "issued_at": ts,
        "request_hash": req_hash,
        "tool": "tools/call",
        "method": "weather/get",  # logical identifier
        "capability_hash": cap_hash,
        "capability": cap_token
    }
    
    msg_canon = canonical_json(mcp_msg_content)
    msg_sig = sign_base64(msg_canon, PRIVATE_KEY)
    
    mcp_msg_frame = mcp_msg_content.copy()
    mcp_msg_frame["sig"] = msg_sig
    
    write_vector(f"{VECTOR_DIR}/positive/mcp_message_frame.json", mcp_msg_frame)

    # MCP_RESPONSE Frame
    # First generate response payload hash
    mcp_resp = {
        "jsonrpc": "2.0",
        "id": "req-123",
        "result": {"temperature": 22}
    }
    resp_canon = canonical_json(mcp_resp)
    resp_hash = sha256_hash(resp_canon)
    
    mcp_resp_content = {
        "type": "MCP_RESPONSE",
        "protocol_version": PROTOCOL_VERSION,
        "session_id": session_id,
        "correlation_id": correlation_id,
        "peer_id": PEER_ID,  # In real flow this would be responder's ID
        "issued_at": ts + 1,
        "response_hash": resp_hash,
        "tool": "tools/call",
        "method": "weather/get",
        "result_code": "OK"
    }
    
    resp_frame_canon = canonical_json(mcp_resp_content)
    resp_sig = sign_base64(resp_frame_canon, PRIVATE_KEY)
    
    mcp_resp_frame = mcp_resp_content.copy()
    mcp_resp_frame["sig"] = resp_sig
    
    write_vector(f"{VECTOR_DIR}/positive/mcp_response_frame.json", mcp_resp_frame)
    
    # 4. Envelope (Legacy / Hello World Wrapper logic if needed, but MCP_MESSAGE is the new standard)
    # The plan lists "Envelope (Hello World)" -> envelope_tool_call.json.
    # I'll map this to the MCP_MESSAGE_FRAME concept to avoid confusion, 
    # but rename it to envelope_tool_call.json as per plan.
    write_vector(f"{VECTOR_DIR}/positive/envelope_tool_call.json", mcp_msg_frame)

def generate_negative():
    print("Generating Negative Vectors...")
    
    base_cap = {
        "v": "1",
        "iss": PEER_ID,
        "sub": "did:talos:recipient",
        "scope": "tools/call",
        "iat": 1700000000,
        "exp": 1700003600
    }
    
    def bake_cap(content, denial) -> dict:
        canon = canonical_json(content)
        sig = sign_base64(canon, PRIVATE_KEY)
        item = content.copy()
        item["sig"] = sig
        return {
            "vector_type": "capability",
            "expected_denial": denial,
            "input": item
        }

    # Expired
    exp_cap = base_cap.copy()
    exp_cap["exp"] = 1600000000 # Past
    write_vector(f"{VECTOR_DIR}/negative/capability_expired.json", bake_cap(exp_cap, "EXPIRED"))
    
    # Revoked (Needs external state to verify, but structure-wise it's a valid cap usually)
    # We'll just generate a valid cap and label it revoked for the harness to load into revocation list
    rev_cap = base_cap.copy()
    rev_cap["iat"] = 1700000001
    write_vector(f"{VECTOR_DIR}/negative/capability_revoked.json", bake_cap(rev_cap, "REVOKED"))
    
    # Wrong Sig
    wrong_sig_cap = base_cap.copy()
    # Sign it
    canon = canonical_json(wrong_sig_cap)
    sig_raw = PRIVATE_KEY.sign(canon)
    # Corrupt last byte
    bad_sig = bytearray(sig_raw)
    bad_sig[-1] ^= 0x01 
    wrong_sig_cap["sig"] = serialize_bytes(bad_sig)
    
    write_vector(f"{VECTOR_DIR}/negative/wrong_sig.json", {
        "vector_type": "capability",
        "expected_denial": "SIGNATURE_INVALID",
        "input": wrong_sig_cap
    })
    
    # Missing Request Binding
    # Generate frame without request_hash (if optional?) or with wrong one
    # The spec says "Unknown top-level fields are rejected", but omitting required fields is also bad.
    # Let's do "Corrupted request_hash"
    
    mcp_msg_content = {
        "type": "MCP_MESSAGE",
        "protocol_version": PROTOCOL_VERSION,
        "session_id": "sess-fail",
        "correlation_id": "corr-fail",
        "peer_id": PEER_ID,
        "issued_at": 1700000100,
        "request_hash": "badhash", # Wrong hash for payload
        "tool": "tools/call",
        "method": "weather/get",
        "capability_hash": "caphash",
    }
    # This vector implies the verifier checks hash vs payload. 
    # Or specifically, if the CLIENT fails to include it?
    # "Detects proxy bugs where request_hash/correlation_id is not bound"
    # Let's simulate a frame that *omits* request_hash
    frame_no_hash = mcp_msg_content.copy()
    del frame_no_hash["request_hash"]
    # If we assume schema validation happens:
    write_vector(f"{VECTOR_DIR}/negative/missing_request_binding.json", {
        "vector_type": "frame",
        "expected_denial": "INVALID_FRAME",
        "input": frame_no_hash
    })
    
    # Canonicalization: Non-canonical order
    # Python dicts preserve insertion order in modern versions, so we can force "wrong" order
    # But json.dumps(sort_keys=True) fixes it.
    # to generate BAD json, we manually construct string or use sort_keys=False
    
    # We need a frame with valid signature over CANONICAL bytes, 
    # but the FRAME ITSELF acts as input that is NOT in canonical order?
    # No, usually "canonicalization mismatch" means:
    # signer canonicalized differently than verifier. 
    # Or, the input JSON received is "messy", verifier canonicalizes it, checks signature.
    # If signature was generated over "messy" bytes, it would fail if verifier canonicalizes.
    # But if signature was generated over "clean" bytes, and message arrives "messy", 
    # verifier cleans it -> bytes match -> valid.
    #
    # The vulnerability is: signer signs NON-CANONICAL bytes.
    # So we generate a signature over non-canonical bytes.
    # Verifier (correct) will canonicalize input -> bytes mismatch -> fail.
    
    messy_content = {
        "v": "1",
        "b_field": 2,
        "a_field": 1
    }
    # Sign in messy order
    messy_json = json.dumps(messy_content, sort_keys=False, separators=(',', ':')).encode('utf-8')
    sig_messy = sign_base64(messy_json, PRIVATE_KEY)
    
    messy_obj = messy_content.copy()
    messy_obj["sig"] = sig_messy
    
    write_vector(f"{VECTOR_DIR}/negative/non_canonical_json_order.json", {
        "vector_type": "object",
        "expected_denial": "SIGNATURE_INVALID",
        "input": messy_obj
    })
    
    # Duplicate Keys
    # Standard JSON parsers dictate last-win or error.
    # We construct raw string.
    dup_json_str = '{"v": "1", "dup": "a", "dup": "b", "sig": "placeholder"}'
    # This is hard to represent in JSON vector file unless "input" is string?
    # Or we verify parser rejection.
    # Let's skip raw string generation inside JSON vector for now to avoid complexity,
    # or wrap it as a string input.
    write_vector(f"{VECTOR_DIR}/negative/duplicate_keys.json", {
        "vector_type": "raw_string",
        "expected_denial": "SIGNATURE_INVALID", # or PARSE_ERROR
        "input": dup_json_str
    })

def generate_replay_session():
    print("Generating Replay/Session Vectors...")
    
    # Replay
    # Just take the valid mcp_message_frame
    with open(f"{VECTOR_DIR}/positive/mcp_message_frame.json", "r") as f:
        valid_frame = json.load(f)
    
    write_vector(f"{VECTOR_DIR}/replay/duplicate.json", {
        "vector_type": "frame",
        "expected_denial": "REPLAY",
        "input": [valid_frame, valid_frame]
    })
    
    # Session
    # 1. First request (with cap) -> Valid
    # 2. Followup (no cap, has hash) -> Valid
    
    # We can use the valid_frame as #1 (it has capability)
    req1 = valid_frame.copy()
    
    # Req 2: Same session, new correlation, NO CAPABILITY, but CAPABILITY_HASH present
    req2_content = req1.copy()
    del req2_content["sig"]
    del req2_content["capability"]
    req2_content["correlation_id"] = "corr-consistency-check"
    req2_content["issued_at"] += 10
    
    req2_canon = canonical_json(req2_content)
    req2_sig = sign_base64(req2_canon, PRIVATE_KEY)
    
    req2 = req2_content.copy()
    req2["sig"] = req2_sig
    
    write_vector(f"{VECTOR_DIR}/session/cache_pair.json", {
        "vector_type": "flow",
        "expected_result": "ACCEPT",
        "inputs": [req1, req2]
    })
    
    # Followup without cache (implied by just sending #2 in isolation?)
    write_vector(f"{VECTOR_DIR}/session/followup_without_cache.json", {
        "vector_type": "frame",
        "expected_denial": "NO_CAPABILITY", # Verification should fail if cache miss and no cap
        "input": req2
    })

def generate_meta():
    meta = {
        "protocol_version": PROTOCOL_VERSION,
        "sig_alg": "ed25519",
        "hash_alg": "sha256",
        "canon_alg": "rfc8785",
        "keypair_seed_hex": SEED_HEX,
        "public_key_hex": PUBLIC_KEY_HEX,
        "peer_id": PEER_ID
    }
    write_vector(f"{VECTOR_DIR}/meta.json", meta)

def main():
    setup_dirs()
    generate_meta()
    generate_positive()
    generate_negative()
    generate_replay_session()
    print("Done.")

if __name__ == "__main__":
    main()
