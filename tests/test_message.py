"""
Tests for the message protocol module.
"""

import pytest
import time

from src.core.message import (
    MessageType,
    ChunkInfo,
    MessagePayload,
    create_text_message,
    create_ack_message,
)
from src.core.crypto import Wallet


class TestMessageType:
    """Tests for MessageType enum."""
    
    def test_message_types_exist(self):
        """Test that required message types are defined."""
        assert MessageType.TEXT
        assert MessageType.ACK
        assert MessageType.STREAM_START
        assert MessageType.STREAM_CHUNK
        assert MessageType.STREAM_END


class TestChunkInfo:
    """Tests for ChunkInfo class."""
    
    def test_chunk_info_creation(self):
        """Test ChunkInfo can be created."""
        info = ChunkInfo(
            sequence=0,
            total=10,
            stream_id="test-stream",
            hash="abc123"
        )
        
        assert info.sequence == 0
        assert info.total == 10
        assert info.stream_id == "test-stream"
    
    def test_chunk_info_serialization(self):
        """Test ChunkInfo to/from dict."""
        original = ChunkInfo(
            sequence=5,
            total=100,
            stream_id="stream-1",
            hash="def456"
        )
        
        data = original.to_dict()
        restored = ChunkInfo.from_dict(data)
        
        assert restored.sequence == original.sequence
        assert restored.total == original.total
        assert restored.stream_id == original.stream_id


class TestMessagePayload:
    """Tests for MessagePayload class."""
    
    def test_message_creation(self):
        """Test message payload can be created."""
        msg = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender="sender123",
            recipient="recipient456",
            content=b"Hello!",
            signature=b"sig"
        )
        
        assert msg.type == MessageType.TEXT
        assert msg.sender == "sender123"
        assert msg.recipient == "recipient456"
        assert msg.content == b"Hello!"
        assert len(msg.id) > 0
        assert msg.timestamp > 0
    
    def test_message_json_serialization(self):
        """Test message JSON serialization."""
        original = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender="sender",
            recipient="recipient",
            content=b"Test content",
            signature=b"signature",
            nonce=b"123456789012"  # 12 bytes
        )
        
        json_str = original.to_json()
        restored = MessagePayload.from_json(json_str)
        
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.content == original.content
        assert restored.nonce == original.nonce
    
    def test_message_bytes_serialization(self):
        """Test message binary serialization (MessagePack)."""
        original = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender="sender",
            recipient="recipient",
            content=b"Binary content",
            signature=b"sig"
        )
        
        data = original.to_bytes()
        restored = MessagePayload.from_bytes(data)
        
        assert restored.id == original.id
        assert restored.content == original.content
    
    def test_broadcast_message(self):
        """Test broadcast message detection."""
        msg = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender="sender",
            recipient="*",
            content=b"Broadcast!",
            signature=b"sig"
        )
        
        assert msg.is_broadcast is True
    
    def test_streaming_message(self):
        """Test streaming message detection."""
        msg = MessagePayload.create(
            msg_type=MessageType.STREAM_CHUNK,
            sender="sender",
            recipient="recipient",
            content=b"chunk data",
            signature=b"sig",
            chunk_info=ChunkInfo(
                sequence=1,
                total=10,
                stream_id="stream-1",
                hash="abc"
            )
        )
        
        assert msg.is_streaming is True
    
    def test_signable_content(self):
        """Test signable content is consistent."""
        msg = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender="sender",
            recipient="recipient",
            content=b"Test",
            signature=b"sig"
        )
        
        signable1 = msg.get_signable_content()
        signable2 = msg.get_signable_content()
        
        assert signable1 == signable2


class TestMessageHelpers:
    """Tests for message creation helpers."""
    
    def test_create_text_message(self):
        """Test text message creation helper."""
        wallet = Wallet.generate("Test")
        
        msg = create_text_message(
            sender=wallet.address,
            recipient="recipient123",
            text="Hello, World!",
            sign_func=wallet.sign
        )
        
        assert msg.type == MessageType.TEXT
        assert msg.sender == wallet.address
        assert b"Hello, World!" in msg.content or msg.content == b"Hello, World!"
    
    def test_create_ack_message(self):
        """Test ACK message creation helper."""
        wallet = Wallet.generate("Test")
        
        ack = create_ack_message(
            sender=wallet.address,
            recipient="original_sender",
            original_message_id="msg-123",
            sign_func=wallet.sign
        )
        
        assert ack.type == MessageType.ACK
        assert b"msg-123" in ack.content
