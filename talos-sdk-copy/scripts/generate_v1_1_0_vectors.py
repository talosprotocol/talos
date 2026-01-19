import json
import os

from talos_sdk.canonical import canonical_json_bytes
from talos_sdk.crypto import b64u_decode, b64u_encode
from talos_sdk.session import KeyPair, SessionManager

# Fixed secrets for reproducibility (from old roundtrip_basic.json)
ALICE_ID_PRIV = b64u_decode("ycPjUCVI9ctfhqau8hlmHSDo_17XS5MV1ZujmHqMWWg")
ALICE_ID_PUB = b64u_decode("EDC4yqS9rJWoqrnmR9T24TVpX4NfqNkeoX3NDC-SwvM")
ALICE_EPH_PRIV = b64u_decode("2N4czt7AZRLm9CmTbo2FPL77rwxOnC8Aq45uDSnqbXE")

BOB_ID_PRIV = b64u_decode("YKGriHH1oHqqtWLCUfDqEBeoYG8i3298EnmZUzIy7e0")
BOB_ID_PUB = b64u_decode("E80vGn1T8vhm2dystAQ5VBKzpbXf8_zf98es-RuGZkw")
BOB_SPK_PRIV = b64u_decode("OM7eZuUYF0K0iSccFg_9doJbna0fDQNimjhYwHDQz1k")
BOB_SPK_PUB = b64u_decode("ZPLNJFKa-PyNyrhA0PD9KAd_2KMiPfzkZe9hz9e6xnc")
BOB_SPK_SIG = b64u_decode(
    "aubPCBHtdqGqq7vBOSFzLl4o5FFfO4jUaTVPtVO3mJ9Q2cYmd9SSQ7kEkwFDADLJqB2Uk66xcciuW1r4rD4lCA"
)


def get_trace_structure():
    return {
        "title": "Ratchet Golden Trace (v1.1.0 Interop)",
        "description": "Generated with JSON wire framing (Option A) and deterministic KDF schedule.",
        "version": "1.1.0",
        "alice": {
            "identity_public": b64u_encode(ALICE_ID_PUB),
            "identity_private": b64u_encode(ALICE_ID_PRIV),
            "ephemeral_private": b64u_encode(ALICE_EPH_PRIV),
        },
        "bob": {
            "identity_public": b64u_encode(BOB_ID_PUB),
            "identity_private": b64u_encode(BOB_ID_PRIV),
            "prekey_bundle": {
                "identity_key": b64u_encode(BOB_ID_PUB),
                "signed_prekey": b64u_encode(BOB_SPK_PUB),
                "prekey_signature": b64u_encode(BOB_SPK_SIG),
                "one_time_prekey": None,
            },
            "bundle_secrets": {"signed_prekey_private": b64u_encode(BOB_SPK_PRIV)},
        },
        "steps": [],
    }


def main():
    import talos_sdk.session as session_mod

    # 1. Setup Bob
    bob_id = KeyPair(private_key=BOB_ID_PRIV, public_key=BOB_ID_PUB, key_type="ed25519")
    bob_mgr = SessionManager(bob_id)
    # Inject fixed SPK
    bob_mgr._signed_prekey = KeyPair(
        private_key=BOB_SPK_PRIV, public_key=BOB_SPK_PUB, key_type="x25519"
    )
    bob_mgr._prekey_signature = BOB_SPK_SIG

    # 2. Setup Alice
    alice_id = KeyPair(
        private_key=ALICE_ID_PRIV, public_key=ALICE_ID_PUB, key_type="ed25519"
    )
    alice_mgr = SessionManager(alice_id)

    # Trace data
    trace = get_trace_structure()

    # Mocking ephemeral generation for Alice initiation
    orig_gen = session_mod.generate_encryption_keypair

    # Step 1: Alice sends
    def mock_alice_eph():
        from cryptography.hazmat.primitives.asymmetric import x25519
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        priv = x25519.X25519PrivateKey.from_private_bytes(ALICE_EPH_PRIV)
        pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        return KeyPair(private_key=ALICE_EPH_PRIV, public_key=pub, key_type="x25519")

    session_mod.generate_encryption_keypair = mock_alice_eph
    alice_session = alice_mgr.create_session_as_initiator(
        "did:bob", bob_mgr.get_prekey_bundle()
    )
    session_mod.generate_encryption_keypair = orig_gen

    plaintext = b"Hello Bob"
    wire_bytes = alice_session.encrypt(plaintext)
    envelope = json.loads(wire_bytes)

    trace["steps"].append(
        {
            "step": 1,
            "action": "encrypt",
            "actor": "alice",
            "description": "Alice sends first message (v1.1.0)",
            "plaintext": b64u_encode(plaintext),
            "header": envelope["header"],
            "nonce": envelope["nonce"],
            "ciphertext": envelope["ciphertext"],
            "wire_message_b64u": b64u_encode(wire_bytes),
            "aad": b64u_encode(canonical_json_bytes(envelope["header"])),
        }
    )

    # Step 2: Bob receives
    bob_session = bob_mgr.create_session_as_responder(
        "did:alice", b64u_decode(envelope["header"]["dh"])
    )
    decrypted = bob_session.decrypt(wire_bytes)
    assert decrypted == plaintext

    trace["steps"].append(
        {
            "step": 2,
            "action": "decrypt",
            "actor": "bob",
            "description": "Bob receives first message",
            "wire_message_b64u": b64u_encode(wire_bytes),
            "expected_plaintext": b64u_encode(plaintext),
        }
    )

    # Step 3: Bob replies
    BOB_RATCHET_PRIV = b"\x11" * 32

    def mock_bob_ratchet():
        from cryptography.hazmat.primitives.asymmetric import x25519
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        priv = x25519.X25519PrivateKey.from_private_bytes(BOB_RATCHET_PRIV)
        pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        return KeyPair(private_key=BOB_RATCHET_PRIV, public_key=pub, key_type="x25519")

    session_mod.generate_encryption_keypair = mock_bob_ratchet
    reply_pt = b"Hi Alice"
    reply_wire = bob_session.encrypt(reply_pt)
    session_mod.generate_encryption_keypair = orig_gen

    envelope_reply = json.loads(reply_wire)
    trace["steps"].append(
        {
            "step": 3,
            "action": "encrypt",
            "actor": "bob",
            "description": "Bob replies",
            "plaintext": b64u_encode(reply_pt),
            "header": envelope_reply["header"],
            "nonce": envelope_reply["nonce"],
            "ciphertext": envelope_reply["ciphertext"],
            "wire_message_b64u": b64u_encode(reply_wire),
            "aad": b64u_encode(canonical_json_bytes(envelope_reply["header"])),
            "ratchet_priv": b64u_encode(BOB_RATCHET_PRIV),
        }
    )

    # Step 4: Alice receives
    decrypted_reply = alice_session.decrypt(reply_wire)
    assert decrypted_reply == reply_pt
    trace["steps"].append(
        {
            "step": 4,
            "action": "decrypt",
            "actor": "alice",
            "description": "Alice receives reply",
            "wire_message_b64u": b64u_encode(reply_wire),
            "expected_plaintext": b64u_encode(reply_pt),
        }
    )

    # Output to file
    out_path = "../talos-contracts/test_vectors/sdk/ratchet/v1_1_0_roundtrip.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(trace, f, indent=2)
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
