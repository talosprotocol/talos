import pytest
import binascii
import os
import json
from talos_sdk.secrets.kek import Envelope, ALGORITHM_AES_256_GCM, generate_master_key, SCHEMA_ID_ENVELOPE
from talos_sdk.secrets.local_provider import LocalKekProvider

# Do NOT hardcode master keys in source. Load from environment or generate for ephemeral tests.
MASTER_KEY = os.environ.get("TALOS_MASTER_KEY", generate_master_key())
KEY_ID = "kek-v1"

@pytest.fixture
def provider():
    return LocalKekProvider(MASTER_KEY, KEY_ID)

def test_encrypt_decrypt_roundtrip(provider):
    plaintext = b"super secret data"
    envelope = provider.encrypt(plaintext)
    
    # Verify Envelope Structure
    assert envelope.kek_id == KEY_ID
    assert envelope.alg == ALGORITHM_AES_256_GCM
    assert envelope.schema_id == SCHEMA_ID_ENVELOPE
    assert len(binascii.unhexlify(envelope.iv)) == 12
    assert len(binascii.unhexlify(envelope.tag)) == 16
    assert envelope.ciphertext # Not empty
    assert envelope.created_at.endswith("Z")
    
    # Decrypt
    decrypted = provider.decrypt(envelope)
    assert decrypted == plaintext

def test_decrypt_fail_key_mismatch(provider):
    plaintext = b"data"
    envelope = provider.encrypt(plaintext)
    
    # Create new envelope with different key ID but same data
    data = envelope.to_dict()
    data["kek_id"] = "wrong-key"
    bad_envelope = Envelope.from_dict(data)
    
    with pytest.raises(ValueError, match="Key mismatch"):
        provider.decrypt(bad_envelope)

def test_decrypt_fail_tampered_ciphertext(provider):
    plaintext = b"data"
    envelope = provider.encrypt(plaintext)
    
    # Tamper ciphertext (flip last char)
    ct_bytes = bytearray(binascii.unhexlify(envelope.ciphertext))
    ct_bytes[-1] ^= 0xFF
    envelope.ciphertext = binascii.hexlify(ct_bytes).decode('ascii')
    
    # GCM should fail authentication
    from cryptography.exceptions import InvalidTag
    with pytest.raises(InvalidTag):
        provider.decrypt(envelope)

def test_envelope_serialization():
    env = Envelope(
        kek_id="k1",
        iv="00"*12,
        ciphertext="aa",
        tag="bb"*16,
        alg="aes-256-gcm"
    )
    json_str = env.to_json()
    d = json.loads(json_str)
    assert d["schema_id"] == SCHEMA_ID_ENVELOPE
    assert d["kek_id"] == "k1"
    
    env2 = Envelope.from_json(json_str)
    assert env2.kek_id == "k1"
    assert env2.iv == env.iv

def test_envelope_validation():
    from pydantic import ValidationError
    # Invalid IV
    with pytest.raises(ValidationError):
        Envelope(kek_id="k1", iv="too-short", ciphertext="aa", tag="bb"*16)
    
    # Invalid Tag
    with pytest.raises(ValidationError):
        Envelope(kek_id="k1", iv="00"*12, ciphertext="aa", tag="invalid-tag")
