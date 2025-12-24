"""
Integration tests for the blockchain messaging protocol.
"""


from src.core.blockchain import Blockchain
from src.core.crypto import Wallet, derive_shared_secret, encrypt_message, decrypt_message
from src.core.message import MessagePayload, MessageType, create_text_message
from src.engine.chunker import DataChunker, ChunkReassembler


class TestEndToEndEncryption:
    """Tests for end-to-end encryption between two wallets."""
    
    def test_encrypted_message_exchange(self):
        """Test that Alice can send an encrypted message to Bob."""
        # Create wallets
        alice = Wallet.generate("Alice")
        bob = Wallet.generate("Bob")
        
        # Original message
        plaintext = b"Hello Bob, this is a secret message!"
        
        # Alice encrypts for Bob
        shared_secret_alice = derive_shared_secret(
            alice.encryption_keys.private_key,
            bob.encryption_keys.public_key
        )
        nonce, ciphertext = encrypt_message(plaintext, shared_secret_alice)
        
        # Verify ciphertext is different from plaintext
        assert ciphertext != plaintext
        
        # Bob decrypts
        shared_secret_bob = derive_shared_secret(
            bob.encryption_keys.private_key,
            alice.encryption_keys.public_key
        )
        decrypted = decrypt_message(ciphertext, shared_secret_bob, nonce)
        
        # Verify successful decryption
        assert decrypted == plaintext
    
    def test_signed_and_encrypted_message(self):
        """Test message that is both signed and encrypted."""
        alice = Wallet.generate("Alice")
        bob = Wallet.generate("Bob")
        
        # Create message
        message = "Top secret information"
        
        # Alice signs
        signature = alice.sign(message.encode())
        
        # Alice encrypts
        shared_secret = derive_shared_secret(
            alice.encryption_keys.private_key,
            bob.encryption_keys.public_key
        )
        nonce, ciphertext = encrypt_message(message.encode(), shared_secret)
        
        # Bob decrypts
        bob_shared_secret = derive_shared_secret(
            bob.encryption_keys.private_key,
            alice.encryption_keys.public_key
        )
        decrypted = decrypt_message(ciphertext, bob_shared_secret, nonce)
        
        # Bob verifies signature
        from src.core.crypto import verify_signature
        is_valid = verify_signature(
            decrypted,
            signature,
            alice.signing_keys.public_key
        )
        
        assert is_valid is True
        assert decrypted.decode() == message


class TestBlockchainMessageRecording:
    """Tests for recording messages in blockchain."""
    
    def test_message_recording(self):
        """Test that messages are recorded in blockchain."""
        bc = Blockchain(difficulty=1)
        
        # Simulate message sending
        messages = [
            {"type": "sent", "to": "peer1", "content_hash": "abc"},
            {"type": "received", "from": "peer2", "content_hash": "def"},
        ]
        
        for msg in messages:
            bc.add_data(msg)
        
        # Mine block
        block = bc.mine_pending()
        
        # Verify
        assert block is not None
        assert bc.is_chain_valid()
        
        recorded = bc.get_messages()
        assert len(recorded) == 2


class TestChunkingLargeData:
    """Tests for chunking large data (future audio/video support)."""
    
    def test_chunk_and_reassemble(self):
        """Test chunking and reassembling data."""
        # Create large data
        data = b"X" * 200000  # 200KB
        
        chunker = DataChunker(chunk_size=64 * 1024)  # 64KB chunks
        reassembler = ChunkReassembler()
        
        # Chunk the data
        chunks = chunker.chunk(data)
        
        assert len(chunks) == 4  # 200KB / 64KB = 3.125 -> 4 chunks
        
        # Reassemble
        result = None
        for chunk in chunks:
            result = reassembler.add_chunk(chunk)
        
        assert result is not None
        assert result == data
    
    def test_out_of_order_chunks(self):
        """Test reassembly with out-of-order chunks."""
        data = b"0123456789" * 10000  # 100KB
        
        chunker = DataChunker(chunk_size=50 * 1024)
        reassembler = ChunkReassembler()
        
        chunks = chunker.chunk(data)
        
        # Send in reverse order
        result = None
        for chunk in reversed(chunks):
            result = reassembler.add_chunk(chunk)
        
        assert result is not None
        assert result == data
    
    def test_chunk_verification(self):
        """Test that corrupted chunks are detected."""
        data = b"Test data for chunking"
        
        chunker = DataChunker(chunk_size=10)
        chunks = chunker.chunk(data)
        
        # Corrupt a chunk
        chunk = chunks[0]
        chunk.data = b"CORRUPTED!"
        
        assert chunk.verify() is False


class TestMessagePayloadIntegration:
    """Integration tests for message payloads."""
    
    def test_full_message_lifecycle(self):
        """Test creating, serializing, and deserializing a message."""
        alice = Wallet.generate("Alice")
        bob = Wallet.generate("Bob")
        
        # Create message
        msg = create_text_message(
            sender=alice.address,
            recipient=bob.address,
            text="Hello Bob!",
            sign_func=alice.sign
        )
        
        # Serialize to bytes (for network transmission)
        wire_data = msg.to_bytes()
        
        # Deserialize
        received = MessagePayload.from_bytes(wire_data)
        
        # Verify
        assert received.id == msg.id
        assert received.sender == alice.address
        assert received.recipient == bob.address
        assert received.type == MessageType.TEXT
        
        # Verify signature
        from src.core.crypto import verify_signature
        signable = received.get_signable_content()
        is_valid = verify_signature(
            signable,
            received.signature,
            alice.signing_keys.public_key
        )
        assert is_valid is True
