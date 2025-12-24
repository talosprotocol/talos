"""
Tests for chain synchronization module.

These tests cover:
- SyncState enum
- SyncProgress dataclass  
- SyncRequest dataclass
- ChainSynchronizer basic operations
"""

import pytest
from src.core.sync import (
    SyncState,
    SyncProgress,
    SyncRequest,
    ChainSynchronizer,
)
from src.core.blockchain import Blockchain


class TestSyncState:
    """Tests for SyncState enum."""
    
    def test_all_states_exist(self):
        """All sync states are defined."""
        assert SyncState.IDLE is not None
        assert SyncState.REQUESTING_STATUS is not None
        assert SyncState.COMPARING is not None
        assert SyncState.DOWNLOADING is not None
        assert SyncState.VALIDATING is not None
        assert SyncState.APPLYING is not None
        assert SyncState.COMPLETE is not None
        assert SyncState.FAILED is not None


class TestSyncProgress:
    """Tests for SyncProgress dataclass."""
    
    def test_default_values(self):
        """Default progress values."""
        progress = SyncProgress()
        assert progress.state == SyncState.IDLE
        assert progress.peer_id is None
        assert progress.total_blocks == 0
        assert progress.received_blocks == 0
        assert progress.error is None
    
    def test_progress_zero_total(self):
        """Progress with zero total blocks."""
        progress = SyncProgress()
        assert progress.progress == 0.0
        assert progress.progress_percent == 0
    
    def test_progress_calculation(self):
        """Progress percentage calculation."""
        progress = SyncProgress(
            total_blocks=100,
            received_blocks=50
        )
        assert progress.progress == 0.5
        assert progress.progress_percent == 50
    
    def test_progress_complete(self):
        """100% progress."""
        progress = SyncProgress(
            total_blocks=10,
            received_blocks=10
        )
        assert progress.progress == 1.0
        assert progress.progress_percent == 100
    
    def test_progress_with_error(self):
        """Progress with error state."""
        progress = SyncProgress(
            state=SyncState.FAILED,
            error="Connection lost"
        )
        assert progress.state == SyncState.FAILED
        assert progress.error == "Connection lost"


class TestSyncRequest:
    """Tests for SyncRequest dataclass."""
    
    def test_basic_request(self):
        """Basic request creation."""
        request = SyncRequest(
            start_height=10,
            end_height=20,
            peer_id="peer123"
        )
        assert request.start_height == 10
        assert request.end_height == 20
        assert request.peer_id == "peer123"
    
    def test_timestamp_set(self):
        """Request timestamp is set."""
        request = SyncRequest(
            start_height=0,
            end_height=10,
            peer_id="peer"
        )
        assert request.requested_at > 0


class TestChainSynchronizer:
    """Tests for ChainSynchronizer class."""
    
    def test_initialization(self):
        """Initialize synchronizer."""
        bc = Blockchain(difficulty=1)
        sync = ChainSynchronizer(bc)
        
        assert sync.blockchain == bc
        assert sync.is_syncing is False
    
    def test_get_all_progress(self):
        """Get all progress returns dict."""
        bc = Blockchain(difficulty=1)
        sync = ChainSynchronizer(bc)
        
        all_progress = sync.get_all_progress()
        assert isinstance(all_progress, dict)
    
    def test_reset(self):
        """Reset synchronizer state."""
        bc = Blockchain(difficulty=1)
        sync = ChainSynchronizer(bc)
        sync.reset()
        assert sync.is_syncing is False


class TestChainSynchronizerAsync:
    """Tests for async sync operations."""
    
    @pytest.mark.asyncio
    async def test_request_chain_status_no_sender(self):
        """Request status without sender returns False."""
        bc = Blockchain(difficulty=1)
        sync = ChainSynchronizer(bc)
        
        result = await sync.request_chain_status("peer1")
        assert result is False
