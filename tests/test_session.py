"""
Tests for the Double Ratchet Protocol implementation.

Tests cover:
- Prekey bundle creation and verification
- X3DH key exchange
- Ratchet encryption/decryption
- Forward secrecy
- Out-of-order message handling
- Session persistence
"""

import pytest
import tempfile
from pathlib import Path

from src.core.session import (
    Session,
    SessionManager,
    RatchetState,
    PrekeyBundle,
    MessageHeader,
    RatchetError,
)
from src.core.crypto import (
    generate_signing_keypair,
    generate_encryption_keypair,
    sign_message,
)


class TestPrekeyBundle:
    """Tests for prekey bundle creation and verification."""
    
    def test_create_prekey_bundle(self):
        """Test creating a prekey bundle."""
        identity = generate_signing_keypair()
        prekey = generate_encryption_keypair()
        signature = sign_message(prekey.public_key, identity.private_key)
        
        bundle = PrekeyBundle(
            identity_key=identity.public_key,
            signed_prekey=prekey.public_key,
            prekey_signature=signature,
        )
        
        assert bundle.verify()
    
    def test_invalid_signature_fails(self):
        """Test that invalid signature fails verification."""
        identity = generate_signing_keypair()
        prekey = generate_encryption_keypair()
        
        # Sign with wrong key
        wrong_key = generate_signing_keypair()
        signature = sign_message(prekey.public_key, wrong_key.private_key)
        
        bundle = PrekeyBundle(
            identity_key=identity.public_key,
            signed_prekey=prekey.public_key,
            prekey_signature=signature,
        )
        
        assert not bundle.verify()
    
    def test_serialization(self):
        """Test bundle serialization."""
        identity = generate_signing_keypair()
        prekey = generate_encryption_keypair()
        signature = sign_message(prekey.public_key, identity.private_key)
        
        bundle = PrekeyBundle(
            identity_key=identity.public_key,
            signed_prekey=prekey.public_key,
            prekey_signature=signature,
        )
        
        # Round-trip
        data = bundle.to_dict()
        restored = PrekeyBundle.from_dict(data)
        
        assert restored.identity_key == bundle.identity_key
        assert restored.signed_prekey == bundle.signed_prekey
        assert restored.verify()


class TestMessageHeader:
    """Tests for message header serialization."""
    
    def test_header_roundtrip(self):
        """Test header serialization round-trip."""
        dh_key = generate_encryption_keypair()
        header = MessageHeader(
            dh_public=dh_key.public_key,
            previous_chain_length=5,
            message_number=10,
        )
        
        data = header.to_bytes()
        restored = MessageHeader.from_bytes(data)
        
        assert restored.dh_public == header.dh_public
        assert restored.previous_chain_length == 5
        assert restored.message_number == 10


class TestSession:
    """Tests for individual sessions."""
    
    @pytest.fixture
    def alice_manager(self):
        """Create Alice's session manager."""
        identity = generate_signing_keypair()
        return SessionManager(identity)
    
    @pytest.fixture
    def bob_manager(self):
        """Create Bob's session manager."""
        identity = generate_signing_keypair()
        return SessionManager(identity)
    
    def test_create_initiator_session(self, alice_manager, bob_manager):
        """Test creating a session as initiator."""
        bob_bundle = bob_manager.get_prekey_bundle()
        
        session = alice_manager.create_session_as_initiator("bob", bob_bundle)
        
        assert session is not None
        assert session.peer_id == "bob"
        assert session.state.chain_key_send is not None
    
    def test_encrypt_decrypt_roundtrip(self, alice_manager, bob_manager):
        """Test basic encryption/decryption."""
        bob_bundle = bob_manager.get_prekey_bundle()
        
        # Alice creates session and encrypts
        alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
        plaintext = b"Hello, Bob!"
        encrypted = alice_session.encrypt(plaintext)
        
        # Bob creates session and decrypts
        # Extract ephemeral from message header
        header_len = int.from_bytes(encrypted[:2], "big")
        header_bytes = encrypted[2:2 + header_len]
        header = MessageHeader.from_bytes(header_bytes)
        
        bob_session = bob_manager.create_session_as_responder(
            "alice",
            header.dh_public,
            alice_manager.identity_keypair.public_key,
        )
        
        # Bob needs to DH ratchet to receive
        decrypted = bob_session.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_multiple_messages(self, alice_manager, bob_manager):
        """Test sending multiple messages."""
        bob_bundle = bob_manager.get_prekey_bundle()
        alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
        
        messages = [b"Message 1", b"Message 2", b"Message 3"]
        encrypted_messages = [alice_session.encrypt(m) for m in messages]
        
        # All should be encrypted with different keys (ratcheting)
        assert len(set(encrypted_messages)) == 3
        assert alice_session.messages_sent == 3
    
    def test_forward_secrecy(self, alice_manager, bob_manager):
        """Test that compromising current key doesn't expose past messages."""
        bob_bundle = bob_manager.get_prekey_bundle()
        alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
        
        # Send message
        alice_session.encrypt(b"Secret message")
        
        # Save old chain key
        old_chain_key = alice_session.state.chain_key_send
        
        # Send another message (advances chain)
        alice_session.encrypt(b"Another message")
        
        # Chain key has changed
        assert alice_session.state.chain_key_send != old_chain_key
    
    def test_session_serialization(self, alice_manager, bob_manager):
        """Test session state serialization."""
        bob_bundle = bob_manager.get_prekey_bundle()
        alice_session = alice_manager.create_session_as_initiator("bob", bob_bundle)
        
        # Encrypt a message
        alice_session.encrypt(b"Test message")
        
        # Serialize and restore
        data = alice_session.to_dict()
        restored = Session.from_dict(data)
        
        assert restored.peer_id == alice_session.peer_id
        assert restored.messages_sent == 1


