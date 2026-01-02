"""
Adapter to use Blockchain as storage for AuditStore.
"""
import logging
from typing import Optional
from datetime import datetime

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

    def _matches_filters(
        self,
        event: AuditEvent,
        agent_id: Optional[str],
        event_type: Optional[AuditEventType],
        after: Optional[datetime],
        before: Optional[datetime],
    ) -> bool:
        """Check if event matches all filter criteria."""
        if agent_id and event.agent_id != agent_id:
            return False
        if event_type and event.event_type != event_type:
            return False
        if after and event.timestamp <= after:
            return False
        if before and event.timestamp >= before:
            return False
        return True

    def _parse_audit_event(self, msg: dict) -> Optional[AuditEvent]:
        """Parse a message dict as an AuditEvent if valid."""
        if not isinstance(msg, dict):
            return None
        if msg.get("type") != "audit_event" and "event_id" not in msg:
            return None
        try:
            return AuditEvent.from_dict(msg)
        except Exception:
            return None

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
        
        for i in range(len(self.blockchain.chain) - 1, 0, -1):
            block = self.blockchain.chain[i]
            if "messages" not in block.data:
                continue
                
            for msg in reversed(block.data["messages"]):
                event = self._parse_audit_event(msg)
                if event is None:
                    continue
                
                if self._matches_filters(event, agent_id, event_type, after, before):
                    results.append(event)
                    if len(results) >= limit:
                        return results
                        
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
