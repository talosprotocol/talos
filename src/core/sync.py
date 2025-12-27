"""
Chain synchronization module for blockchain peer synchronization.

This module provides:
- ChainSynchronizer: Manages chain sync between peers
- Sync strategies: Full sync, partial sync, header-first sync
- Fork detection and resolution
"""

import asyncio
import logging
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Optional

from .blockchain import Blockchain, Block, ChainStatus
from .message import MessageType, MessagePayload

logger = logging.getLogger(__name__)


class SyncState(Enum):
    """State of chain synchronization."""

    IDLE = auto()
    REQUESTING_STATUS = auto()
    COMPARING = auto()
    DOWNLOADING = auto()
    VALIDATING = auto()
    APPLYING = auto()
    COMPLETE = auto()
    FAILED = auto()


class SyncProgress(BaseModel):
    """Progress of a sync operation."""

    state: SyncState = SyncState.IDLE
    peer_id: Optional[str] = None
    total_blocks: int = 0
    received_blocks: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def progress(self) -> float:
        """Get progress percentage (0.0 to 1.0)."""
        if self.total_blocks == 0:
            return 0.0
        return self.received_blocks / self.total_blocks

    @property
    def progress_percent(self) -> int:
        """Get progress as integer percentage."""
        return int(self.progress * 100)


class SyncRequest(BaseModel):
    """Request for blocks from a peer."""

    start_height: int
    end_height: int
    peer_id: str
    requested_at: float = Field(default_factory=lambda: __import__('time').time())

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def block_count(self) -> int:
        return self.end_height - self.start_height


# Type alias for message send function
MessageSender = Callable[[MessagePayload, str], Coroutine[Any, Any, bool]]


