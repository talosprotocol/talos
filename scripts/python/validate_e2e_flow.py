import sys
import json
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Spec-compliant Canonical JSON (Embedded for reference validation)
def canonical_json(obj):
    if obj is None: raise ValueError("Null not allowed in v1")
    if isinstance(obj, (int, float)):
        if isinstance(obj, float):
             if not obj.is_integer(): raise ValueError("Float not allowed")
             return str(int(obj)).encode("utf-8")
        return str(obj).encode("utf-8")
    if isinstance(obj, bool): return b"true" if obj else b"false"
    if isinstance(obj, str): return json.dumps(obj, separators=(',', ':')).encode("utf-8")
    if isinstance(obj, (list, tuple)):
        items = [canonical_json(x) for x in obj]
        return b"[" + b",".join(items) + b"]"
    if isinstance(obj, dict):
        items = []
        for k in sorted(obj.keys()):
            val = obj[k]
            if val is None: continue 
            encoded_k = json.dumps(k).encode("utf-8")
            encoded_v = canonical_json(val)
            items.append(encoded_k + b":" + encoded_v)
        return b"{" + b",".join(items) + b"}"
    raise TypeError(f"Type {type(obj)} not supported in canonical json")

def decode_base64url(s):
    s = s.replace('-', '+').replace('_', '/')
    rem = len(s) % 4
    if rem: s += '=' * (4 - rem)
    return base64.b64decode(s)

def main():
    print("Reading from stdin...", file=sys.stderr)
    input_data = sys.stdin.read()
    if not input_data:
        print("No input data", file=sys.stderr)
        sys.exit(1)
        
    try:
        data = json.loads(input_data)
        request = data['request']
        frame = data['frame']
        pub_key_hex = data['public_key_hex']
    except Exception as e:
        print(f"Invalid input format: {e}", file=sys.stderr)
        sys.exit(1)
        
    pub_key_bytes = bytes.fromhex(pub_key_hex)
    public_key = Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    
    print(f"Validating Frame from Agent {frame.get('peer_id')}...", file=sys.stderr)
    
    # 1. Verify Frame Signature (Authentication)
    try:
        sig = frame.pop('sig')
        canon_frame = canonical_json(frame)
        sig_bytes = decode_base64url(sig)
        public_key.verify(sig_bytes, canon_frame)
        print("PASS: Frame Signature Verified", file=sys.stderr)
    except Exception as e:
        print(f"FAIL: Frame Signature: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 2. Verify Request Binding (Integrity)
    request_hash_hex = frame['request_hash']
    # Canonicalize original request
    canon_request = canonical_json(request)
    computed_hash = hashlib.sha256(canon_request).hexdigest()
    
    if computed_hash != request_hash_hex:
        print(f"FAIL: Request Binding Hash Mismatch!", file=sys.stderr)
        print(f"Expected: {request_hash_hex}", file=sys.stderr)
        print(f"Computed: {computed_hash}", file=sys.stderr)
        sys.exit(1)
    else:
        print("PASS: Request Binding Verified", file=sys.stderr)
        
    # 3. Verify Capability (Authorization)
    capability = frame.get('capability')
    if not capability:
         print("FAIL: No capability in frame", file=sys.stderr)
         sys.exit(1)
         
    try:
        cap_sig = capability.pop('sig')
        canon_cap = canonical_json(capability)
        cap_sig_bytes = decode_base64url(cap_sig)
        public_key.verify(cap_sig_bytes, canon_cap) # Self-signed check
        print("PASS: Capability Signature Verified", file=sys.stderr)
    except Exception as e:
        print(f"FAIL: Capability Signature: {e}", file=sys.stderr)
        sys.exit(1)

    print("SUCCESS: E2E Validation Passed")

if __name__ == "__main__":
    main()
