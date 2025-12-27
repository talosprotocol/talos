import json
import os
import sys
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import base64
import hashlib

def canonical_json(obj):
    """
    RFC 8785 Canonical JSON Serialization (Minimal correct implementation for verification).
    """
    if obj is None:
        raise ValueError("Null not allowed in v1")
    if isinstance(obj, (int, float)):
        # Check for float
        if isinstance(obj, float):
             # Just strict rejection for verification script
             if not obj.is_integer():
                 raise ValueError("Float not allowed")
             return str(int(obj)).encode("utf-8")
        return str(obj).encode("utf-8")
    if isinstance(obj, bool):
        return b"true" if obj else b"false"
    if isinstance(obj, str):
        # json.dumps ensures correct escaping
        return json.dumps(obj, separators=(',', ':')).encode("utf-8")
    if isinstance(obj, (list, tuple)):
        items = [canonical_json(x) for x in obj]
        return b"[" + b",".join(items) + b"]"
    if isinstance(obj, dict):
        items = []
        for k in sorted(obj.keys()):
            val = obj[k]
            # strict: omit nulls? Spec says "omitting null fields".
            # If TS generated it, it shouldn't produce nulls.
            if val is None: 
                continue 
            encoded_k = json.dumps(k).encode("utf-8")
            encoded_v = canonical_json(val)
            items.append(encoded_k + b":" + encoded_v)
        return b"{" + b",".join(items) + b"}"
    # Fallback
    raise TypeError(f"Type {type(obj)} not supported in canonical json")

def decode_base64url(s):
    """Base64URL decode without padding requirements."""
    s = s.replace('-', '+').replace('_', '/')
    rem = len(s) % 4
    if rem:
        s += '=' * (4 - rem)
    return base64.b64decode(s)

def verify_ts_vectors():
    path = os.path.join(os.path.dirname(__file__), '../test_vectors/ts_generated/interop.json')
    if not os.path.exists(path):
        print("Skipping TS verification: Vector file not found (TS generation failed?)")
        sys.exit(1)

    with open(path, 'r') as f:
        data = json.load(f)

    pub_key_hex = data['public_key_hex']
    pub_key_bytes = bytes.fromhex(pub_key_hex)
    
    print(f"Verifying TS vectors with Public Key: {pub_key_hex[:8]}...")

    # 1. Capability
    cap = data['capability']
    print("Verifying Capability...")
    # Manually verify to ensure we use our python stack
    sig = cap.pop('sig')
    canon = canonical_json(cap)
    sig_bytes = decode_base64url(sig)
    
    # Verify using cryptography directly
    public_key = Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    try:
        public_key.verify(sig_bytes, canon)
        print("PASS: Capability Signature")
    except Exception as e:
        print(f"FAIL: Capability Signature: {e}")
        sys.exit(1)

    # 2. Frame
    frame = data['frame']
    print("Verifying Frame...")
    sig = frame.pop('sig')
    canon = canonical_json(frame)
    sig_bytes = decode_base64url(sig)

    try:
        public_key.verify(sig_bytes, canon)
        print("PASS: Frame Signature")
    except Exception as e:
        print(f"FAIL: Frame Signature: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_ts_vectors()