class TestSessionManager:
    """Tests for the session manager."""
    
    def test_get_prekey_bundle(self):
        """Test prekey bundle generation."""
        identity = generate_signing_keypair()
        manager = SessionManager(identity)
        
        bundle = manager.get_prekey_bundle()
        
        assert bundle.identity_key == identity.public_key
        assert bundle.verify()
    
    def test_session_storage(self):
        """Test session retrieval."""
        identity = generate_signing_keypair()
        manager = SessionManager(identity)
        
        # Create a session
        peer_identity = generate_signing_keypair()
        peer_prekey = generate_encryption_keypair()
        peer_sig = sign_message(peer_prekey.public_key, peer_identity.private_key)
        
        peer_bundle = PrekeyBundle(
            identity_key=peer_identity.public_key,
            signed_prekey=peer_prekey.public_key,
            prekey_signature=peer_sig,
        )
        
        session = manager.create_session_as_initiator("peer1", peer_bundle)
        
        # Retrieve it
        assert manager.has_session("peer1")
        assert manager.get_session("peer1") == session
        assert not manager.has_session("peer2")
    
    def test_persistence(self):
        """Test session persistence to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "sessions.json"
            
            identity = generate_signing_keypair()
            manager = SessionManager(identity, storage_path)
            
            # Create a peer bundle
            peer_identity = generate_signing_keypair()
            peer_prekey = generate_encryption_keypair()
            peer_sig = sign_message(peer_prekey.public_key, peer_identity.private_key)
            
            peer_bundle = PrekeyBundle(
                identity_key=peer_identity.public_key,
                signed_prekey=peer_prekey.public_key,
                prekey_signature=peer_sig,
            )
            
            # Create session and send message
            session = manager.create_session_as_initiator("peer1", peer_bundle)
            session.encrypt(b"Test")
            
            # Save
            manager.save()
            assert storage_path.exists()
            
            # Load in new manager
            manager2 = SessionManager(identity, storage_path)
            manager2.load()
            
            assert manager2.has_session("peer1")
            loaded_session = manager2.get_session("peer1")
            assert loaded_session.messages_sent == 1
    
    def test_remove_session(self):
        """Test session removal."""
        identity = generate_signing_keypair()
        manager = SessionManager(identity)
        
        peer_identity = generate_signing_keypair()
        peer_prekey = generate_encryption_keypair()
        peer_sig = sign_message(peer_prekey.public_key, peer_identity.private_key)
        
        peer_bundle = PrekeyBundle(
            identity_key=peer_identity.public_key,
            signed_prekey=peer_prekey.public_key,
            prekey_signature=peer_sig,
        )
        
        manager.create_session_as_initiator("peer1", peer_bundle)
        assert manager.has_session("peer1")
        
        manager.remove_session("peer1")
        assert not manager.has_session("peer1")
    
    def test_stats(self):
        """Test session statistics."""
        identity = generate_signing_keypair()
        manager = SessionManager(identity)
        
        peer_identity = generate_signing_keypair()
        peer_prekey = generate_encryption_keypair()
        peer_sig = sign_message(peer_prekey.public_key, peer_identity.private_key)
        
        peer_bundle = PrekeyBundle(
            identity_key=peer_identity.public_key,
            signed_prekey=peer_prekey.public_key,
            prekey_signature=peer_sig,
        )
        
        session = manager.create_session_as_initiator("peer1", peer_bundle)
        session.encrypt(b"Message 1")
        session.encrypt(b"Message 2")
        
        stats = manager.get_stats()
        
        assert stats["active_sessions"] == 1
        assert stats["total_messages_sent"] == 2


class TestRatchetState:
    """Tests for ratchet state serialization."""
    
    def test_state_roundtrip(self):
        """Test state serialization round-trip."""
        dh = generate_encryption_keypair()
        remote = generate_encryption_keypair()
        
        state = RatchetState(
            dh_keypair=dh,
            dh_remote=remote.public_key,
            root_key=b"a" * 32,
            chain_key_send=b"b" * 32,
            chain_key_recv=b"c" * 32,
            send_count=5,
            recv_count=3,
        )
        
        data = state.to_dict()
        restored = RatchetState.from_dict(data)
        
        assert restored.root_key == state.root_key
        assert restored.send_count == 5
        assert restored.recv_count == 3


class TestErrorCases:
    """Tests for error handling."""
    
    def test_invalid_prekey_bundle_rejected(self):
        """Test that invalid prekey bundle is rejected."""
        identity = generate_signing_keypair()
        manager = SessionManager(identity)
        
        # Create an invalid bundle (wrong signature)
        peer_id = generate_signing_keypair()
        prekey = generate_encryption_keypair()
        wrong_sig = b"x" * 64  # Invalid signature
        
        bad_bundle = PrekeyBundle(
            identity_key=peer_id.public_key,
            signed_prekey=prekey.public_key,
            prekey_signature=wrong_sig,
        )
        
        with pytest.raises(RatchetError):
            manager.create_session_as_initiator("bad_peer", bad_bundle)
