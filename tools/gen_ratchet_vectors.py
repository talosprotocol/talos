
import json
import base64
import sys
import os
from pathlib import Path


# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import hashlib
from src.core.session import SessionManager, MessageHeader
from src.core.crypto import generate_signing_keypair, generate_encryption_keypair
def b64u(b: bytes) -> str:
    """Base64URL no padding."""
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def b64u_decode(s: str) -> bytes:
    """Base64URL no padding decode."""
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)

def make_did(public_key: bytes) -> str:
    """Generate DID from public key (replicates src.core.did logic)."""
    pubkey_hash = hashlib.sha256(public_key).hexdigest()[:32]
    return f"did:talos:{pubkey_hash}"


def generate_out_of_order_trace(out_dir: Path):
    print("Generating Ratchet Out-of-Order Trace...")
    
    # 1. Setup Same Identities
    alice_identity = generate_signing_keypair()
    bob_identity = generate_signing_keypair()
    
    alice_mgr = SessionManager(alice_identity)
    bob_mgr = SessionManager(bob_identity)
    
    alice_did = make_did(alice_identity.public_key)
    bob_did = make_did(bob_identity.public_key)
    
    # X3DH
    bob_bundle = bob_mgr.get_prekey_bundle()
    alice_session = alice_mgr.create_session_as_initiator(bob_did, bob_bundle)
    
    # Trace with explicit keys to ensure determinism if we want to run spec validation later
    trace = {
        "title": "Ratchet Out-of-Order Trace",
        "description": "Tests handling of skipped message keys.",
        "alice": {
            "identity_public": b64u(alice_identity.public_key),
            "identity_private": b64u(alice_identity.private_key),
            "ephemeral_private": b64u(alice_session.state.dh_keypair.private_key)
        },
        "bob": {
            "identity_public": b64u(bob_identity.public_key),
            "identity_private": b64u(bob_identity.private_key),
            "prekey_bundle": bob_bundle.to_dict(),
            "bundle_secrets": {
                "signed_prekey_private": b64u(bob_mgr._signed_prekey.private_key)
            }
        },
        "steps": []
    }
    
    # Helper for parsing
    def parse_msg(m):
        header_len = int.from_bytes(m[:2], "big")
        header_bytes = m[2:2+header_len]
        payload = m[2+header_len:]
        nonce = payload[:12]
        ct = payload[12:]
        header_json = json.loads(header_bytes)
        dh_b64u = header_json["dh"]
        header_obj = {"dh": dh_b64u, "pn": header_json["pn"], "n": header_json["n"]}
        aad_b64u = b64u(header_bytes)
        return header_obj, b64u(nonce), b64u(ct), aad_b64u, m

    # 1. Alice sends Msg1 (M1)
    pt1 = b"Message 1"
    m1 = alice_session.encrypt(pt1)
    h1, n1, c1, a1, wire_m1 = parse_msg(m1)
    
    trace["steps"].append({
        "step": 1, "action": "encrypt", "actor": "alice", "description": "Alice sends M1",
        "plaintext": b64u(pt1), "header": h1, "nonce": n1, "ciphertext": c1, "aad": a1, "wire_message": b64u(wire_m1)
    })
    
    # 2. Alice sends Msg2 (M2) - DELAYED
    pt2 = b"Message 2"
    m2 = alice_session.encrypt(pt2)
    h2, n2, c2, a2, wire_m2 = parse_msg(m2)
    
    trace["steps"].append({
        "step": 2, "action": "encrypt", "actor": "alice", "description": "Alice sends M2 (will arrive late)",
        "plaintext": b64u(pt2), "header": h2, "nonce": n2, "ciphertext": c2, "aad": a2
    })
    
    # 3. Alice sends Msg3 (M3)
    pt3 = b"Message 3"
    m3 = alice_session.encrypt(pt3)
    h3, n3, c3, a3, wire_m3 = parse_msg(m3)
    
    trace["steps"].append({
        "step": 3, "action": "encrypt", "actor": "alice", "description": "Alice sends M3",
        "plaintext": b64u(pt3), "header": h3, "nonce": n3, "ciphertext": c3, "aad": a3
    })
    
    # 4. Bob receives M1 (Normal)
    header1_bytes_std = m1[2:2+int.from_bytes(m1[:2], "big")]
    header1_json_std = json.loads(header1_bytes_std)
    alice_ephemeral = b64u_decode(header1_json_std["dh"])
    bob_session = bob_mgr.create_session_as_responder(alice_did, alice_ephemeral, alice_identity.public_key)
    
    dec1 = bob_session.decrypt(m1)
    assert dec1 == pt1
    
    trace["steps"].append({
        "step": 4, "action": "decrypt", "actor": "bob", "description": "Bob receives M1",
        "ciphertext": c1, "header": h1, "nonce": n1, "aad": a1, "expected_plaintext": b64u(dec1)
    })
    
    # 5. Bob receives M3 (M2 skipped)
    dec3 = bob_session.decrypt(m3)
    assert dec3 == pt3
    
    trace["steps"].append({
        "step": 5, "action": "decrypt", "actor": "bob", "description": "Bob receives M3 (skipping M2)",
        "ciphertext": c3, "header": h3, "nonce": n3, "aad": a3, "expected_plaintext": b64u(dec3)
    })
    
    # 6. Bob receives M2 (From skipped keys)
    dec2 = bob_session.decrypt(m2)
    assert dec2 == pt2
    
    trace["steps"].append({
        "step": 6, "action": "decrypt", "actor": "bob", "description": "Bob receives M2 (out-of-order)",
        "ciphertext": c2, "header": h2, "nonce": n2, "aad": a2, "expected_plaintext": b64u(dec2)
    })
    
    with open(out_dir / "out_of_order.json", "w") as f:
        json.dump(trace, f, indent=2)
    print(f"Generated {out_dir / 'out_of_order.json'}")


