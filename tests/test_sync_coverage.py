
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.core.sync import ChainSynchronizer, SyncState, SyncProgress, SyncRequest, MessageType
from src.core.blockchain import Blockchain, ChainStatus, Block
from src.core.message import MessagePayload

@pytest.fixture
def mock_blockchain():
    bc = MagicMock(spec=Blockchain)
    bc.height = 5
    bc.get_status.return_value = ChainStatus(
        height=5, 
        total_work=100, 
        latest_hash="hash5",
        genesis_hash="genesis",
        difficulty=2
    )
    bc.should_accept_chain.return_value = True
    bc.replace_chain.return_value = True
    bc.chain = [MagicMock(spec=Block)] # Genesis
    return bc

@pytest.fixture
def message_sender():
    return AsyncMock(return_value=True)

@pytest.fixture
def synchronizer(mock_blockchain, message_sender):
    return ChainSynchronizer(
        blockchain=mock_blockchain,
        message_sender=message_sender,
        wallet_address="test_node"
    )

@pytest.mark.asyncio
class TestChainSynchronizer:
    async def test_init(self, synchronizer):
        assert synchronizer.is_syncing is False
        assert len(synchronizer.get_all_progress()) == 0

    async def test_request_chain_status_success(self, synchronizer, message_sender):
        success = await synchronizer.request_chain_status("peer1")
        assert success is True
        assert "peer1" in synchronizer._sync_progress
        assert synchronizer._sync_progress["peer1"].state == SyncState.REQUESTING_STATUS
        message_sender.assert_called_once()
        args, _ = message_sender.call_args
        msg = args[0]
        assert msg.type == MessageType.CHAIN_STATUS
        assert msg.metadata["request"] is True

    async def test_handle_chain_status_response(self, synchronizer):
        # Setup incoming status that is BETTER than ours
        status_data = {
            "height": 10,
            "total_work": 200,
            "latest_hash": "hash10",
            "genesis_hash": "genesis",
            "difficulty": 2
        }
        msg = MessagePayload(
            id="1", type=MessageType.CHAIN_STATUS, sender="peer1", recipient="me",
            timestamp=0, content=b"", signature=b"", 
            metadata={"status": status_data}
        )
        
        # Start sync logic should be triggered
        with patch.object(synchronizer, 'start_sync', new_callable=AsyncMock) as mock_start:
            await synchronizer.handle_chain_status(msg, "peer1")
            
            mock_start.assert_called_once()
            args, _ = mock_start.call_args
            assert args[0] == "peer1"
            assert args[1].height == 10

    async def test_handle_chain_status_request(self, synchronizer, message_sender):
        # Prevent auto-sync for this test
        synchronizer.blockchain.should_accept_chain.return_value = False
        
        # Peer asks for OUR status
        status_data = {
            "height": 1, 
            "total_work": 10, 
            "latest_hash": "h1",
            "genesis_hash": "genesis",
            "difficulty": 2
        }
        msg = MessagePayload(
            id="1", type=MessageType.CHAIN_STATUS, sender="peer1", recipient="me",
            timestamp=0, content=b"", signature=b"", 
            metadata={"status": status_data, "request": True}
        )
        
        await synchronizer.handle_chain_status(msg, "peer1")
        
        # Should send response
        message_sender.assert_called_once()
        args, _ = message_sender.call_args
        msg_sent = args[0]
        assert msg_sent.type == MessageType.CHAIN_STATUS
        assert "status" in msg_sent.metadata
        # Ensure we didn't accidentally request back
        assert "request" not in msg_sent.metadata or msg_sent.metadata.get("request") is None

    async def test_start_sync(self, synchronizer, message_sender):
        remote_status = ChainStatus(
            height=20, 
            total_work=500, 
            latest_hash="hash20",
            genesis_hash="genesis",
            difficulty=2
        )
        
        # Mock finding common ancestor
        with patch.object(synchronizer, '_find_common_ancestor', return_value=5):
            success = await synchronizer.start_sync("peer1", remote_status)
            
            assert success is True
            assert synchronizer.is_syncing is True
            assert "peer1" in synchronizer._sync_progress
            assert synchronizer._sync_progress["peer1"].state == SyncState.DOWNLOADING
            
            # Should have requested blocks
            message_sender.assert_called()
            # 20 - 5 = 15 blocks needed. BLOCKS_PER_REQUEST=100. So 1 request.
            args, _ = message_sender.call_args
            msg = args[0]
            assert msg.type == MessageType.CHAIN_REQUEST
            assert msg.metadata["start_height"] == 6
            assert msg.metadata["end_height"] == 21

    async def test_handle_chain_request(self, synchronizer, message_sender, mock_blockchain):
        # Setup blocks to return
        mock_blocks = [MagicMock(spec=Block), MagicMock(spec=Block)]
        for i, b in enumerate(mock_blocks):
            b.to_dict.return_value = {"index": i, "hash": f"h{i}"}
        mock_blockchain.get_blocks_from.return_value = mock_blocks
        
        msg = MessagePayload(
            id="1", type=MessageType.CHAIN_REQUEST, sender="peer1", recipient="me",
            timestamp=0, content=b"", signature=b"", 
            metadata={"start_height": 0, "end_height": 2}
        )
        
        await synchronizer.handle_chain_request(msg, "peer1")
        
        message_sender.assert_called_once()
        args, _ = message_sender.call_args
        msg_out = args[0]
        assert msg_out.type == MessageType.CHAIN_RESPONSE
        assert len(msg_out.metadata["blocks"]) == 2

    async def test_handle_chain_response_process(self, synchronizer):
        # Setup sync state
        progress = SyncProgress(state=SyncState.DOWNLOADING, peer_id="peer1", total_blocks=2, received_blocks=0)
        synchronizer._sync_progress["peer1"] = progress
        synchronizer._received_blocks["peer1"] = []
        
        # Incoming blocks
        block_data = [{"index": 6, "hash": "h6", "prev_hash": "h5", "timestamp": 123, "nonce": 1, "transactions": []}]
        msg = MessagePayload(
            id="1", type=MessageType.CHAIN_RESPONSE, sender="peer1", recipient="me",
            timestamp=0, content=b"", signature=b"", 
            metadata={"blocks": block_data}
        )
        
        # Mock Block.from_dict to return a mock
        with patch("src.core.sync.Block.from_dict") as mock_from_dict:
            mock_block = MagicMock(spec=Block)
            mock_from_dict.return_value = mock_block
            
            # We need total_blocks to match received for apply_sync to trigger
            # Total needed was set to 2, sending 1.
            await synchronizer.handle_chain_response(msg, "peer1")
            
            assert progress.received_blocks == 1
            assert synchronizer.blockchain.replace_chain.call_count == 0
            
            # Send second block
            block_data2 = [{"index": 7}]
            msg2 = MessagePayload(
                id="2", type=MessageType.CHAIN_RESPONSE, sender="peer1", recipient="me",
                timestamp=0, content=b"", signature=b"", 
                metadata={"blocks": block_data2}
            )
            
            await synchronizer.handle_chain_response(msg2, "peer1")
            
            assert progress.received_blocks == 2
            # Should trigger apply
            assert progress.state == SyncState.COMPLETE # or FAILED depending on replace_chain mock
            assert synchronizer.blockchain.replace_chain.call_count == 1

    async def test_reset(self, synchronizer):
        synchronizer._syncing = True
        synchronizer._sync_progress["p1"] = SyncProgress()
        
        synchronizer.reset()
        
        assert synchronizer.is_syncing is False
        assert len(synchronizer._sync_progress) == 0
