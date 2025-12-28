"""
Transmission engine for the blockchain messaging protocol.

This module provides:
- TransmissionEngine: Unified interface for sending/receiving data
- Support for text and file transfers
- Automatic chunking for large payloads
- Encryption and signing
- Progress tracking for file transfers
"""

import asyncio
import logging
import uuid
from pydantic import BaseModel, ConfigDict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from ..core.blockchain import Blockchain
from ..core.crypto import (
    Wallet,
    derive_shared_secret,
    encrypt_message,
    decrypt_message,
    verify_signature,
)
from ..core.message import (
    MessagePayload,
    MessageType,
    ChunkInfo,
    create_ack_message,
)
from ..network.p2p import P2PNode
from ..network.peer import Peer
from .chunker import DataChunker, ChunkReassembler, Chunk, CHUNK_SIZE_TEXT
from .media import (
    MediaFile,
    MediaInfo,
    MediaType,
    MediaTransfer,
    TransferManager,
    get_chunk_size,
    MediaError,
)

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content that can be transmitted."""

    TEXT = auto()
    BINARY = auto()
    FILE = auto()
    MCP = auto()
    # Future content types
    AUDIO = auto()
    VIDEO = auto()


class ReceivedMessage(BaseModel):
    """A received and decrypted message."""

    id: str
    sender: str
    sender_name: Optional[str]
    content: str
    timestamp: float
    verified: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __repr__(self) -> str:
        sender_short = f"{self.sender[:8]}..." if len(self.sender) > 8 else self.sender
        name = f" ({self.sender_name})" if self.sender_name else ""
        return f"Message from {sender_short}{name}: {self.content[:50]}..."


class ReceivedMedia(BaseModel):
    """A received file/media."""

    id: str
    sender: str
    sender_name: Optional[str]
    filename: str
    mime_type: str
    media_type: MediaType
    size: int
    data: bytes
    file_hash: str
    timestamp: float
    verified: bool
    saved_path: Optional[Path] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def save(self, directory: Path, filename: Optional[str] = None) -> Path:
        """
        Save the received file to disk.
        
        Args:
            directory: Directory to save to
            filename: Optional filename override
            
        Returns:
            Path to saved file
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        save_name = filename or self.filename
        save_path = directory / save_name

        # Avoid overwriting
        if save_path.exists():
            stem = save_path.stem
            suffix = save_path.suffix
            counter = 1
            while save_path.exists():
                save_path = directory / f"{stem}_{counter}{suffix}"
                counter += 1

        with open(save_path, "wb") as f:
            f.write(self.data)

        self.saved_path = save_path
        logger.info(f"Saved file to {save_path}")
        return save_path

    @property
    def size_formatted(self) -> str:
        """Get human-readable file size."""
        from .media import format_file_size
        return format_file_size(self.size)

    def __repr__(self) -> str:
        sender_short = f"{self.sender[:8]}..." if len(self.sender) > 8 else self.sender
        return f"ReceivedMedia({self.filename}, {self.size_formatted}, from {sender_short})"


class MCPMessage(BaseModel):
    """A received MCP JSON-RPC message."""

    id: str
    sender: str
    content: dict[str, Any]  # Parsed JSON-RPC
    timestamp: float
    verified: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Type aliases for callbacks
MessageCallback = Callable[[ReceivedMessage], Coroutine[Any, Any, None]]
FileCallback = Callable[[ReceivedMedia], Coroutine[Any, Any, None]]
MCPCallback = Callable[[MCPMessage], Coroutine[Any, Any, None]]