def main():
    print("Generating Ratchet Golden Trace (Reference)...")
    
    # 1. Setup Identities
    alice_identity = generate_signing_keypair()
    bob_identity = generate_signing_keypair()
    
    alice_mgr = SessionManager(alice_identity)
    bob_mgr = SessionManager(bob_identity)
    
    alice_did = make_did(alice_identity.public_key)
    bob_did = make_did(bob_identity.public_key)

    # 2. X3DH Setup
    bob_bundle = bob_mgr.get_prekey_bundle()
    
    # Alice initiates
    alice_session = alice_mgr.create_session_as_initiator(bob_did, bob_bundle)
    
    # Trace Object
    trace = {
        "title": "Ratchet Golden Trace (Reference)",
        "description": "Trace generated from src/core/session.py with normalized encoding.",
        "alice": {
            "identity_public": b64u(alice_identity.public_key),
            "identity_private": b64u(alice_identity.private_key),
            "ephemeral_private": b64u(alice_session.state.dh_keypair.private_key)
        },

        "bob": {
            "identity_public": b64u(bob_identity.public_key),
            "identity_private": b64u(bob_identity.private_key),
            "prekey_bundle": {
                "identity_key": b64u(bob_bundle.identity_key),
                "signed_prekey": b64u(bob_bundle.signed_prekey),
                "prekey_signature": b64u(bob_bundle.prekey_signature),
                "one_time_prekey": b64u(bob_bundle.one_time_prekey) if bob_bundle.one_time_prekey else None
            },
            "bundle_secrets": {
                "signed_prekey_private": b64u(bob_mgr._signed_prekey.private_key)
            }
        },
        "steps": []
    }

    # Helper to parse talos-encoded message
    def parse_message(msg_bytes):
        # Format: 2-byte len | header_json | nonce (12) | ciphertext
        header_len = int.from_bytes(msg_bytes[:2], "big")
        header_bytes = msg_bytes[2:2+header_len]
        payload = msg_bytes[2+header_len:]
        nonce = payload[:12]
        ciphertext = payload[12:]
        
        header_json = json.loads(header_bytes)
        
        # header_json["dh"] is now URL-safe from session.py
        dh_b64u = header_json["dh"]
        
        header_obj = {
            "dh": dh_b64u,
            "pn": header_json["pn"],
            "n": header_json["n"]
        }
        
        # AAD for reference impl is the raw header bytes
        aad_b64u = b64u(header_bytes)
        
        return header_obj, b64u(nonce), b64u(ciphertext), aad_b64u

    # Step 1: Alice -> Bob "Hello"
    msg1_pt = b"Hello Bob"
    msg1_full = alice_session.encrypt(msg1_pt)
    
    header1, nonce1, ct1, aad1 = parse_message(msg1_full)
    
    trace["steps"].append({
        "step": 1,
        "action": "encrypt",
        "actor": "alice",
        "description": "Alice sends first message (X3DH implicit)",
        "plaintext": b64u(msg1_pt),
        "header": header1,
        "nonce": nonce1,
        "ciphertext": ct1,
        "aad": aad1
    })

    # Bob Receive
    # Manually parse to get initial DH for session creation
    header1_bytes_std = msg1_full[2:2+int.from_bytes(msg1_full[:2], "big")]
    header1_json_std = json.loads(header1_bytes_std)
    alice_ephemeral = b64u_decode(header1_json_std["dh"])
    
    bob_session = bob_mgr.create_session_as_responder(alice_did, alice_ephemeral, alice_identity.public_key)
    dec1 = bob_session.decrypt(msg1_full)
    assert dec1 == msg1_pt
    
    trace["steps"].append({
        "step": 2,
        "action": "decrypt",
        "actor": "bob",
        "description": "Bob receives first message",
        "ciphertext": ct1, # For matching
        "header": header1,
        "nonce": nonce1,
        "aad": aad1,
        "expected_plaintext": b64u(dec1)
    })
    
    # Step 2: Bob -> Alice "Hi Alice"
    msg2_pt = b"Hi Alice"
    msg2_full = bob_session.encrypt(msg2_pt)
    header2, nonce2, ct2, aad2 = parse_message(msg2_full)
    
    trace["steps"].append({
        "step": 3,
        "action": "encrypt",
        "actor": "bob",
        "description": "Bob replies (Ratchet turn)",
        "plaintext": b64u(msg2_pt),
        "header": header2,
        "nonce": nonce2,
        "ciphertext": ct2,
        "aad": aad2,
        "ratchet_priv": b64u(bob_session.state.dh_keypair.private_key)
    })
    
    dec2 = alice_session.decrypt(msg2_full)
    assert dec2 == msg2_pt
    
    trace["steps"].append({
        "step": 4,
        "action": "decrypt",
        "actor": "alice",
        "description": "Alice receives reply",
        "ciphertext": ct2,
        "header": header2,
        "nonce": nonce2,
        "aad": aad2,
        "expected_plaintext": b64u(dec2)
    })
    
    # Save
    out_dir = Path("deploy/repos/talos-contracts/test_vectors/sdk/ratchet")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "roundtrip_basic.json", "w") as f:
        json.dump(trace, f, indent=2)
        
    print(f"Generated {out_dir / 'roundtrip_basic.json'}")

    # GENERATE OUT OF ORDER
    generate_out_of_order_trace(out_dir)
    
    # GENERATE MAX SKIP
    generate_max_skip_trace(out_dir)

