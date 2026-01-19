"""RatchetFrameCrypto - bridges A2A transport with Double Ratchet Session.

Phase 10.3 implementation per LOCKED SPEC:
- Nonce fixed at 12 bytes (ChaCha20-Poly1305)
- ciphertext_hash is SHA-256 of ciphertext only (excluding nonce)
- frame_digest computed externally by session_client
"""

import base64
import hashlib
import json
from typing import TYPE_CHECKING

from talos_sdk.canonical import canonical_json_bytes
from talos_sdk.crypto import b64u_encode

if TYPE_CHECKING:
    from talos_sdk.session import Session

# ChaCha20-Poly1305 nonce length (fixed, hardcoded)
NONCE_LEN = 12


def _b64u_decode_strict(s: str) -> bytes:
    """Decode base64url without padding.

    Rejects:
    - Inputs containing '='
    - Impossible lengths (len % 4 == 1)

    Raises:
        ValueError: If input is invalid base64url
    """
    if "=" in s:
        raise ValueError("Base64url must not contain padding")

    # base64url without padding can never have length mod 4 == 1
    rem = len(s) % 4
    if rem == 1:
        raise ValueError("Invalid base64url length")

    # Add internal padding only for decoding
    if rem:
        s = s + ("=" * (4 - rem))

    return base64.urlsafe_b64decode(s)


class RatchetFrameCrypto:
    """FrameCrypto implementation using Double Ratchet Session.

    Bridges Phase 10.2 transport with existing ratchet encryption.
    Does NOT compute frame_digest (caller computes after reserving sender_seq).

    Usage:
        crypto = RatchetFrameCrypto(session)
        header_b64u, ciphertext_b64u, ciphertext_hash = crypto.encrypt(plaintext)
    """

    def __init__(self, session: "Session"):
        self._session = session

    def encrypt(self, plaintext: bytes) -> tuple[str, str, str]:
        """Encrypt plaintext and return frame components.

        Returns:
            Tuple of (header_b64u, ciphertext_b64u, ciphertext_hash)

        Note:
            frame_digest is computed by session_client after reserving sender_seq.

        Raises:
            ValueError: If nonce length is unexpected (regression guard)
        """
        # Use existing session encrypt
        envelope_bytes = self._session.encrypt(plaintext)
        envelope = json.loads(envelope_bytes.decode("utf-8"))

        # Extract and validate components
        header_dict = envelope["header"]
        nonce = _b64u_decode_strict(envelope["nonce"])
        ciphertext = _b64u_decode_strict(envelope["ciphertext"])

        # Regression guard: assert nonce length
        if len(nonce) != NONCE_LEN:
            raise ValueError(f"Unexpected nonce length: {len(nonce)}, expected {NONCE_LEN}")

        # Compute header_b64u from canonical header
        # Uses same format Session expects: {"dh", "n", "pn"}
        header_bytes = canonical_json_bytes(header_dict)
        header_b64u = b64u_encode(header_bytes)

        # Combine nonce + ciphertext for transport
        combined = nonce + ciphertext
        ciphertext_b64u = b64u_encode(combined)

        # Compute ciphertext_hash (SHA256 of raw ciphertext only, not nonce)
        ciphertext_hash = hashlib.sha256(ciphertext).hexdigest()

        return header_b64u, ciphertext_b64u, ciphertext_hash

    def decrypt(
        self,
        header_b64u: str,
        ciphertext_b64u: str,
        ciphertext_hash: str | None = None,
    ) -> bytes:
        """Decrypt frame and return plaintext.

        Args:
            header_b64u: Base64url encoded canonical header JSON
            ciphertext_b64u: Base64url encoded nonce||ciphertext
            ciphertext_hash: Optional SHA256 hash for integrity check

        Returns:
            Decrypted plaintext bytes

        Raises:
            ValueError: If base64url is invalid, ciphertext too short,
                       or ciphertext_hash mismatch
            RatchetError: If decryption fails (from Session.decrypt)
        """
        # Decode components (strict: reject padding and invalid lengths)
        header_bytes = _b64u_decode_strict(header_b64u)
        combined = _b64u_decode_strict(ciphertext_b64u)

        # Split nonce (12 bytes) and ciphertext
        if len(combined) < NONCE_LEN:
            raise ValueError(f"Ciphertext too short: {len(combined)} bytes")
        nonce = combined[:NONCE_LEN]
        ciphertext = combined[NONCE_LEN:]

        # Regression guard: assert nonce length after split
        if len(nonce) != NONCE_LEN:
            raise ValueError(f"Unexpected nonce length after split: {len(nonce)}")

        # Optional integrity check
        if ciphertext_hash is not None:
            computed_hash = hashlib.sha256(ciphertext).hexdigest()
            if computed_hash != ciphertext_hash:
                raise ValueError(
                    f"Ciphertext hash mismatch: expected {ciphertext_hash}, got {computed_hash}"
                )

        # Parse header JSON safely
        try:
            header_dict = json.loads(header_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid header JSON: {e}") from e

        # Validate required header fields (ratchet expects these)
        required_fields = {"dh", "pn", "n"}
        if not required_fields.issubset(header_dict.keys()):
            missing = required_fields - set(header_dict.keys())
            raise ValueError(f"Missing header fields: {missing}")

        # Reconstruct envelope in the format Session.decrypt expects
        envelope = {
            "header": header_dict,
            "nonce": b64u_encode(nonce),
            "ciphertext": b64u_encode(ciphertext),
        }

        # Serialize using canonical_json_bytes (same as Session.encrypt output)
        envelope_bytes = canonical_json_bytes(envelope)

        return self._session.decrypt(envelope_bytes)