class TransmissionEngine:
    """
    Main engine for transmitting and receiving messages and files.
    
    Provides a high-level interface for:
    - Sending encrypted text messages
    - Sending and receiving files (images, documents, audio, video)
    - Receiving and decrypting messages
    - Automatic chunking for large data
    - Progress tracking for file transfers
    - Recording messages to blockchain
    """

    def __init__(
        self,
        wallet: Wallet,
        p2p_node: P2PNode,
        blockchain: Optional[Blockchain] = None,
        downloads_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize transmission engine.
        
        Args:
            wallet: The user's identity wallet
            p2p_node: P2P networking node
            blockchain: Optional blockchain for message recording
            downloads_dir: Directory for saving received files
        """
        self.wallet = wallet
        self.p2p_node = p2p_node
        self.blockchain = blockchain or Blockchain(difficulty=2)
        self.downloads_dir = downloads_dir or Path.home() / ".bmp" / "downloads"

        # Ensure downloads directory exists
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # Chunking
        self.chunker = DataChunker(chunk_size=CHUNK_SIZE_TEXT)
        self.reassembler = ChunkReassembler()

        # File transfer management
        self.transfer_manager = TransferManager()

        # Callbacks
        self._message_callbacks: list[MessageCallback] = []
        self._file_callbacks: list[FileCallback] = []
        self._mcp_callbacks: list[MCPCallback] = []

        # Received files (in-memory for recent files)
        self._received_files: list[ReceivedMedia] = []
        self._max_received_files = 100  # Keep last 100 files in memory

        # Shared secrets cache (peer_id -> secret)
        self._shared_secrets: dict[str, bytes] = {}

        # Register P2P message handler
        self.p2p_node.on_message(self._handle_incoming)

    def on_message(self, callback: MessageCallback) -> None:
        """Register a callback for received messages."""
        self._message_callbacks.append(callback)

    def on_file(self, callback: FileCallback) -> None:
        """Register a callback for received files."""
        self._file_callbacks.append(callback)

    def on_mcp_message(self, callback: MCPCallback) -> None:
        """Register a callback for received MCP messages."""
        self._mcp_callbacks.append(callback)

    def _get_shared_secret(self, peer: Peer) -> Optional[bytes]:
        """Get or derive shared secret with a peer."""
        if not peer.encryption_key:
            return None

        if peer.id not in self._shared_secrets:
            self._shared_secrets[peer.id] = derive_shared_secret(
                self.wallet.encryption_keys.private_key,
                peer.encryption_key
            )

        return self._shared_secrets[peer.id]

    async def send_text(
        self,
        recipient_id: str,
        text: str,
        encrypt: bool = True
    ) -> bool:
        """
        Send a text message to a peer.
        
        Args:
            recipient_id: Recipient's peer ID (public key hex)
            text: Message text
            encrypt: Whether to encrypt the message
            
        Returns:
            True if sent successfully
        """
        peer = self.p2p_node.get_peer(recipient_id)
        if not peer:
            logger.error(f"Peer not found: {recipient_id[:16]}...")
            return False

        content = text.encode()
        nonce = None

        # Encrypt if requested and we have peer's encryption key
        if encrypt and peer.encryption_key:
            shared_secret = self._get_shared_secret(peer)
            if shared_secret:
                nonce, content = encrypt_message(content, shared_secret)

        # Create and sign message
        message = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender=self.wallet.address,
            recipient=recipient_id,
            content=content,
            signature=b"",  # Will be set below
            nonce=nonce,
            metadata={"name": self.wallet.name}
        )

        # Sign the message
        signable = message.get_signable_content()
        message.signature = self.wallet.sign(signable)

        # Record to blockchain
        self.blockchain.add_data({
            "type": "message",
            "id": message.id,
            "sender": message.sender,
            "recipient": message.recipient,
            "timestamp": message.timestamp
        })

        # Send via P2P
        success = await self.p2p_node.send_message(message, recipient_id)

        if success:
            logger.info(f"Sent message to {peer}")

        return success

    async def broadcast_text(self, text: str) -> int:
        """
        Broadcast a text message to all connected peers.
        
        Args:
            text: Message text
            
        Returns:
            Number of peers message was sent to
        """
        content = text.encode()

        message = MessagePayload.create(
            msg_type=MessageType.TEXT,
            sender=self.wallet.address,
            recipient="*",  # Broadcast
            content=content,
            signature=b"",
            metadata={"name": self.wallet.name}
        )

        signable = message.get_signable_content()
        message.signature = self.wallet.sign(signable)

        # Record to blockchain
        self.blockchain.add_data({
            "type": "broadcast",
            "id": message.id,
            "sender": message.sender,
            "timestamp": message.timestamp
        })

        return await self.p2p_node.broadcast(message)

    async def send_file(
        self,
        recipient_id: str,
        file_path: str | Path,
        encrypt: bool = True
    ) -> Optional[str]:
        """
        Send a file to a peer.
        
        Args:
            recipient_id: Recipient's peer ID (public key hex)
            file_path: Path to the file to send
            encrypt: Whether to encrypt the file content
            
        Returns:
            Transfer ID if transfer started, None on error
        """
        peer = self.p2p_node.get_peer(recipient_id)
        if not peer:
            logger.error(f"Peer not found: {recipient_id[:16]}...")
            return None

        try:
            # Load file and validate
            media_file = MediaFile.from_path(file_path)
            logger.info(
                f"Starting file transfer: {media_file.filename} "
                f"({media_file.size_formatted}) to {peer}"
            )

            # Create transfer
            transfer_id = str(uuid.uuid4())
            transfer = self.transfer_manager.create_send_transfer(
                transfer_id=transfer_id,
                media_file=media_file,
                peer_id=recipient_id
            )

            # Get shared secret for encryption
            shared_secret = None
            if encrypt and peer.encryption_key:
                shared_secret = self._get_shared_secret(peer)

            # Send file metadata first
            media_info = media_file.to_media_info()
            metadata = {
                "name": self.wallet.name,
                "transfer_id": transfer_id,
                "media_info": media_info.to_dict()
            }

            # Create FILE message with metadata
            file_msg = MessagePayload.create(
                msg_type=MessageType.FILE,
                sender=self.wallet.address,
                recipient=recipient_id,
                content=b"",  # No content in start message
                signature=b"",
                metadata=metadata
            )
            file_msg.signature = self.wallet.sign(file_msg.get_signable_content())

            # Record to blockchain
            self.blockchain.add_data({
                "type": "file_transfer",
                "id": transfer_id,
                "filename": media_info.filename,
                "size": media_info.size,
                "sender": self.wallet.address,
                "recipient": recipient_id,
                "timestamp": file_msg.timestamp
            })

            # Send metadata message
            if not await self.p2p_node.send_message(file_msg, recipient_id):
                transfer.fail("Failed to send file metadata")
                return None

            transfer.start()

            # Send file chunks
            await self._send_file_chunks(
                media_file=media_file,
                transfer=transfer,
                recipient_id=recipient_id,
                shared_secret=shared_secret
            )

            return transfer_id

        except MediaError as e:
            logger.error(f"File transfer error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during file transfer: {e}")
            return None

    async def _send_file_chunks(
        self,
        media_file: MediaFile,
        transfer: MediaTransfer,
        recipient_id: str,
        shared_secret: Optional[bytes] = None
    ) -> None:
        """Send file data in chunks."""
        chunk_size = get_chunk_size(media_file.media_type)
        chunk_num = 0
        total_chunks = transfer.media_info.chunk_count

        for chunk_data in media_file.read_chunks(chunk_size):
            # Encrypt chunk if we have a shared secret
            nonce = None
            content = chunk_data
            if shared_secret:
                nonce, content = encrypt_message(chunk_data, shared_secret)

            # Create chunk info
            chunk_info = ChunkInfo(
                sequence=chunk_num,
                total=total_chunks,
                stream_id=transfer.id,
                hash=""  # Will be calculated
            )

            # Create FILE_CHUNK message
            chunk_msg = MessagePayload.create(
                msg_type=MessageType.FILE_CHUNK,
                sender=self.wallet.address,
                recipient=recipient_id,
                content=content,
                signature=b"",
                nonce=nonce,
                chunk_info=chunk_info,
                metadata={"transfer_id": transfer.id}
            )
            chunk_msg.signature = self.wallet.sign(chunk_msg.get_signable_content())

            # Send chunk
            if not await self.p2p_node.send_message(chunk_msg, recipient_id):
                transfer.fail(f"Failed to send chunk {chunk_num}")
                return

            transfer.chunks_completed = chunk_num + 1
            transfer.bytes_transferred += len(chunk_data)
            chunk_num += 1

            # Log progress periodically
            if chunk_num % 10 == 0 or chunk_num == total_chunks:
                logger.debug(
                    f"Transfer {transfer.id[:8]}... progress: "
                    f"{transfer.progress_percent}%"
                )

            # Small delay to avoid overwhelming the receiver
            await asyncio.sleep(0.01)

        # Send FILE_COMPLETE message
        complete_msg = MessagePayload.create(
            msg_type=MessageType.FILE_COMPLETE,
            sender=self.wallet.address,
            recipient=recipient_id,
            content=b"",
            signature=b"",
            metadata={
                "transfer_id": transfer.id,
                "file_hash": media_file.file_hash
            }
        )
        complete_msg.signature = self.wallet.sign(complete_msg.get_signable_content())

        await self.p2p_node.send_message(complete_msg, recipient_id)
        transfer.complete()

        logger.info(
            f"File transfer complete: {media_file.filename} "
            f"({transfer.transfer_rate_formatted})"
        )

    def get_received_files(self) -> list[ReceivedMedia]:
        """Get list of recently received files."""
        return self._received_files.copy()

    def get_transfer(self, transfer_id: str) -> Optional[MediaTransfer]:
        """Get a transfer by ID."""
        return self.transfer_manager.get_transfer(transfer_id)

    def get_active_transfers(self) -> list[MediaTransfer]:
        """Get all active transfers."""
        return self.transfer_manager.get_active_transfers()

    async def _handle_incoming(
        self,
        message: MessagePayload,
        peer: Peer
    ) -> None:
        """Handle incoming message from P2P layer."""

        # Verify signature
        if not peer.public_key:
            logger.warning(f"No public key for peer {peer.id[:16]}...")
            return

        signable = message.get_signable_content()
        verified = verify_signature(signable, message.signature, peer.public_key)

        if not verified:
            logger.warning(f"Invalid signature from {peer}")
            return

        # Handle based on message type
        if message.type == MessageType.TEXT:
            await self._handle_text_message(message, peer, verified)

        elif message.type == MessageType.ACK:
            logger.debug(f"Received ACK from {peer}")

        elif message.type == MessageType.FILE:
            await self._handle_file_start(message, peer, verified)

        elif message.type == MessageType.FILE_CHUNK:
            await self._handle_file_chunk(message, peer)

        elif message.type == MessageType.FILE_COMPLETE:
            await self._handle_file_complete(message, peer, verified)

        elif message.type in (
            MessageType.STREAM_START,
            MessageType.STREAM_CHUNK,
            MessageType.STREAM_END
        ):
            await self._handle_stream_message(message, peer)

        elif message.type in (MessageType.MCP_MESSAGE, MessageType.MCP_RESPONSE, MessageType.MCP_ERROR):
            await self._handle_mcp_message(message, peer, verified)

    async def _handle_text_message(
        self,
        message: MessagePayload,
        peer: Peer,
        verified: bool
    ) -> None:
        """Handle received text message."""
        content = message.content

        # Decrypt if encrypted
        if message.nonce and peer.encryption_key:
            shared_secret = self._get_shared_secret(peer)
            if shared_secret:
                try:
                    content = decrypt_message(content, shared_secret, message.nonce)
                except Exception as e:
                    logger.error(f"Failed to decrypt message: {e}")
                    return

        # Decode text
        try:
            text = content.decode()
        except UnicodeDecodeError:
            logger.error("Failed to decode message content")
            return

        # Create received message
        received = ReceivedMessage(
            id=message.id,
            sender=message.sender,
            sender_name=message.metadata.get("name"),
            content=text,
            timestamp=message.timestamp,
            verified=verified
        )

        # Record to blockchain
        self.blockchain.add_data({
            "type": "received",
            "id": message.id,
            "sender": message.sender,
            "timestamp": message.timestamp
        })

        # Notify callbacks
        for callback in self._message_callbacks:
            try:
                await callback(received)
            except Exception as e:
                logger.error(f"Message callback error: {e}")

        # Send ACK
        ack = create_ack_message(
            sender=self.wallet.address,
            recipient=message.sender,
            original_message_id=message.id,
            sign_func=self.wallet.sign
        )
        await self.p2p_node.send_message(ack, peer.id)

    async def _handle_file_start(
        self,
        message: MessagePayload,
        peer: Peer,
        verified: bool
    ) -> None:
        """Handle incoming file transfer start message."""
        transfer_id = message.metadata.get("transfer_id")
        media_info_data = message.metadata.get("media_info")

        if not transfer_id or not media_info_data:
            logger.error("Invalid FILE message: missing transfer_id or media_info")
            return

        try:
            media_info = MediaInfo.from_dict(media_info_data)
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid media_info: {e}")
            return

        # Create receive transfer
        transfer = self.transfer_manager.create_receive_transfer(
            transfer_id=transfer_id,
            media_info=media_info,
            peer_id=peer.id
        )
        transfer.start()

        logger.info(
            f"Receiving file from {peer}: {media_info.filename} "
            f"({media_info.size_formatted})"
        )

        # Record to blockchain
        self.blockchain.add_data({
            "type": "file_receive",
            "id": transfer_id,
            "filename": media_info.filename,
            "size": media_info.size,
            "sender": message.sender,
            "recipient": self.wallet.address,
            "timestamp": message.timestamp
        })

    async def _handle_file_chunk(
        self,
        message: MessagePayload,
        peer: Peer
    ) -> None:
        """Handle incoming file chunk."""
        transfer_id = message.metadata.get("transfer_id")
        if not transfer_id:
            logger.error("FILE_CHUNK missing transfer_id")
            return

        transfer = self.transfer_manager.get_transfer(transfer_id)
        if not transfer:
            logger.warning(f"Unknown transfer: {transfer_id[:16]}...")
            return

        # Decrypt if encrypted
        content = message.content
        if message.nonce and peer.encryption_key:
            shared_secret = self._get_shared_secret(peer)
            if shared_secret:
                try:
                    content = decrypt_message(content, shared_secret, message.nonce)
                except Exception as e:
                    logger.error(f"Failed to decrypt chunk: {e}")
                    transfer.fail(f"Decryption failed: {e}")
                    return

        # Add chunk to transfer
        transfer.add_chunk(content)

        # Log progress periodically
        if transfer.chunks_completed % 10 == 0:
            logger.debug(
                f"Receiving {transfer.media_info.filename}: "
                f"{transfer.progress_percent}%"
            )

    async def _handle_file_complete(
        self,
        message: MessagePayload,
        peer: Peer,
        verified: bool
    ) -> None:
        """Handle file transfer completion."""
        transfer_id = message.metadata.get("transfer_id")
        message.metadata.get("file_hash")

        if not transfer_id:
            logger.error("FILE_COMPLETE missing transfer_id")
            return

        transfer = self.transfer_manager.get_transfer(transfer_id)
        if not transfer:
            logger.warning(f"Unknown transfer: {transfer_id[:16]}...")
            return

        # Verify hash
        if not transfer.verify_hash():
            logger.error(
                f"File hash verification failed for {transfer.media_info.filename}"
            )
            transfer.fail("Hash verification failed")
            return

        transfer.complete()

        # Create ReceivedMedia
        received = ReceivedMedia(
            id=transfer_id,
            sender=message.sender,
            sender_name=message.metadata.get("name"),
            filename=transfer.media_info.filename,
            mime_type=transfer.media_info.mime_type,
            media_type=transfer.media_info.media_type,
            size=transfer.media_info.size,
            data=transfer.data,
            file_hash=transfer.media_info.file_hash,
            timestamp=message.timestamp,
            verified=verified
        )

        # Auto-save to downloads directory
        try:
            received.save(self.downloads_dir)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")

        # Add to received files list
        self._received_files.append(received)
        if len(self._received_files) > self._max_received_files:
            self._received_files.pop(0)

        logger.info(
            f"File received: {received.filename} ({received.size_formatted}) "
            f"from {peer}"
        )

        # Notify callbacks
        for callback in self._file_callbacks:
            try:
                await callback(received)
            except Exception as e:
                logger.error(f"File callback error: {e}")

        # Send ACK
        ack = create_ack_message(
            sender=self.wallet.address,
            recipient=message.sender,
            original_message_id=message.id,
            sign_func=self.wallet.sign
        )
        await self.p2p_node.send_message(ack, peer.id)

    async def _handle_stream_message(
        self,
        message: MessagePayload,
        peer: Peer
    ) -> None:
        """Handle streaming message (for future audio/video)."""
        if not message.chunk_info:
            return

        chunk = Chunk(
            stream_id=message.chunk_info.stream_id,
            sequence=message.chunk_info.sequence,
            total=message.chunk_info.total,
            data=message.content
        )

        # Add to reassembler
        completed = self.reassembler.add_chunk(chunk)

        if completed:
            # Future: Handle completed audio/video stream
            pass

    async def send_mcp(
        self,
        recipient_id: str,
        content: dict[str, Any],
        is_response: bool = False
    ) -> bool:
        """
        Send an MCP JSON-RPC message.
        
        Args:
            recipient_id: Recipient's public key
            content: JSON-RPC dict
            is_response: Whether this is a response to a previous request
            
        Returns:
            True if sent successfully
        """
        import json

        peer = self.p2p_node.get_peer(recipient_id)
        if not peer:
            logger.error(f"Peer not found: {recipient_id[:16]}...")
            return False

        import hashlib
        
        # Calculate Audit Hash (SHA256 of plaintext content)
        # Canonical JSON for consistent hashing
        canonical_content = json.dumps(content, sort_keys=True, separators=(',', ':')).encode()
        content_hash = hashlib.sha256(canonical_content).hexdigest()

        # Serialize and encode for wire
        msg_content = json.dumps(content).encode()

        # Encrypt
        nonce = None
        if peer.encryption_key:
            shared_secret = self._get_shared_secret(peer)
            if shared_secret:
                nonce, msg_content = encrypt_message(msg_content, shared_secret)

        # Create message
        msg_type_enum = MessageType.MCP_RESPONSE if is_response else MessageType.MCP_MESSAGE
        
        message = MessagePayload.create(
            msg_type=msg_type_enum,
            sender=self.wallet.address,
            recipient=recipient_id,
            content=msg_content,
            signature=b"",
            nonce=nonce,
            metadata={
                "audit_hash": content_hash,
                "tool": content.get("tool") or content.get("params", {}).get("name"),
                "method": content.get("method"),
            }
        )

        # Sign
        message.signature = self.wallet.sign(message.get_signable_content())

        # Audit Log to Blockchain (Local Node)
        # This ensures the Dashboard on this node sees the outgoing request/response
        self.blockchain.add_data({
            "type": "mcp_response" if is_response else "mcp_request",
            "id": message.id,
            "sender": self.wallet.address,
            "recipient": recipient_id,
            "timestamp": message.timestamp,
            "hash": content_hash,
            "tool": message.metadata["tool"],
            "method": message.metadata["method"],
            # Log params/result only if not sensitive? 
            # User complained about empty fields. Let's include them for now.
            "params": content.get("params") if not is_response else None,
            "result": content.get("result") if is_response else None,
            "error": content.get("error") if is_response else None,
        })

        # Send
        return await self.p2p_node.send_message(message, recipient_id)

    async def _handle_mcp_message(
        self,
        message: MessagePayload,
        peer: Peer,
        verified: bool
    ) -> None:
        """Handle incoming MCP message."""
        import json

        content_bytes = message.content

        # Decrypt
        if message.nonce and peer.encryption_key:
            shared_secret = self._get_shared_secret(peer)
            if shared_secret:
                try:
                    content_bytes = decrypt_message(content_bytes, shared_secret, message.nonce)
                except Exception as e:
                    logger.error(f"Failed to decrypt MCP message: {e}")
                    return

        try:
            content = json.loads(content_bytes.decode())
        except Exception:
            logger.error("Failed to decode MCP message content")
            return

        mcp_msg = MCPMessage(
            id=message.id,
            sender=message.sender,
            content=content,
            timestamp=message.timestamp,
            verified=verified
        )

        # Audit Log to Blockchain (Local Node)
        # Log incoming requests/responses
        msg_type_str = "mcp_response" if message.type == MessageType.MCP_RESPONSE else "mcp_request"
        # Extract audit hash from metadata if present, else calculate
        audit_hash = message.metadata.get("audit_hash")
        if not audit_hash:
             import hashlib
             canonical_content = json.dumps(content, sort_keys=True, separators=(',', ':')).encode()
             audit_hash = hashlib.sha256(canonical_content).hexdigest()

        self.blockchain.add_data({
            "type": f"received_{msg_type_str}",
            "id": message.id,
            "sender": message.sender,
            "recipient": self.wallet.address,
            "timestamp": message.timestamp,
            "hash": audit_hash,
            "tool": message.metadata.get("tool"),
            "method": message.metadata.get("method"),
            "params": content.get("params") if msg_type_str == "mcp_request" else None,
            "result": content.get("result") if msg_type_str == "mcp_response" else None,
            "error": content.get("error") if msg_type_str == "mcp_response" else None,
        })

        for callback in self._mcp_callbacks:
            try:
                await callback(mcp_msg)
            except Exception as e:
                logger.error(f"MCP callback error: {e}")

    def mine_pending(self) -> None:
        """Mine pending blockchain transactions."""
        block = self.blockchain.mine_pending()
        if block:
            logger.info(f"Mined block #{block.index}: {block.hash[:16]}...")

    def get_message_history(self) -> list[dict]:
        """Get message history from blockchain."""
        return self.blockchain.get_messages()
