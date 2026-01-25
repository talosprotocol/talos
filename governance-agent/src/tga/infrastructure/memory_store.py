from typing import Dict, List, Optional
import uuid
from ..domain.models import ActionRequest, ExecutionLogEntry, ExecutionState

class InMemStore:
    """
    In-memory storage for TGA state and logs.
    Used for Phase 1 baseline.
    """
    def __init__(self):
        self.action_requests: Dict[uuid.UUID, ActionRequest] = {}
        self.execution_logs: Dict[uuid.UUID, List[ExecutionLogEntry]] = {}
        self.sessions: Dict[uuid.UUID, dict] = {}  # session_id -> {principal_id, last_ts}
        self.idempotency_keys: Dict[uuid.UUID, str] = {}  # key -> result_digest

    def save_action_request(self, req: ActionRequest):
        self.action_requests[req.action_request_id] = req

    def get_action_request(self, action_request_id: uuid.UUID) -> Optional[ActionRequest]:
        return self.action_requests.get(action_request_id)

    def append_log_entry(self, trace_id: uuid.UUID, entry: ExecutionLogEntry):
        if trace_id not in self.execution_logs:
            self.execution_logs[trace_id] = []
        self.execution_logs[trace_id].append(entry)

    def get_execution_log(self, trace_id: uuid.UUID) -> List[ExecutionLogEntry]:
        return self.execution_logs.get(trace_id, [])

    def get_latest_log_entry(self, trace_id: uuid.UUID) -> Optional[ExecutionLogEntry]:
        log = self.get_execution_log(trace_id)
        return log[-1] if log else None

    def save_session(self, session_id: uuid.UUID, principal_id: uuid.UUID):
        self.sessions[session_id] = {"principal_id": principal_id}

    def get_session(self, session_id: uuid.UUID) -> Optional[dict]:
        return self.sessions.get(session_id)

    def check_idempotency(self, key: uuid.UUID) -> Optional[str]:
        return self.idempotency_keys.get(key)

    def record_idempotency(self, key: uuid.UUID, result_digest: str):
        self.idempotency_keys[key] = result_digest
