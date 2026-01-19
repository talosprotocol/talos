import time

from talos_sdk.security import Capability
from talos_sdk.wallet import Wallet


def test_capability_lifecycle():
    # Setup Wallets
    issuer = Wallet.generate("did:example:issuer")
    subject_did = "did:example:subject"

    # Create Capability
    scope = [{"tool": "aws:s3", "actions": ["list"]}]
    cap = Capability.create(
        issuer_wallet=issuer,
        subject_did=subject_did,
        scope=scope,
        exp=int(time.time()) + 3600,
    )

    # Verify Fields
    assert cap.iss == issuer.to_did()
    assert cap.sub == subject_did
    assert cap.scope == scope
    assert cap.v == "1"
    assert cap.sig is not None

    # Verify Signature Success
    assert cap.verify(issuer.public_key) is True

    # Check Authorization
    assert cap.authorize("aws:s3", "list") is True
    assert cap.authorize("aws:s3", "delete") is False
    assert cap.authorize("aws:ec2", "list") is False


def test_capability_expiry():
    issuer = Wallet.generate("did:example:issuer")
    cap = Capability.create(
        issuer_wallet=issuer,
        subject_did="did:example:subject",
        scope=[],
        exp=int(time.time()) - 3600,  # Expired
    )

    # Should fail verification due to expiry
    assert cap.verify(issuer.public_key) is False


def test_capability_tampering():
    issuer = Wallet.generate("did:example:issuer")
    cap = Capability.create(
        issuer_wallet=issuer,
        subject_did="did:example:subject",
        scope=[],
        exp=int(time.time()) + 3600,
    )

    # Tamper with scope
    cap.data["scope"] = [{"tool": "aws:all", "actions": ["*"]}]

    # Verification should fail
    assert cap.verify(issuer.public_key) is False


def test_capability_invalid_sig_structure():
    issuer = Wallet.generate("did:example:issuer")
    cap = Capability.create(
        issuer_wallet=issuer,
        subject_did="did:example:subj",
        scope=[],
        exp=int(time.time()) + 60,
    )

    # Valid signature
    assert cap.verify(issuer.public_key) is True

    # Remove signature
    cap.sig = None
    assert cap.verify(issuer.public_key) is False


def test_authorize_malformed_scope():
    issuer = Wallet.generate("did:example:issuer")
    cap = Capability.create(
        issuer_wallet=issuer,
        subject_did="did:example:subj",
        scope="server-admin",  # Not a list
        exp=int(time.time()) + 60,
    )
    # Should return False safely
    assert cap.authorize("any", "action") is False
