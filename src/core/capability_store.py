"""
LMDB-backed storage for capability tokens.

Provides persistent storage for:
- Issued capabilities
- Revocation list
- Capability index by subject/scope

Usage:
    store = CapabilityStore("/path/to/data/capabilities")
    await store.save(capability)
    cap = await store.get(capability_id)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator

try:
    import lmdb
    LMDB_AVAILABLE = True
except ImportError:
    LMDB_AVAILABLE = False

from .capability import Capability, RevocationEntry

logger = logging.getLogger(__name__)


class CapabilityStore:
    """
    LMDB-backed capability storage.
    
    Databases:
    - capabilities: id -> Capability JSON
    - revocations: id -> RevocationEntry JSON
    - by_subject: subject -> list of capability IDs
    - by_scope: scope -> list of capability IDs
    """
    
    def __init__(self, path: str, map_size: int = 100 * 1024 * 1024):
        """
        Initialize capability store.
        
        Args:
            path: Directory for LMDB files
            map_size: Maximum database size (default 100MB)
        """
        if not LMDB_AVAILABLE:
            raise RuntimeError("lmdb package not installed. Run: pip install lmdb")
        
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        self.env = lmdb.open(
            str(self.path),
            map_size=map_size,
            max_dbs=4,
            subdir=True,
        )
        
        # Open named databases
        self.db_capabilities = self.env.open_db(b"capabilities")
        self.db_revocations = self.env.open_db(b"revocations")
        self.db_by_subject = self.env.open_db(b"by_subject")
        self.db_by_scope = self.env.open_db(b"by_scope")
        
        logger.info(f"Initialized CapabilityStore at {self.path}")
    
    def save(self, capability: Capability) -> None:
        """Save a capability to storage."""
        with self.env.begin(write=True) as txn:
            # Store capability
            key = capability.id.encode()
            value = json.dumps(capability.to_dict()).encode()
            txn.put(key, value, db=self.db_capabilities)
            
            # Index by subject
            self._add_to_index(txn, self.db_by_subject, capability.subject, capability.id)
            
            # Index by scope (store under each scope level)
            scope_parts = capability.scope.split("/")
            for i in range(len(scope_parts)):
                scope_prefix = "/".join(scope_parts[:i+1])
                self._add_to_index(txn, self.db_by_scope, scope_prefix, capability.id)
        
        logger.debug(f"Saved capability {capability.id}")
    
    def get(self, capability_id: str) -> Optional[Capability]:
        """Get a capability by ID."""
        with self.env.begin() as txn:
            value = txn.get(capability_id.encode(), db=self.db_capabilities)
            if value is None:
                return None
            data = json.loads(value.decode())
            return Capability.from_dict(data)
    
    def delete(self, capability_id: str) -> bool:
        """Delete a capability."""
        cap = self.get(capability_id)
        if cap is None:
            return False
        
        with self.env.begin(write=True) as txn:
            txn.delete(capability_id.encode(), db=self.db_capabilities)
            self._remove_from_index(txn, self.db_by_subject, cap.subject, capability_id)
            
            scope_parts = cap.scope.split("/")
            for i in range(len(scope_parts)):
                scope_prefix = "/".join(scope_parts[:i+1])
                self._remove_from_index(txn, self.db_by_scope, scope_prefix, capability_id)
        
        logger.debug(f"Deleted capability {capability_id}")
        return True
    
    def save_revocation(self, entry: RevocationEntry) -> None:
        """Save a revocation entry."""
        with self.env.begin(write=True) as txn:
            key = entry.capability_id.encode()
            value = json.dumps({
                "capability_id": entry.capability_id,
                "revoked_at": entry.revoked_at.isoformat(),
                "reason": entry.reason,
                "revoked_by": entry.revoked_by,
            }).encode()
            txn.put(key, value, db=self.db_revocations)
        
        logger.debug(f"Saved revocation for {entry.capability_id}")
    
    def get_revocation(self, capability_id: str) -> Optional[RevocationEntry]:
        """Get revocation entry for a capability."""
        with self.env.begin() as txn:
            value = txn.get(capability_id.encode(), db=self.db_revocations)
            if value is None:
                return None
            data = json.loads(value.decode())
            return RevocationEntry(
                capability_id=data["capability_id"],
                revoked_at=datetime.fromisoformat(data["revoked_at"]),
                reason=data["reason"],
                revoked_by=data["revoked_by"],
            )
    
    def is_revoked(self, capability_id: str) -> bool:
        """Check if a capability is revoked."""
        return self.get_revocation(capability_id) is not None
    
    def list_by_subject(self, subject: str) -> list[Capability]:
        """List all capabilities for a subject."""
        cap_ids = self._get_index(self.db_by_subject, subject)
        return [self.get(cid) for cid in cap_ids if self.get(cid) is not None]
    
    def list_by_scope(self, scope: str) -> list[Capability]:
        """List all capabilities for a scope."""
        cap_ids = self._get_index(self.db_by_scope, scope)
        return [self.get(cid) for cid in cap_ids if self.get(cid) is not None]
    
    def list_all(self) -> Iterator[Capability]:
        """Iterate over all capabilities."""
        with self.env.begin() as txn:
            cursor = txn.cursor(db=self.db_capabilities)
            for key, value in cursor:
                data = json.loads(value.decode())
                yield Capability.from_dict(data)
    
    def list_revocations(self) -> Iterator[RevocationEntry]:
        """Iterate over all revocations."""
        with self.env.begin() as txn:
            cursor = txn.cursor(db=self.db_revocations)
            for key, value in cursor:
                data = json.loads(value.decode())
                yield RevocationEntry(
                    capability_id=data["capability_id"],
                    revoked_at=datetime.fromisoformat(data["revoked_at"]),
                    reason=data["reason"],
                    revoked_by=data["revoked_by"],
                )
    
    def _add_to_index(self, txn, db, key: str, cap_id: str) -> None:
        """Add capability ID to an index."""
        existing = txn.get(key.encode(), db=db)
        if existing:
            ids = json.loads(existing.decode())
        else:
            ids = []
        
        if cap_id not in ids:
            ids.append(cap_id)
            txn.put(key.encode(), json.dumps(ids).encode(), db=db)
    
    def _remove_from_index(self, txn, db, key: str, cap_id: str) -> None:
        """Remove capability ID from an index."""
        existing = txn.get(key.encode(), db=db)
        if existing:
            ids = json.loads(existing.decode())
            if cap_id in ids:
                ids.remove(cap_id)
                if ids:
                    txn.put(key.encode(), json.dumps(ids).encode(), db=db)
                else:
                    txn.delete(key.encode(), db=db)
    
    def _get_index(self, db, key: str) -> list[str]:
        """Get capability IDs from an index."""
        with self.env.begin() as txn:
            value = txn.get(key.encode(), db=db)
            if value is None:
                return []
            return json.loads(value.decode())
    
    def close(self) -> None:
        """Close the database."""
        self.env.close()
        logger.info(f"Closed CapabilityStore at {self.path}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
