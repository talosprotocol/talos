#!/usr/bin/env python3
"""Session Persistence Demo.

Demonstrates saving and restoring Double Ratchet session state:
- Serialize ratchet state securely
- Store in temp directory with restrictive permissions
- Restore both Alice and Bob sessions
- Verify message sequence continuity

SECURITY: Ratchet state is stored in a temp directory with mode 0o700.
This is for demo purposes only - production should use encrypted storage.

Run: python examples/session_persistence_demo.py --help
"""

import hashlib
import json
import os
import sys
import tempfile
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

from talos_sdk.crypto import generate_signing_keypair
from talos_sdk.session import SessionManager, Session


def main():
    args = parse_common_args(description="Talos Session Persistence Demo")

    print_header("Talos Session Persistence Demo")
    print_warning("State files stored in temp directory for demo only.")
    print_warning("Production should use encrypted at-rest storage.")

    # =========================================================================
    # Step 1: Create Original Sessions
    # =========================================================================
    print_header("Step 1: Create Original Sessions")

    # Alice and Bob identities
    alice_keypair = generate_signing_keypair()
    bob_keypair = generate_signing_keypair()

    alice_manager = SessionManager(alice_keypair)
    bob_manager = SessionManager(bob_keypair)

    # X3DH key exchange
    bob_bundle = bob_manager.get_prekey_bundle()
    alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
    bob_session = bob_manager.create_session_as_responder(
        "alice", alice_session.state.dh_keypair.public_key
    )

    print_info(f"Alice messages sent: {alice_session.messages_sent}")
    print_info(f"Bob messages sent: {bob_session.messages_sent}")
    print_success("Sessions created")

    # =========================================================================
    # Step 2: Exchange Initial Messages
    # =========================================================================
    print_header("Step 2: Exchange Messages (Pre-Persist)")

    msg1 = b"Hello Bob, this is message 1"
    ct1 = alice_session.encrypt(msg1)
    pt1 = bob_session.decrypt(ct1)
    print_info(f"Alice → Bob: {msg1.decode()}")
    assert pt1 == msg1

    msg2 = b"Hi Alice, got message 1"
    ct2 = bob_session.encrypt(msg2)
    pt2 = alice_session.decrypt(ct2)
    print_info(f"Bob → Alice: {msg2.decode()}")
    assert pt2 == msg2

    print_info(f"Alice msgs sent: {alice_session.messages_sent}, received: {alice_session.messages_received}")
    print_info(f"Bob msgs sent: {bob_session.messages_sent}, received: {bob_session.messages_received}")

    # =========================================================================
    # Step 3: Persist State to Temp Directory
    # =========================================================================
    print_header("Step 3: Persist State")

    # Create temp directory with restrictive permissions
    temp_dir = tempfile.mkdtemp(prefix="talos_session_")
    os.chmod(temp_dir, 0o700)

    alice_state_path = Path(temp_dir) / "alice_session.json"
    bob_state_path = Path(temp_dir) / "bob_session.json"

    # Serialize sessions using to_dict
    alice_state = json.dumps(alice_session.to_dict())
    bob_state = json.dumps(bob_session.to_dict())

    # Write with restrictive perms
    alice_state_path.write_text(alice_state)
    alice_state_path.chmod(0o600)
    bob_state_path.write_text(bob_state)
    bob_state_path.chmod(0o600)

    safe_print({
        "directory": temp_dir,
        "permissions": "0o700",
        "alice_state_digest": hashlib.sha256(alice_state.encode()).hexdigest()[:16] + "...",
        "bob_state_digest": hashlib.sha256(bob_state.encode()).hexdigest()[:16] + "...",
    }, "Persisted State (Digest Only)")

    print_success("State persisted to temp directory")

    # =========================================================================
    # Step 4: Restore Sessions
    # =========================================================================
    print_header("Step 4: Restore Sessions")

    # Simulate application restart - load from files
    restored_alice_state = json.loads(alice_state_path.read_text())
    restored_bob_state = json.loads(bob_state_path.read_text())

    alice_restored = Session.from_dict(restored_alice_state)
    bob_restored = Session.from_dict(restored_bob_state)

    print_info(f"Alice restored - msgs sent: {alice_restored.messages_sent}")
    print_info(f"Bob restored - msgs sent: {bob_restored.messages_sent}")
    print_success("Sessions restored")

    # =========================================================================
    # Step 5: Verify Continuity
    # =========================================================================
    print_header("Step 5: Verify Message Continuity")

    msg3 = b"Hello again Bob, this is message 3 after restore"
    ct3 = alice_restored.encrypt(msg3)
    pt3 = bob_restored.decrypt(ct3)
    print_info(f"Alice → Bob (post-restore): {msg3.decode()}")
    assert pt3 == msg3

    msg4 = b"Got it Alice, continuity confirmed"
    ct4 = bob_restored.encrypt(msg4)
    pt4 = alice_restored.decrypt(ct4)
    print_info(f"Bob → Alice (post-restore): {msg4.decode()}")
    assert pt4 == msg4

    print_success("Message sequence continuity verified!")

    # =========================================================================
    # Cleanup
    # =========================================================================
    print_header("Cleanup")

    # Remove state files
    alice_state_path.unlink()
    bob_state_path.unlink()
    os.rmdir(temp_dir)

    print_success("Temp state files removed")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Summary")

    print("✅ Session Persistence demonstrated:")
    print("   - [x] Create sessions with X3DH")
    print("   - [x] Exchange messages (pre-persist)")
    print("   - [x] Serialize state to JSON")
    print("   - [x] Store in temp dir (mode 0o700)")
    print("   - [x] Restore both sessions")
    print("   - [x] Verify message continuity (post-restore)")
    print("   - [x] Cleanup temp files")


if __name__ == "__main__":
    main()
