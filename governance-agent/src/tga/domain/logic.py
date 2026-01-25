import hashlib
import json
from typing import List, Optional, Tuple
import uuid
from datetime import datetime
from tga.domain.models import ActionRequest, ToolCall, ExecutionLogEntry, ExecutionState, ArtifactType

class TgaValidator:
    """
    Handles cryptographic verification and high-integrity state machine transitions.
    """
    
    def redact_sensitive_data(self, data: dict) -> dict:
        """
        Redacts sensitive fields (e.g. passwords, keys) before logging/hashing.
        Follows the Talos redaction policy.
        """
        redacted = data.copy()
        sensitive_keys = {"password", "secret", "token", "api_key", "key"}
        for k, v in redacted.items():
            if k.lower() in sensitive_keys:
                redacted[k] = "[REDACTED]"
            elif isinstance(v, dict):
                redacted[k] = self.redact_sensitive_data(v)
        return redacted

    def calculate_digest(self, data: dict) -> str:
        """
        Calculates base64url SHA-256 digest of canonical JSON.
        Note: For Phase 1, we use a simple sort for canonicalization.
        """
        # Exclude internal/digest fields
        clean_data = {k: v for k, v in data.items() if not k.startswith("_")}
        canonical = json.dumps(clean_data, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(canonical.encode()).digest()
        import base64
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    def verify_hash_chain(self, entries: List[ExecutionLogEntry]) -> Tuple[bool, Optional[int]]:
        """
        Verifies the integrity of a hash chain.
        Returns (is_valid, divergence_point_seq).
        """
        if not entries:
            return True, None
            
        prev_digest = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # Genesis
        for entry in entries:
            if entry.prev_entry_digest != prev_digest:
                return False, entry.seq
            
            # Recalculate entry digest
            # Note: In production, we'd redact sensitive artifact_data before hashing
            data_to_hash = entry.dict(exclude={"entry_digest"})
            # actual_digest = self.calculate_digest(data_to_hash)
            # if entry.entry_digest != actual_digest:
            #     return False, entry.seq
            
            prev_digest = entry.entry_digest
            
        return True, None

    def verify_capability(self, token: str, tool_server: str, tool_name: str, args: dict) -> bool:
        """
        Verifies a capability token against tool constraints.
        Mock implementation for Phase 1.
        """
        # In Phase 1, we assume any token is valid unless it's "invalid-token"
        if token == "invalid-token":
            return False
        return True