def generate_max_skip_trace(out_dir: Path):
    print("Generating Ratchet Max Skip Trace...")
    
    # Identical setup
    alice_identity = generate_signing_keypair()
    bob_identity = generate_signing_keypair()
    alice_mgr = SessionManager(alice_identity)
    bob_mgr = SessionManager(bob_identity)
    alice_did = make_did(alice_identity.public_key)
    bob_did = make_did(bob_identity.public_key)
    bob_bundle = bob_mgr.get_prekey_bundle()
    alice_session = alice_mgr.create_session_as_initiator(bob_did, bob_bundle)
    
    trace = {
        "title": "Ratchet Max Skip Trace",
        "description": "Tests rejection of too many skipped messages (>1000).",
        "expected_error": {
            "message_contains": "Too many skipped messages"
        },
        "alice": {
            "identity_public": b64u(alice_identity.public_key),
            "identity_private": b64u(alice_identity.private_key),
            "ephemeral_private": b64u(alice_session.state.dh_keypair.private_key)
        },
        "bob": {
            "identity_public": b64u(bob_identity.public_key),
            "identity_private": b64u(bob_identity.private_key),
            "prekey_bundle": bob_bundle.to_dict(),
            "bundle_secrets": {
                "signed_prekey_private": b64u(bob_mgr._signed_prekey.private_key)
            }
        },
        "steps": []
    }
    
    # Helper for parsing
    def parse_msg(m):
        header_len = int.from_bytes(m[:2], "big")
        header_bytes = m[2:2+header_len]
        payload = m[2+header_len:]
        nonce = payload[:12]
        ct = payload[12:]
        header_json = json.loads(header_bytes)
        dh_b64u = header_json["dh"]
        header_obj = {"dh": dh_b64u, "pn": header_json["pn"], "n": header_json["n"]}
        aad_b64u = b64u(header_bytes)
        return header_obj, b64u(nonce), b64u(ct), aad_b64u, b64u(m)

    # 1. Alice sends Msg1
    pt1 = b"Message 1"
    m1 = alice_session.encrypt(pt1)
    h1, n1, c1, a1, wire_m1 = parse_msg(m1)
    
    trace["steps"].append({
        "step": 1, "action": "encrypt", "actor": "alice", "description": "Alice sends M1",
        "plaintext": b64u(pt1), "header": h1, "nonce": n1, "ciphertext": c1, "aad": a1, "wire_message": wire_m1
    })
    
    # 2. Alice sends 1002 messages (M2..M1003)
    # 1001 skips allows?
    # recv_count=1 (after M1).
    # If we receive n=1002 (M1003). Skips M2(n=1)...M1002(n=1001). Total 1001 skips.
    # 1 + 1000 < 1002 => 1001 < 1002 => True (Error).
    
    # We loop Alice 1001 times to get to M1002?
    # No, we need M1003.
    # M1 is n=0.
    # We want n=1002.
    
    last_msg_full = None
    last_pt = b"Message 1003"
    
    for i in range(1002):
        # Encrypt intermediate messages to advance state
        if i == 1001: # The last one (n=1002)
             last_msg_full = alice_session.encrypt(last_pt)
        else:
             alice_session.encrypt(f"Msg {i}".encode())
             
    # Add step for M1003
    h_last, n_last, c_last, a_last, wire_last = parse_msg(last_msg_full)
    
    trace["steps"].append({
        "step": 2, "action": "encrypt", "actor": "alice", "description": "Alice sends M1003 (skipping >1000)",
        "plaintext": b64u(last_pt), "header": h_last, "nonce": n_last, "ciphertext": c_last, "aad": a_last, "wire_message": wire_last
    })
    
    # 3. Bob Decrypt M1
    header1_bytes_std = m1[2:2+int.from_bytes(m1[:2], "big")]
    header1_json_std = json.loads(header1_bytes_std)
    alice_ephemeral = b64u_decode(header1_json_std["dh"])
    bob_session = bob_mgr.create_session_as_responder(alice_did, alice_ephemeral, alice_identity.public_key)
    
    dec1 = bob_session.decrypt(m1)
    assert dec1 == pt1
    
    trace["steps"].append({
        "step": 3, "action": "decrypt", "actor": "bob", "description": "Bob receives M1",
        "ciphertext": c1, "header": h1, "nonce": n1, "aad": a1, "expected_plaintext": b64u(dec1)
    })
    
    # 4. Bob Decrypt M1003 -> Should Fail
    # For generation, we assert it FAILS here?
    try:
        bob_session.decrypt(last_msg_full)
        print("WARNING: Max skip generation failed - decrypt succeeded unexpectedly")
    except Exception as e:
        # Expected
        pass
        
    trace["steps"].append({
        "step": 4, "action": "decrypt", "actor": "bob", "description": "Bob receives M1003 (should fail)",
        "ciphertext": c_last, "header": h_last, "nonce": n_last, "aad": a_last, "expected_plaintext": b64u(last_pt)
    })
    
    with open(out_dir / "max_skip.json", "w") as f:
        json.dump(trace, f, indent=2)
    print(f"Generated {out_dir / 'max_skip.json'}")

if __name__ == "__main__":
    main()
