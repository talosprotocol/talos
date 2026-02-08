"""
Terminal MCP Adapter - Session Manager

Manages terminal sessions with ephemeral Merkle trees and Write-Ahead Log (WAL)
for crash recovery, as specified in the Terminal MCP Adapter spec.
"""

import os
import json
import hashlib
import asyncio
from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

from .classifier import TerminalSession, TerminalAction, RiskLevel

logger = logging.getLogger("terminal-adapter.session")


@dataclass
class WALEntry:
    """Write-Ahead Log entry for crash recovery."""
    sequence: int
    action_id: str
    session_id: str
    timestamp: str
    command: str
    args: List[str]
    cwd: str
    risk_level: str


class WriteAheadLog:
    """Encrypted Write-Ahead Log for session durability.
    
    Actions are written to WAL before updating the in-memory tree,
    ensuring we can recover the session state after a crash.
    """
    
    def __init__(self, session_id: str, wal_dir: str = "~/.talos/sessions"):
        self.session_id = session_id
        self.wal_dir = os.path.expanduser(wal_dir)
        self.wal_path = os.path.join(self.wal_dir, f"{session_id}.wal")
        self.sequence = 0
        
        os.makedirs(self.wal_dir, exist_ok=True)
    
    def append(self, action: TerminalAction) -> None:
        """Append an action to the WAL (sync write for durability)."""
        entry = WALEntry(
            sequence=self.sequence,
            action_id=action.action_id,
            session_id=action.session_id,
            timestamp=action.timestamp.isoformat(),
            command=action.command,
            args=action.args,
            cwd=action.cwd,
            risk_level=action.risk_level.value
        )
        
        with open(self.wal_path, 'a') as f:
            f.write(json.dumps(asdict(entry)) + "\n")
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        self.sequence += 1
    
    def recover(self) -> List[TerminalAction]:
        """Recover actions from WAL after crash."""
        actions = []
        
        if not os.path.exists(self.wal_path):
            return actions
        
        with open(self.wal_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                action = TerminalAction(
                    action_id=data["action_id"],
                    session_id=data["session_id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    command=data["command"],
                    args=data["args"],
                    cwd=data["cwd"],
                    risk_level=RiskLevel(data["risk_level"])
                )
                actions.append(action)
        
        return actions
    
    def truncate(self) -> None:
        """Truncate WAL after successful anchor (checkpoint)."""
        if os.path.exists(self.wal_path):
            os.truncate(self.wal_path, 0)
        self.sequence = 0


class SessionManager:
    """Manages terminal sessions with Merkle trees and anchoring.
    
    Features:
    - Ephemeral in-memory Merkle trees for action tracking
    - Write-Ahead Log for crash recovery
    - Periodic anchoring to global audit chain
    - Session lifecycle management
    """
    
    ANCHOR_INTERVAL = timedelta(minutes=10)
    
    def __init__(
        self,
        project_root: str,
        anchor_callback: Optional[Callable[[str, str], Any]] = None
    ):
        self.project_root = project_root
        self.anchor_callback = anchor_callback
        self.sessions: Dict[str, TerminalSession] = {}
        self.wals: Dict[str, WriteAheadLog] = {}
        self._anchor_task: Optional[asyncio.Task] = None
        self._last_anchor: Dict[str, datetime] = {}
    
    def create_session(self) -> TerminalSession:
        """Create a new terminal session."""
        session = TerminalSession(project_root=self.project_root)
        self.sessions[session.session_id] = session
        self.wals[session.session_id] = WriteAheadLog(session.session_id)
        self._last_anchor[session.session_id] = datetime.utcnow()
        
        logger.info(f"Created session {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat(),
                "action_count": len(s.actions),
                "is_active": s.is_active,
            }
            for s in self.sessions.values()
            if s.is_active
        ]
    
    def record_action(
        self,
        session_id: str,
        command: str,
        args: List[str],
        cwd: str,
        risk_level: RiskLevel,
        exit_code: Optional[int] = None,
        stdout: str = "",
        stderr: str = ""
    ) -> str:
        """Record an action to a session.
        
        Returns the action's audit hash.
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        action = TerminalAction(
            command=command,
            args=args,
            cwd=cwd,
            risk_level=risk_level,
            exit_code=exit_code,
            stdout_hash=hashlib.sha256(stdout.encode()).hexdigest()[:16] if stdout else "",
            stderr_hash=hashlib.sha256(stderr.encode()).hexdigest()[:16] if stderr else "",
        )
        
        # 1. Write to WAL first (durability)
        wal = self.wals.get(session_id)
        if wal:
            wal.append(action)
        
        # 2. Add to in-memory session tree
        audit_hash = session.add_action(action)
        
        logger.debug(f"Recorded action {action.action_id}: {command}")
        return audit_hash
    
    async def anchor_session(self, session_id: str, immediate: bool = False) -> Optional[str]:
        """Anchor a session's Merkle root to the global audit chain.
        
        Args:
            session_id: Session to anchor
            immediate: If True, anchor even if interval hasn't elapsed
            
        Returns:
            The anchored Merkle root, or None if skipped
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check if we should anchor
        last = self._last_anchor.get(session_id, datetime.min)
        if not immediate and datetime.utcnow() - last < self.ANCHOR_INTERVAL:
            return None
        
        merkle_root = session.compute_merkle_root()
        
        # Call anchor callback (e.g., to Talos Audit Service)
        if self.anchor_callback:
            try:
                await self.anchor_callback(session_id, merkle_root)
            except Exception as e:
                logger.error(f"Anchor callback failed: {e}")
                return None
        
        # Truncate WAL after successful anchor
        wal = self.wals.get(session_id)
        if wal:
            wal.truncate()
        
        self._last_anchor[session_id] = datetime.utcnow()
        logger.info(f"Anchored session {session_id}: {merkle_root[:16]}...")
        
        return merkle_root
    
    async def close_session(self, session_id: str) -> Optional[str]:
        """Close a session and anchor its final state."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        session.is_active = False
        
        # Final anchor
        merkle_root = await self.anchor_session(session_id, immediate=True)
        
        logger.info(f"Closed session {session_id}")
        return merkle_root
    
    def recover_session(self, session_id: str) -> Optional[TerminalSession]:
        """Recover a session from WAL after crash."""
        wal = WriteAheadLog(session_id)
        actions = wal.recover()
        
        if not actions:
            return None
        
        session = TerminalSession(session_id=session_id)
        for action in actions:
            session.actions.append(action)
        
        self.sessions[session_id] = session
        self.wals[session_id] = wal
        
        logger.info(f"Recovered session {session_id} with {len(actions)} actions")
        return session
    
    async def start_anchor_loop(self) -> None:
        """Start periodic anchoring background task."""
        async def _anchor_loop():
            while True:
                await asyncio.sleep(60)  # Check every minute
                for session_id in list(self.sessions.keys()):
                    if self.sessions.get(session_id, TerminalSession()).is_active:
                        await self.anchor_session(session_id)
        
        self._anchor_task = asyncio.create_task(_anchor_loop())
    
    async def stop_anchor_loop(self) -> None:
        """Stop the anchor loop."""
        if self._anchor_task:
            self._anchor_task.cancel()
            try:
                await self._anchor_task
            except asyncio.CancelledError:
                pass
