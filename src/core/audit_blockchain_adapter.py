"""
Adapter to use Blockchain as storage for AuditStore.
"""
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from .audit_plane import AuditStore, AuditEvent, AuditEventType
from .blockchain import Blockchain

logger = logging.getLogger(__name__)

class BlockchainAuditStore(AuditStore):
    """
    AuditStore implementation backed by a Blockchain.
    Events are stored as data messages in blocks.
    """

    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

    def append(self, event: AuditEvent) -> None:
        """Append an audit event to the blockchain."""
        # Convert to dict
        data = event.to_dict()
        # Add type marker
        data["type"] = "audit_event"
        
        # Add to blockchain mempool
        success = self.blockchain.add_data(data)
        if not success:
            logger.error("Failed to add audit event to blockchain")
            return
            
        # Mine immediately for "real-time" feel in this demo
        # in production, this would be a background task
        self.blockchain.mine_pending()

    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events from blockchain."""
        results = []
        
        # Iterate backwards from latest block
        # Skip genesis (index 0)
        for i in range(len(self.blockchain.chain) - 1, 0, -1):
            block = self.blockchain.chain[i]
            if "messages" not in block.data:
                continue
                
            # Iterate messages in block (reverse order for newest first)
            for msg in reversed(block.data["messages"]):
                if not isinstance(msg, dict):
                    continue
                    
                # Check if it's an audit event
                # (either explicit type or by schema heuristic)
                if msg.get("type") != "audit_event" and "event_id" not in msg:
                    continue
                    
                try:
                    event = AuditEvent.from_dict(msg)
                except Exception:
                    continue
                
                # Filters
                if agent_id and event.agent_id != agent_id:
                    continue
                if event_type and event.event_type != event_type:
                    continue
                if after and event.timestamp <= after:
                    continue
                if before and event.timestamp >= before:
                    continue
                    
                results.append(event)
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
                
        return results

    def count(self) -> int:
        """Count total audit events."""
        count = 0
        for block in self.blockchain.chain[1:]:
            if "messages" in block.data:
                for msg in block.data["messages"]:
                    if isinstance(msg, dict) and msg.get("event_id"):
                        count += 1
        return count
