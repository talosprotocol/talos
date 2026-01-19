#!/usr/bin/env python3
"""A2A Live Gateway Integration Example.

Demonstrates REAL A2A communication with a live gateway:
- Creates actual sessions via gateway API
- Sends encrypted frames to gateway storage
- Receives frames from gateway
- Full Double Ratchet E2E encryption

REQUIRES: Gateway running at http://localhost:8000

Run: python examples/a2a_live_integration.py --gateway-url http://localhost:8000
"""

import asyncio
import hashlib
import sys
from pathlib import Path

# Add examples dir to path for _common import
sys.path.insert(0, str(Path(__file__).parent))
# Add src for SDK imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from _common import (
    parse_common_args,
    check_gateway,
    safe_print,
    print_header,
    print_success,
    print_info,
    print_error,
)

from talos_sdk import Wallet, TalosClient
from talos_sdk.a2a import A2ATransport, A2ASessionClient, RatchetFrameCrypto
from talos_sdk.a2a.ratchet_crypto import NONCE_LEN
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


async def main():
    args = parse_common_args(description="Talos A2A Live Gateway Integration")

    print_header("Talos A2A Live Gateway Integration")

    # =========================================================================
    # Step 0: Check gateway is reachable
    # =========================================================================
    check_gateway(args.gateway_url, args.timeout)

    # =========================================================================
    # Step 1: Create agent wallets and ratchet sessions
    # =========================================================================
    print_header("Step 1: Agent Setup")

    # Alice's identity (Wallet + TalosClient for HTTP signing)
    alice_wallet = Wallet.generate(name="alice-live")
    alice_client = TalosClient(args.gateway_url, alice_wallet)
    alice_keypair = generate_signing_keypair()
    alice_manager = SessionManager(alice_keypair)

    # Bob's identity
    bob_wallet = Wallet.generate(name="bob-live")
    bob_client = TalosClient(args.gateway_url, bob_wallet)
    bob_keypair = generate_signing_keypair()
    bob_manager = SessionManager(bob_keypair)

    print_info(f"Alice DID: {alice_wallet.to_did()[:40]}...")
    print_info(f"Bob DID:   {bob_wallet.to_did()[:40]}...")

    # =========================================================================
    # Step 2: Key Exchange (X3DH) - Local
    # =========================================================================
    print_header("Step 2: Key Exchange (X3DH)")

    bob_bundle = bob_manager.get_prekey_bundle()
    alice_ratchet = alice_manager.create_session_as_initiator("bob", bob_bundle)
    bob_ratchet = bob_manager.create_session_as_responder(
        "alice", alice_ratchet.state.dh_keypair.public_key
    )

    print_success("X3DH key exchange complete")

    # Create crypto adapters
    alice_crypto = RatchetFrameCrypto(alice_ratchet)
    bob_crypto = RatchetFrameCrypto(bob_ratchet)

    # =========================================================================
    # Step 3: Create A2A Session via Gateway
    # =========================================================================
    print_header("Step 3: Create Gateway Session")

    # Use TalosClient for signing (has sign_http_request method)
    alice_transport = A2ATransport(args.gateway_url, alice_client)
    bob_transport = A2ATransport(args.gateway_url, bob_client)

    try:
        # Alice creates session
        session_resp = await alice_transport.create_session(bob_wallet.to_did())
        session_id = session_resp.session_id

        safe_print({
            "session_id": session_id,
            "state": session_resp.state,
            "initiator": session_resp.initiator_id[:30] + "...",
            "responder": session_resp.responder_id[:30] + "...",
        }, "Session Created via Gateway")

        # Bob accepts session
        await bob_transport.accept_session(session_id)
        print_success("Bob accepted session")

    except Exception as e:
        print_error(f"Gateway session creation failed: {e}")
        print_info("This may be expected if A2A endpoints are not yet implemented")
        print_info("Falling back to local-only demo...")
        session_id = "local-demo-session"

    # =========================================================================
    # Step 4: Send Encrypted Frame via Gateway
    # =========================================================================
    print_header("Step 4: Send Encrypted Message")

    plaintext = b"Hello Bob! This is a LIVE message via the gateway!"
    print_info(f"Plaintext: {plaintext.decode()}")

    # Encrypt with Double Ratchet
    header_b64u, ciphertext_b64u, ciphertext_hash = alice_crypto.encrypt(plaintext)

    # Compute frame_digest
    sender_seq = 0
    frame_digest = compute_frame_digest(
        session_id, alice_wallet.to_did(), sender_seq, header_b64u, ciphertext_hash
    )

    from talos_sdk.a2a.models import EncryptedFrame

    frame = EncryptedFrame(
        session_id=session_id,
        sender_id=alice_wallet.to_did(),
        sender_seq=sender_seq,
        header_b64u=header_b64u,
        ciphertext_b64u=ciphertext_b64u,
        frame_digest=frame_digest,
        ciphertext_hash=ciphertext_hash,
    )

    try:
        resp = await alice_transport.send_frame(session_id, frame)
        safe_print({
            "session_id": resp.session_id,
            "sender_seq": resp.sender_seq,
            "frame_digest": resp.frame_digest[:16] + "...",
        }, "Frame Sent via Gateway")
        print_success("Frame stored in gateway!")

    except Exception as e:
        print_error(f"Frame send failed: {e}")
        print_info("Gateway may not have A2A frame endpoints yet")

    # =========================================================================
    # Step 5: Receive and Decrypt
    # =========================================================================
    print_header("Step 5: Bob Receives & Decrypts")

    try:
        frames_resp = await bob_transport.receive_frames(session_id)
        print_info(f"Received {len(frames_resp.items)} frame(s) from gateway")

        for f in frames_resp.items:
            decrypted = bob_crypto.decrypt(f.header_b64u, f.ciphertext_b64u, f.ciphertext_hash)
            print_success(f"Decrypted: {decrypted.decode()}")

    except Exception as e:
        print_error(f"Frame receive failed: {e}")
        # Fallback: decrypt locally
        print_info("Decrypting locally instead...")
        decrypted = bob_crypto.decrypt(header_b64u, ciphertext_b64u, ciphertext_hash)
        print_success(f"Decrypted (local): {decrypted.decode()}")

    # =========================================================================
    # Cleanup
    # =========================================================================
    print_header("Cleanup")

    await alice_transport.aclose()
    await bob_transport.aclose()
    print_success("Transports closed")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Live Integration Complete!")

    print("✅ Features demonstrated:")
    print("   - Real wallet identity generation")
    print("   - X3DH key exchange")
    print("   - Double Ratchet encryption")
    print("   - Gateway session creation (if available)")
    print("   - Encrypted frame transmission")
    print("   - Frame decryption")


if __name__ == "__main__":
    asyncio.run(main())
