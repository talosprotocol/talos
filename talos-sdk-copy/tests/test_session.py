import json

from talos_sdk.crypto import generate_encryption_keypair
from talos_sdk.session import Session, SessionManager
from talos_sdk.wallet import Wallet


def test_ratchet_flow_and_out_of_order():
    # 1. Setup Identities
    alice_wallet = Wallet.generate("Alice")
    bob_wallet = Wallet.generate("Bob")

    # NOTE: In this implementation SessionManager takes a KeyPair not a Wallet
    # We need to construct a KeyPair from the wallet's keys for SessionManager
    # Or SessionManager expects ED25519 helper?
    # Let's check SessionManager.__init__: def __init__(self, identity_keypair: KeyPair ...
    # And KeyPair is from .crypto.
    # Wallet uses Ed25519PrivateKey directly.
    # We need to adapt because SessionManager uses KeyPair struct.

    from talos_sdk.crypto import KeyPair

    def wallet_to_keypair(w):
        return KeyPair(
            public_key=w.public_key,
            private_key=w._private_key.private_bytes_raw(),
            key_type="ed25519",
        )

    alice_mgr = SessionManager(wallet_to_keypair(alice_wallet))
    bob_mgr = SessionManager(wallet_to_keypair(bob_wallet))

    # 2. Publish Bob's Bundle
    bob_bundle = bob_mgr.get_prekey_bundle()

    # 3. Alice initiates session
    alice_session = alice_mgr.create_session_as_initiator("Bob", bob_bundle)

    # 4. Alice sends message "Hello Bob"
    msg1 = alice_session.encrypt(b"Hello Bob")

    # 5. Bob receives "Hello Bob"
    # Bob needs to create session from first message hint?
    # Or does create_session_as_responder assume we know the peer?
    # In Signal X3DH, the first message contains the initial key exchange info usually.
    # Here create_session_as_responder signature is:
    # create_session_as_responder(self, peer_id: str, peer_dh_public: bytes)
    # The first message envelope contains "header": {"dh": ...}

    envelope1 = json.loads(msg1)
    # Need to base64url decode envelope1["header"]["dh"] to get bytes
    from talos_sdk.crypto import b64u_decode

    alice_dh_public = b64u_decode(envelope1["header"]["dh"])

    bob_session = bob_mgr.create_session_as_responder("Alice", alice_dh_public)
    decrypted1 = bob_session.decrypt(msg1)
    assert decrypted1 == b"Hello Bob"

    # 6. Bob replies "Hello Alice"
    msg2 = bob_session.encrypt(b"Hello Alice")
    decrypted2 = alice_session.decrypt(msg2)
    assert decrypted2 == b"Hello Alice"

    # 7. Ratchet Test (Ping Pong)
    msgs = [b"MSG_1", b"MSG_2", b"MSG_3"]
    encrypted_msgs = []

    for m in msgs:
        encrypted_msgs.append(alice_session.encrypt(m))

    # Decrypt out of order
    # Decrypt 3 first, then 1, then 2
    assert bob_session.decrypt(encrypted_msgs[2]) == msgs[2]
    assert bob_session.decrypt(encrypted_msgs[0]) == msgs[0]
    assert bob_session.decrypt(encrypted_msgs[1]) == msgs[1]


def test_session_serialization():
    # Setup
    # Setup
    # w = Wallet.generate("Test") - REMOVED (Unused)
    # kp = KeyPair(...) - REMOVED (Unused)
    # SessionManager not needed for this test; we are testing Session serialization directly.

    # Create a dummy session (mocked state for minimal test)
    # Ideally should run thorough handshake, but re-using flow logic above
    # Let's just create a session and serialize it

    # Manually bootstrapping state just to test ser/deser
    from talos_sdk.session import RatchetState

    state = RatchetState(
        dh_keypair=generate_encryption_keypair(),
        dh_remote=generate_encryption_keypair().public_key,
        root_key=b"0" * 32,
        chain_key_send=b"1" * 32,
        chain_key_recv=b"2" * 32,
    )

    sess = Session("remote-peer", state)
    data = sess.to_dict()

    sess2 = Session.from_dict(data)
    assert sess2.peer_id == sess.peer_id
    assert sess2.state.root_key == sess.state.root_key
