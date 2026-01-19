#!/usr/bin/env python3
"""Secrets Envelope Encryption Demo.

Demonstrates secure secret management:
- Envelope encryption with AES-256-GCM
- Key derivation with HKDF
- KEK rotation handling

SECURITY: This demo never prints KEK, DEK, plaintext secrets, or raw ciphertext.
Only prints: sizes, digests, schema IDs, and success markers.

Run: python examples/secrets_demo.py --help
"""

import hashlib
import os
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

from talos_sdk.secrets import SecretsEnvelope, encrypt_envelope, decrypt_envelope


def main():
    args = parse_common_args(description="Talos Secrets Envelope Demo")

    print_header("Talos Secrets Envelope Encryption Demo")
    print_warning("No plaintext, KEKs, DEKs, or raw ciphertext will be displayed.")

    # =========================================================================
    # Step 1: Setup - Simulated KEK (Never printed)
    # =========================================================================
    print_header("Step 1: Key Setup")

    # Simulate a KEK (Key Encryption Key) - in production this comes from KMS
    kek_v1 = os.urandom(32)  # 256-bit key
    kek_id_v1 = "kek-v1"

    print_info(f"KEK ID: {kek_id_v1}")
    print_info(f"KEK size: 256 bits")
    print_success("KEK loaded (never printed)")

    # =========================================================================
    # Step 2: Encrypt a Secret
    # =========================================================================
    print_header("Step 2: Encrypt Secret")

    # The actual secret - NEVER PRINTED
    secret_plaintext = b"super-secret-api-key-12345"

    envelope = encrypt_envelope(
        plaintext=secret_plaintext,
        kek=kek_v1,
        kek_id=kek_id_v1,
    )

    # Safe output - only metadata
    safe_print({
        "schema_id": envelope.schema_id,
        "schema_version": envelope.schema_version,
        "kek_id": envelope.kek_id,
        "ciphertext_size": len(envelope.ciphertext),
        "ciphertext_digest": hashlib.sha256(envelope.ciphertext).hexdigest()[:16] + "...",
    }, "Encrypted Envelope (Metadata Only)")

    print_success("Secret encrypted successfully")

    # =========================================================================
    # Step 3: Decrypt the Secret
    # =========================================================================
    print_header("Step 3: Decrypt Secret")

    decrypted = decrypt_envelope(envelope, kek_v1)

    # Verify without printing the actual secret
    if decrypted == secret_plaintext:
        print_success("Decryption verified: Plaintext matches original")
        print_info(f"Decrypted size: {len(decrypted)} bytes")
    else:
        print_warning("Decryption mismatch!")

    # =========================================================================
    # Step 4: KEK Rotation
    # =========================================================================
    print_header("Step 4: KEK Rotation")

    # New KEK for rotation
    kek_v2 = os.urandom(32)
    kek_id_v2 = "kek-v2"

    print_info(f"Old KEK ID: {kek_id_v1}")
    print_info(f"New KEK ID: {kek_id_v2}")

    # Re-encrypt with new KEK
    new_envelope = encrypt_envelope(
        plaintext=decrypted,  # Decrypt with old, encrypt with new
        kek=kek_v2,
        kek_id=kek_id_v2,
    )

    safe_print({
        "kek_id": new_envelope.kek_id,
        "ciphertext_size": len(new_envelope.ciphertext),
        "ciphertext_digest": hashlib.sha256(new_envelope.ciphertext).hexdigest()[:16] + "...",
    }, "Rotated Envelope")

    # Verify decryption with new KEK
    rotated_decrypted = decrypt_envelope(new_envelope, kek_v2)
    if rotated_decrypted == secret_plaintext:
        print_success("Post-rotation decryption verified")
    else:
        print_warning("Post-rotation decryption failed!")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Security Properties Demonstrated")

    print("🔐 Envelope Encryption:")
    print("   - Plaintext encrypted with DEK (per-secret)")
    print("   - DEK encrypted with KEK (master/KMS)")

    print("\n🔄 Key Rotation:")
    print("   - KEK can be rotated without re-encrypting all secrets immediately")
    print("   - kek_id tracks which KEK version was used")

    print("\n🛡️  What was NOT printed:")
    print("   - ❌ KEK bytes")
    print("   - ❌ DEK bytes")
    print("   - ❌ Plaintext secret")
    print("   - ❌ Raw ciphertext bytes")


if __name__ == "__main__":
    main()
