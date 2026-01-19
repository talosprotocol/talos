#!/usr/bin/env python3
"""A2A Messaging Example.

Demonstrates secure Agent-to-Agent communication using:
- Mode 1: Transport-only (Phase 10.2) - frames, digests, counts
- Mode 2: Ratchet Binding (Phase 10.3) - Double Ratchet encryption

Run: python examples/a2a_messaging.py --help
"""

import hashlib
import sys
from pathlib import Path

# Add examples dir to path for _common import
sys.path.insert(0, str(Path(__file__).parent))
# Add src for SDK imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from _common import (
    parse_common_args,
    safe_print,
    print_header,
    print_success,
    print_info,
    print_warning,
)

from talos_sdk.a2a.ratchet_crypto import RatchetFrameCrypto, NONCE_LEN
from talos_sdk.a2a.models import GroupResponse
from talos_sdk.canonical import canonical_json_bytes
from talos_sdk.crypto import generate_signing_keypair
from talos_sdk.session import SessionManager


def compute_frame_digest(
    session_id: str,
    sender_id: str,
    sender_seq: int,
    header_b64u: str,
    ciphertext_hash: str,
) -> str:
    """Compute frame_digest per Phase 10 LOCKED SPEC."""
    preimage = {
        "schema_id": "talos.a2a.encrypted_frame",
        "schema_version": "v1",
        "session_id": session_id,
        "sender_id": sender_id,
        "sender_seq": sender_seq,
        "header_b64u": header_b64u,
        "ciphertext_hash": ciphertext_hash,
    }
    return hashlib.sha256(canonical_json_bytes(preimage)).hexdigest()


def main():
    args = parse_common_args(description="Talos A2A Messaging Example")

    print_header("Talos A2A Messaging Example")

    # =========================================================================
    # Setup: Create identities (using Ed25519 for signing)
    # =========================================================================
    print_info("Creating agent identities...")

    alice_keypair = generate_signing_keypair()
    bob_keypair = generate_signing_keypair()

    alice_manager = SessionManager(alice_keypair)
    bob_manager = SessionManager(bob_keypair)

    print(f"   Alice ID: alice-agent")
    print(f"   Bob ID:   bob-agent")

    # =========================================================================
    # Key Exchange: X3DH
    # =========================================================================
    print_header("Phase 1: Key Exchange (X3DH)")

    bob_bundle = bob_manager.get_prekey_bundle()
    print_info("Bob publishes prekey bundle")
    print(f"   Identity key:  {bob_bundle.identity_key.hex()[:16]}...")
    print(f"   Signed prekey: {bob_bundle.signed_prekey.hex()[:16]}...")

    # Alice initiates session
    alice_session = alice_manager.create_session_as_initiator("bob-agent", bob_bundle)
    print_success("Alice created session as initiator")

    # Bob accepts session
    bob_session = bob_manager.create_session_as_responder(
        "alice-agent",
        alice_session.state.dh_keypair.public_key,
    )
    print_success("Bob created session as responder")

    # =========================================================================
    # Mode 1: Transport-Only (Phase 10.2)
    # =========================================================================
    print_header("Mode 1: Transport-Only (Phase 10.2)")
    print_info("This mode shows frame metadata without encryption details.")
    print_warning("In production, use Mode 2 with RatchetFrameCrypto for E2E encryption.")

    session_id = "sess-example-001"
    sender_seq = 0

    # Simulate frame metadata (no actual encryption in this mode)
    frame_metadata = {
        "session_id": session_id,
        "sender_id": "alice-agent",
        "sender_seq": sender_seq,
        "frame_size": 256,  # Example size
        "status": "would_be_sent",
    }
    safe_print(frame_metadata, "Transport-Only Frame Metadata")

    # =========================================================================
    # Mode 2: Ratchet Binding (Phase 10.3)
    # =========================================================================
    print_header("Mode 2: Ratchet Binding (Phase 10.3)")

    # Create crypto adapters
    alice_crypto = RatchetFrameCrypto(alice_session)
    bob_crypto = RatchetFrameCrypto(bob_session)

    print_info("RatchetFrameCrypto adapters created")

    # --- Alice sends message to Bob ---
    print_header("Alice → Bob: Encrypted Message")

    plaintext = b"Hello Bob! This is a secure A2A message with forward secrecy."
    print_info(f"Plaintext: {plaintext.decode()}")

    # Encrypt
    header_b64u, ciphertext_b64u, ciphertext_hash = alice_crypto.encrypt(plaintext)
    frame_digest = compute_frame_digest(
        session_id, "alice-agent", sender_seq, header_b64u, ciphertext_hash
    )

    # Safe print - only counts and digests, no raw ciphertext
    safe_print({
        "session_id": session_id,
        "sender_id": "alice-agent",
        "sender_seq": sender_seq,
        "ciphertext_hash": ciphertext_hash[:16] + "...",
        "frame_digest": frame_digest[:16] + "...",
    }, "Encrypted Frame (Metadata Only)")

    # --- Bob decrypts ---
    print_header("Bob Receives & Decrypts")

    decrypted = bob_crypto.decrypt(header_b64u, ciphertext_b64u, ciphertext_hash)
    print_success(f"Decrypted: {decrypted.decode()}")

    if decrypted == plaintext:
        print_success("Plaintext matches original!")

    # --- Bob replies ---
    print_header("Bob → Alice: Reply Message")

    reply = b"Hi Alice! Got your message. Double Ratchet working perfectly!"
    print_info(f"Reply: {reply.decode()}")

    h, c, ch = bob_crypto.encrypt(reply)
    fd = compute_frame_digest(session_id, "bob-agent", 0, h, ch)

    safe_print({
        "sender_id": "bob-agent",
        "sender_seq": 0,
        "frame_digest": fd[:16] + "...",
    }, "Reply Frame (Metadata Only)")

    decrypted_reply = alice_crypto.decrypt(h, c, ch)
    print_success(f"Alice decrypted: {decrypted_reply.decode()}")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Security Properties Demonstrated")

    print("🛡️  Forward Secrecy:")
    print("   - Each message uses a unique message key")
    print("   - Keys are deleted after use")

    print("\n🔄 Break-in Recovery:")
    print("   - DH ratchet generates fresh keys automatically")

    print("\n🔐 Frame Integrity:")
    print("   - ciphertext_hash: SHA-256 of ciphertext (not nonce)")
    print("   - frame_digest: SHA-256 of canonical preimage")

    print_header("Demo Complete!")
    print(f"   Alice messages sent: {alice_session.messages_sent}")
    print(f"   Bob messages sent:   {bob_session.messages_sent}")


if __name__ == "__main__":
    main()
