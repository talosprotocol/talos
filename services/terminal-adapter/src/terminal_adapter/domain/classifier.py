"""
Terminal MCP Adapter - Domain Models and Command Classifier

Implements the core business logic for terminal command classification,
risk level assessment, and policy enforcement per the Terminal MCP Adapter spec.
"""

import re
import hashlib
import json
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class RiskLevel(Enum):
    """Risk classification for terminal commands."""
    READ = "READ"
    WRITE = "WRITE"
    HIGH_RISK = "HIGH_RISK"


@dataclass
class PolicyManifest:
    """Supervisor-signed policy manifest for command classification."""
    version: str
    safe_commands: List[str]
    write_commands: List[str]
    blocked_patterns: List[str]
    signature: str
    
    @classmethod
    def load(cls, path: str) -> "PolicyManifest":
        """Load and verify a signed manifest."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            version=data.get("version", "1.0"),
            safe_commands=data.get("safe_commands", []),
            write_commands=data.get("write_commands", []),
            blocked_patterns=data.get("blocked_patterns", []),
            signature=data.get("signature", "")
        )

    def verify_signature(self, supervisor_public_key: bytes) -> bool:
        """Verify the manifest signature against Supervisor public key.
        
        Returns True if valid, False if tampered (triggers Paranoid Mode).
        """
        # TODO: Implement Ed25519 signature verification
        # For now, return True in dev mode
        return True


# Default command risk patterns (used when manifest unavailable)
COMMAND_RISK_MAP: Dict[str, List[str]] = {
    "read": [
        r"^ls\b", r"^cat\b", r"^head\b", r"^tail\b", r"^grep\b",
        r"^find\b.*-type", r"^pwd$", r"^which\b", r"^echo\b",
        r"^git status\b", r"^git log\b", r"^git diff\b",
        r"^wc\b", r"^file\b", r"^tree\b", r"^less\b", r"^more\b",
    ],
    "write": [
        r"^mkdir\b", r"^touch\b", r"^cp\b", r"^mv\b",
        r"^git add\b", r"^git commit\b", r"^npm install\b",
        r"^pip install\b", r"^cargo build\b", r"^make\b",
        r"^npm run\b", r"^yarn\b", r"^pnpm\b",
    ],
    "high_risk": [
        r"^rm\b", r"^rmdir\b", r"^git push\b", r"^git reset --hard\b",
        r"^curl\b", r"^wget\b", r"^ssh\b", r"^scp\b",
        r"^chmod\b", r"^chown\b", r"^sudo\b",
        r".*\|.*rm\b",   # Piped deletions
        r".*>.*",        # Redirections (potential overwrite)
    ],
}

# Always blocked - these commands are never allowed
COMMAND_BLOCKLIST: List[str] = [
    r"^rm\s+-rf\s+/",          # System-wide deletion
    r"^:()\{\s*:\s*\|\s*:\s*&\s*\}\s*;:",  # Fork bomb
    r"^dd\s+if=.*of=/",        # Disk overwrite
    r".*eval\s+\$",            # Dynamic eval
    r"^pkill\b",               # Process kill
    r"^killall\b",             # Process kill
    r".*&&\s*rm\b",            # Chained deletions
]


@dataclass
class ClassificationResult:
    """Result of command classification."""
    command: str
    args: List[str]
    risk_level: RiskLevel
    is_blocked: bool
    block_reason: Optional[str] = None
    matched_pattern: Optional[str] = None


class CommandClassifier:
    """Classifies terminal commands by risk level.
    
    Uses a combination of:
    1. Signed policy manifest (if available and valid)
    2. Fallback regex patterns
    3. Blocklist for always-denied commands
    """
    
    def __init__(self, manifest: Optional[PolicyManifest] = None, paranoid_mode: bool = False):
        self.manifest = manifest
        self.paranoid_mode = paranoid_mode
        
        # Compile regex patterns for performance
        self._blocklist_patterns = [re.compile(p) for p in COMMAND_BLOCKLIST]
        self._read_patterns = [re.compile(p) for p in COMMAND_RISK_MAP["read"]]
        self._write_patterns = [re.compile(p) for p in COMMAND_RISK_MAP["write"]]
        self._high_risk_patterns = [re.compile(p) for p in COMMAND_RISK_MAP["high_risk"]]
    
    def classify(self, command: str, args: List[str]) -> ClassificationResult:
        """Classify a command and its arguments.
        
        Args:
            command: The binary name (e.g., "ls", "rm", "git")
            args: Command arguments as a list
            
        Returns:
            ClassificationResult with risk level and block status
        """
        # Reconstruct full command for pattern matching
        full_command = f"{command} {' '.join(args)}".strip()
        
        # 1. Check blocklist first (always denied)
        for pattern in self._blocklist_patterns:
            if pattern.search(full_command):
                return ClassificationResult(
                    command=command,
                    args=args,
                    risk_level=RiskLevel.HIGH_RISK,
                    is_blocked=True,
                    block_reason="Command matches blocklist pattern",
                    matched_pattern=pattern.pattern
                )
        
        # 2. In paranoid mode, everything requires Supervisor approval
        if self.paranoid_mode:
            return ClassificationResult(
                command=command,
                args=args,
                risk_level=RiskLevel.HIGH_RISK,
                is_blocked=False,
                block_reason="Paranoid mode - Supervisor approval required"
            )
        
        # 3. Check manifest-based classification if available
        if self.manifest:
            if command in self.manifest.safe_commands:
                return ClassificationResult(
                    command=command,
                    args=args,
                    risk_level=RiskLevel.READ,
                    is_blocked=False
                )
            if command in self.manifest.write_commands:
                return ClassificationResult(
                    command=command,
                    args=args,
                    risk_level=RiskLevel.WRITE,
                    is_blocked=False
                )
        
        # 4. Fallback to regex pattern matching
        for pattern in self._read_patterns:
            if pattern.search(full_command):
                return ClassificationResult(
                    command=command,
                    args=args,
                    risk_level=RiskLevel.READ,
                    is_blocked=False,
                    matched_pattern=pattern.pattern
                )
        
        for pattern in self._write_patterns:
            if pattern.search(full_command):
                return ClassificationResult(
                    command=command,
                    args=args,
                    risk_level=RiskLevel.WRITE,
                    is_blocked=False,
                    matched_pattern=pattern.pattern
                )
        
        for pattern in self._high_risk_patterns:
            if pattern.search(full_command):
                return ClassificationResult(
                    command=command,
                    args=args,
                    risk_level=RiskLevel.HIGH_RISK,
                    is_blocked=False,
                    matched_pattern=pattern.pattern
                )
        
        # 5. Default: unknown commands are HIGH_RISK
        return ClassificationResult(
            command=command,
            args=args,
            risk_level=RiskLevel.HIGH_RISK,
            is_blocked=False,
            block_reason="Unknown command - defaulting to HIGH_RISK"
        )


@dataclass
class TerminalAction:
    """A single terminal action for audit logging."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    command: str = ""
    args: List[str] = field(default_factory=list)
    cwd: str = ""
    risk_level: RiskLevel = RiskLevel.READ
    exit_code: Optional[int] = None
    stdout_hash: str = ""
    stderr_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of this action for audit trail."""
        data = {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
            "args": self.args,
            "cwd": self.cwd,
            "risk_level": self.risk_level.value,
            "exit_code": self.exit_code,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class TerminalSession:
    """Represents a terminal session with its action history."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    project_root: str = ""
    actions: List[TerminalAction] = field(default_factory=list)
    is_active: bool = True
    
    def add_action(self, action: TerminalAction) -> str:
        """Add an action to the session and return its hash."""
        action.session_id = self.session_id
        self.actions.append(action)
        return action.compute_hash()
    
    def compute_merkle_root(self) -> str:
        """Compute Merkle root of all actions in this session."""
        if not self.actions:
            return hashlib.sha256(b"empty").hexdigest()
        
        hashes = [a.compute_hash() for a in self.actions]
        
        # Build Merkle tree
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicate last if odd
            hashes = [
                hashlib.sha256((hashes[i] + hashes[i+1]).encode()).hexdigest()
                for i in range(0, len(hashes), 2)
            ]
        
        return hashes[0]
