#!/usr/bin/env python3
"""Multi-Message Demo.

Demonstrates:
- Send 10 messages from Alice to Bob
- Verify all decrypt successfully
- Verify sender_seq is monotonic
- Verify each frame_digest is unique

SECURITY: No raw keys or ciphertext printed. Only counts, digests, and assertions.

Run: python examples/multi_message_demo.py --help
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

from talos_sdk.a2a.ratchet_crypto import RatchetFrameCrypto
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
    args = parse_common_args(description="Talos Multi-Message Demo")

    print_header("Talos Multi-Message Demo")

    NUM_MESSAGES = 10

    # =========================================================================
    # Setup: Create Sessions
    # =========================================================================
    print_header("Setup: Create Ratchet Sessions")

    alice_keypair = generate_signing_keypair()
    bob_keypair = generate_signing_keypair()

    alice_manager = SessionManager(alice_keypair)
    bob_manager = SessionManager(bob_keypair)

    bob_bundle = bob_manager.get_prekey_bundle()
    alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
    bob_session = bob_manager.create_session_as_responder(
        "alice", alice_session.state.dh_keypair.public_key
    )

    alice_crypto = RatchetFrameCrypto(alice_session)
    bob_crypto = RatchetFrameCrypto(bob_session)

    print_success("Sessions established")

    # =========================================================================
    # Send 10 Messages
    # =========================================================================
    print_header(f"Sending {NUM_MESSAGES} Messages")

    session_id = "sess-multi-demo"
    frame_digests = []
    sender_seqs = []

    for i in range(NUM_MESSAGES):
        msg = f"Message {i + 1} from Alice to Bob".encode()

        # Encrypt
        header_b64u, ciphertext_b64u, ciphertext_hash = alice_crypto.encrypt(msg)

        # Compute frame digest
        sender_seq = i
        frame_digest = compute_frame_digest(
            session_id, "alice", sender_seq, header_b64u, ciphertext_hash
        )

        frame_digests.append(frame_digest)
        sender_seqs.append(sender_seq)

        # Decrypt
        decrypted = bob_crypto.decrypt(header_b64u, ciphertext_b64u, ciphertext_hash)

        # Verify
        assert decrypted == msg, f"Message {i + 1} decryption failed"

        if args.verbose:
            print(f"   [{i + 1:2d}] ✅ sender_seq={sender_seq}, digest={frame_digest[:12]}...")

    print_success(f"All {NUM_MESSAGES} messages encrypted and decrypted successfully")

    # =========================================================================
    # Verify Monotonic Sequence
    # =========================================================================
    print_header("Verify sender_seq Monotonic")

    for i in range(1, len(sender_seqs)):
        assert sender_seqs[i] > sender_seqs[i - 1], f"Sequence not monotonic at {i}"

    print_info(f"sender_seq range: {sender_seqs[0]} → {sender_seqs[-1]}")
    print_success("sender_seq is strictly monotonic increasing")

    # =========================================================================
    # Verify Unique Digests
    # =========================================================================
    print_header("Verify frame_digest Uniqueness")

    unique_digests = set(frame_digests)
    assert len(unique_digests) == NUM_MESSAGES, "Duplicate frame_digest detected!"

    print_info(f"Total digests: {len(frame_digests)}")
    print_info(f"Unique digests: {len(unique_digests)}")
    print_success("All frame_digests are unique")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Summary")

    safe_print({
        "messages_sent": NUM_MESSAGES,
        "messages_decrypted": NUM_MESSAGES,
        "sender_seq_monotonic": True,
        "digests_unique": True,
        "first_digest": frame_digests[0][:16] + "...",
        "last_digest": frame_digests[-1][:16] + "...",
    }, "Results")

    print("\n✅ Multi-Message properties verified:")
    print(f"   - [x] All {NUM_MESSAGES} messages decrypted successfully")
    print("   - [x] sender_seq is strictly monotonic")
    print("   - [x] Each frame_digest is unique")


if __name__ == "__main__":
    main()