class ChainSynchronizer:
    """
    Manages blockchain synchronization between peers.
    
    Features:
    - Longest chain rule with total work comparison
    - Fork detection and resolution
    - Partial sync for efficiency
    - Concurrent sync from multiple peers
    """

    BLOCKS_PER_REQUEST = 100  # Max blocks to request at once
    SYNC_TIMEOUT = 30.0       # Seconds before timing out
    MAX_CONCURRENT_SYNCS = 3  # Max concurrent sync operations

    def __init__(
        self,
        blockchain: Blockchain,
        message_sender: Optional[MessageSender] = None,
        wallet_address: str = ""
    ) -> None:
        """
        Initialize chain synchronizer.
        
        Args:
            blockchain: The local blockchain to sync
            message_sender: Function to send messages to peers
            wallet_address: Local wallet address for signing
        """
        self.blockchain = blockchain
        self.message_sender = message_sender
        self.wallet_address = wallet_address

        # Sync state
        self._syncing = False
        self._sync_progress: dict[str, SyncProgress] = {}
        self._pending_requests: dict[str, SyncRequest] = {}
        self._received_blocks: dict[str, list[Block]] = {}

        # Peer chain status cache
        self._peer_status: dict[str, ChainStatus] = {}

        # Lock for concurrent access
        self._lock = asyncio.Lock()

    @property
    def is_syncing(self) -> bool:
        """Check if currently syncing."""
        return self._syncing

    def get_progress(self, peer_id: str) -> Optional[SyncProgress]:
        """Get sync progress for a peer."""
        return self._sync_progress.get(peer_id)

    def get_all_progress(self) -> dict[str, SyncProgress]:
        """Get all sync progress."""
        return self._sync_progress.copy()

    async def request_chain_status(self, peer_id: str) -> bool:
        """
        Request chain status from a peer.
        
        Args:
            peer_id: Peer to request from
            
        Returns:
            True if request was sent
        """
        if not self.message_sender:
            return False

        status = self.blockchain.get_status()

        message = MessagePayload.create(
            msg_type=MessageType.CHAIN_STATUS,
            sender=self.wallet_address,
            recipient=peer_id,
            content=b"",
            signature=b"",
            metadata={"status": status.to_dict(), "request": True}
        )

        self._sync_progress[peer_id] = SyncProgress(
            state=SyncState.REQUESTING_STATUS,
            peer_id=peer_id
        )

        return await self.message_sender(message, peer_id)

    async def handle_chain_status(
        self,
        message: MessagePayload,
        peer_id: str
    ) -> None:
        """
        Handle received chain status message.
        
        Args:
            message: The status message
            peer_id: Peer that sent the status
        """
        status_data = message.metadata.get("status")
        if not status_data:
            return

        try:
            remote_status = ChainStatus.from_dict(status_data)
        except (KeyError, TypeError) as e:
            logger.warning(f"Invalid chain status from {peer_id}: {e}")
            return

        # Cache peer status
        self._peer_status[peer_id] = remote_status

        # If this was a request, send our status back
        if message.metadata.get("request") and self.message_sender:
            response = MessagePayload.create(
                msg_type=MessageType.CHAIN_STATUS,
                sender=self.wallet_address,
                recipient=peer_id,
                content=b"",
                signature=b"",
                metadata={"status": self.blockchain.get_status().to_dict()}
            )
            await self.message_sender(response, peer_id)

        # Check if we should sync
        if self.blockchain.should_accept_chain(remote_status):
            logger.info(
                f"Peer {peer_id[:16]}... has better chain: "
                f"height={remote_status.height} work={remote_status.total_work}"
            )
            await self.start_sync(peer_id, remote_status)

    async def start_sync(
        self,
        peer_id: str,
        remote_status: ChainStatus
    ) -> bool:
        """
        Start syncing chain from a peer.
        
        Args:
            peer_id: Peer to sync from
            remote_status: Their chain status
            
        Returns:
            True if sync was started
        """
        async with self._lock:
            if self._syncing and len(self._sync_progress) >= self.MAX_CONCURRENT_SYNCS:
                logger.warning("Too many concurrent syncs, skipping")
                return False

            self._syncing = True

        progress = SyncProgress(
            state=SyncState.DOWNLOADING,
            peer_id=peer_id,
            total_blocks=remote_status.height - self.blockchain.height
        )
        self._sync_progress[peer_id] = progress
        self._received_blocks[peer_id] = []

        # Find common ancestor (where our chains diverge)
        common_height = await self._find_common_ancestor(peer_id, remote_status)

        # Request blocks from common ancestor
        start_height = common_height + 1
        end_height = remote_status.height + 1

        logger.info(
            f"Starting sync with {peer_id[:16]}...: "
            f"blocks {start_height} to {end_height}"
        )

        # Request in batches
        for batch_start in range(start_height, end_height, self.BLOCKS_PER_REQUEST):
            batch_end = min(batch_start + self.BLOCKS_PER_REQUEST, end_height)

            success = await self._request_blocks(peer_id, batch_start, batch_end)
            if not success:
                progress.state = SyncState.FAILED
                progress.error = "Failed to request blocks"
                return False

        return True

    async def _find_common_ancestor(
        self,
        peer_id: str,
        remote_status: ChainStatus
    ) -> int:
        """Find the highest common ancestor block."""
        # Simple approach: start from our latest block
        # In production, would use binary search with header requests
        return min(self.blockchain.height, 0)  # Simplified: sync from genesis

    async def _request_blocks(
        self,
        peer_id: str,
        start_height: int,
        end_height: int
    ) -> bool:
        """Request blocks from a peer."""
        if not self.message_sender:
            return False

        message = MessagePayload.create(
            msg_type=MessageType.CHAIN_REQUEST,
            sender=self.wallet_address,
            recipient=peer_id,
            content=b"",
            signature=b"",
            metadata={
                "start_height": start_height,
                "end_height": end_height
            }
        )

        request = SyncRequest(
            start_height=start_height,
            end_height=end_height,
            peer_id=peer_id
        )
        self._pending_requests[peer_id] = request

        return await self.message_sender(message, peer_id)

    async def handle_chain_request(
        self,
        message: MessagePayload,
        peer_id: str
    ) -> None:
        """
        Handle request for blocks.
        
        Args:
            message: The request message
            peer_id: Requesting peer
        """
        start_height = message.metadata.get("start_height", 0)
        end_height = message.metadata.get("end_height", 0)

        if end_height <= start_height:
            return

        # Limit response size
        max_blocks = min(end_height - start_height, self.BLOCKS_PER_REQUEST)
        blocks = self.blockchain.get_blocks_from(start_height, max_blocks)

        if not blocks or not self.message_sender:
            return

        # Send blocks
        response = MessagePayload.create(
            msg_type=MessageType.CHAIN_RESPONSE,
            sender=self.wallet_address,
            recipient=peer_id,
            content=b"",
            signature=b"",
            metadata={
                "start_height": start_height,
                "blocks": [b.to_dict() for b in blocks]
            }
        )

        await self.message_sender(response, peer_id)
        logger.debug(f"Sent {len(blocks)} blocks to {peer_id[:16]}...")

    async def handle_chain_response(
        self,
        message: MessagePayload,
        peer_id: str
    ) -> None:
        """
        Handle received blocks.
        
        Args:
            message: The response message
            peer_id: Sending peer
        """
        blocks_data = message.metadata.get("blocks", [])
        if not blocks_data:
            return

        progress = self._sync_progress.get(peer_id)
        if not progress:
            return

        try:
            blocks = [Block.from_dict(b) for b in blocks_data]
        except (KeyError, TypeError) as e:
            logger.error(f"Invalid blocks from {peer_id}: {e}")
            progress.state = SyncState.FAILED
            progress.error = f"Invalid block data: {e}"
            return

        # Add to received blocks
        if peer_id not in self._received_blocks:
            self._received_blocks[peer_id] = []
        self._received_blocks[peer_id].extend(blocks)

        progress.received_blocks += len(blocks)
        logger.debug(
            f"Received {len(blocks)} blocks from {peer_id[:16]}... "
            f"({progress.progress_percent}%)"
        )

        # Check if sync complete
        if progress.received_blocks >= progress.total_blocks:
            await self._apply_sync(peer_id)

    async def _apply_sync(self, peer_id: str) -> None:
        """Apply synced blocks to chain."""
        progress = self._sync_progress.get(peer_id)
        if not progress:
            return

        progress.state = SyncState.VALIDATING
        received = self._received_blocks.get(peer_id, [])

        if not received:
            progress.state = SyncState.FAILED
            progress.error = "No blocks received"
            return

        # Build new chain: keep our genesis, add received blocks
        new_chain = [self.blockchain.chain[0]] + received

        progress.state = SyncState.APPLYING

        # Attempt to replace chain
        if self.blockchain.replace_chain(new_chain):
            progress.state = SyncState.COMPLETE
            logger.info(
                f"Sync complete with {peer_id[:16]}...: "
                f"{len(new_chain)} blocks"
            )
        else:
            progress.state = SyncState.FAILED
            progress.error = "Chain replacement failed"
            logger.error(f"Failed to apply chain from {peer_id[:16]}...")

        # Cleanup
        async with self._lock:
            if peer_id in self._received_blocks:
                del self._received_blocks[peer_id]
            if peer_id in self._pending_requests:
                del self._pending_requests[peer_id]

            # Check if any syncs still active
            active = [p for p in self._sync_progress.values()
                     if p.state in (SyncState.DOWNLOADING, SyncState.VALIDATING)]
            if not active:
                self._syncing = False

    def reset(self) -> None:
        """Reset all sync state."""
        self._syncing = False
        self._sync_progress.clear()
        self._pending_requests.clear()
        self._received_blocks.clear()
        self._peer_status.clear()
