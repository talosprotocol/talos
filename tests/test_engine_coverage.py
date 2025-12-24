
import pytest
import asyncio
import time
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.engine.engine import TransmissionEngine, ReceivedMessage
from src.network.p2p import P2PNode
from src.core.blockchain import Blockchain
from src.core.crypto import Wallet, KeyPair
from src.network.peer import Peer
from src.core.message import MessagePayload, MessageType
from src.engine.media import MediaType

@pytest.fixture
def mock_wallet():
    wallet = MagicMock(spec=Wallet)
    wallet.address = "sender_addr"
    wallet.name = "TestNode"
    
    # Mock keys
    wallet.signing_keys = MagicMock(spec=KeyPair)
    wallet.signing_keys.public_key = b"signing_key"
    wallet.signing_keys.private_key = b"private_key"
    
    wallet.encryption_keys = MagicMock(spec=KeyPair)
    wallet.encryption_keys.public_key = b"encryption_key"
    wallet.encryption_keys.private_key = b"enc_priv_key"
    
    wallet.sign.return_value = b"signature"
    
    return wallet

@pytest.fixture
def mock_p2p():
    node = MagicMock(spec=P2PNode)
    node.on_message = MagicMock()
    # Ensure background tasks don't fail
    node.send_message = AsyncMock(return_value=True)
    node.broadcast = AsyncMock(return_value=1)
    return node

@pytest.fixture
def mock_blockchain():
    bc = MagicMock(spec=Blockchain)
    bc.add_data = MagicMock()
    return bc

@pytest.fixture
def engine(mock_wallet, mock_p2p, mock_blockchain):
    return TransmissionEngine(mock_wallet, mock_p2p, mock_blockchain)

@pytest.mark.asyncio
class TestTransmissionEngine:
    async def test_init(self, engine, mock_p2p):
        assert engine.downloads_dir.exists()
        mock_p2p.on_message.assert_called_once()
        assert len(engine._message_callbacks) == 0

    async def test_callbacks(self, engine):
        cb = AsyncMock()
        engine.on_message(cb)
        assert cb in engine._message_callbacks
        
        cb2 = AsyncMock()
        engine.on_file(cb2)
        assert cb2 in engine._file_callbacks
        
        cb3 = AsyncMock()
        engine.on_mcp_message(cb3)
        assert cb3 in engine._mcp_callbacks

    async def test_send_text_peer_not_found(self, engine, mock_p2p):
        mock_p2p.get_peer.return_value = None
        result = await engine.send_text("unknown", "hello")
        assert result is False

    async def test_send_text_success(self, engine, mock_p2p):
        peer = MagicMock(spec=Peer)
        peer.id = "peer_id"
        peer.encryption_key = b"peer_key"
        mock_p2p.get_peer.return_value = peer
        
        with patch("src.engine.engine.derive_shared_secret", return_value=b"secret"), \
             patch("src.engine.engine.encrypt_message", return_value=(b"nonce", b"encrypted")):
             
            result = await engine.send_text("peer_id", "hello", encrypt=True)
            
            assert result is True
            mock_p2p.send_message.assert_called_once()
            args, _ = mock_p2p.send_message.call_args
            msg = args[0]
            assert isinstance(msg, MessagePayload)
            assert msg.type == MessageType.TEXT
            assert msg.content == b"encrypted"

    async def test_broadcast_text(self, engine, mock_p2p):
        result = await engine.broadcast_text("hello")
        assert result == 1
        mock_p2p.broadcast.assert_called_once()

    async def test_handle_incoming_text(self, engine):
        # Setup peer
        peer = MagicMock(spec=Peer)
        peer.id = "peer_id"
        peer.public_key = b"pub_key"
        peer.encryption_key = b"enc_key"
        
        # Setup message
        msg = MessagePayload(
            id="msg_id",
            type=MessageType.TEXT,
            sender="peer_id",
            recipient="me",
            timestamp=time.time(),
            content=b"encrypted",
            signature=b"sig",
            nonce=b"nonce",
            metadata={"name": "Sender"}
        )
        
        # Mock callbacks
        callback = AsyncMock()
        engine.on_message(callback)
        
        with patch("src.engine.engine.verify_signature", return_value=True), \
             patch("src.engine.engine.derive_shared_secret", return_value=b"secret"), \
             patch("src.engine.engine.decrypt_message", return_value=b"decrypted"):
             
            await engine._handle_incoming(msg, peer)
            
            callback.assert_called_once()
            args, _ = callback.call_args
            received = args[0]
            assert isinstance(received, ReceivedMessage)
            assert received.content == "decrypted"
            assert received.sender == "peer_id"

    async def test_handle_incoming_files_start(self, engine):
        # Setup peer
        peer = MagicMock(spec=Peer)
        peer.id = "peer_id"
        peer.public_key = b"pub_key"
        
        # Setup message
        metadata = {
            "transfer_id": "tx1",
            "media_info": {
                "filename": "test.txt",
                "size": 100,
                "mime_type": "text/plain",
                "media_type": "DOCUMENT", 
                "file_hash": "hash",
                "chunk_count": 1,
                "chunk_size": 100
            }
        }
        msg = MessagePayload(
            id="msg_id",
            type=MessageType.FILE,
            sender="peer_id",
            recipient="me",
            timestamp=time.time(),
            content=b"",
            signature=b"sig",
            metadata=metadata
        )
        
        with patch("src.engine.engine.verify_signature", return_value=True):
             await engine._handle_incoming(msg, peer)
             
        # Check transfer manager has transfer
        transfer = engine.transfer_manager.get_transfer("tx1")
        assert transfer is not None
        assert transfer.media_info.filename == "test.txt"
