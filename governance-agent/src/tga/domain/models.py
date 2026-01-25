from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict
import uuid6

class RiskLevel(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    HIGH_RISK = "HIGH_RISK"

class ExecutionState(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ArtifactType(str, Enum):
    ACTION_REQUEST = "action_request"
    SUPERVISOR_DECISION = "supervisor_decision"
    TOOL_CALL = "tool_call"
    TOOL_EFFECT = "tool_effect"

class ActionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    schema_id: str = "talos.tga.action_request"
    schema_version: str = "tga.v1"
    trace_id: uuid.UUID
    plan_id: uuid.UUID
    action_request_id: uuid.UUID
    agent_id: uuid.UUID
    ts: datetime
    risk_level: RiskLevel
    intent: str
    resources: List[Dict[str, str]]
    proposal: Dict[str, Any]
    idempotency_key: Optional[uuid.UUID] = None
    meta: Optional[Dict[str, Any]] = None
    digest_alg: str = Field(default="sha256", serialization_alias="_digest_alg", validation_alias="_digest_alg")
    digest: str = Field(..., serialization_alias="_digest", validation_alias="_digest")

class SupervisorDecision(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    schema_id: str = "talos.tga.supervisor_decision"
    schema_version: str = "tga.v1"
    trace_id: uuid.UUID
    plan_id: uuid.UUID
    supervisor_decision_id: uuid.UUID
    action_request_id: uuid.UUID
    action_request_digest: str
    ts: datetime
    decision: str
    rationale: Optional[str] = None
    minted_capability: Optional[str] = None
    digest_alg: str = Field(default="sha256", serialization_alias="_digest_alg", validation_alias="_digest_alg")
    digest: str = Field(..., serialization_alias="_digest", validation_alias="_digest")

class ToolCall(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    schema_id: str = "talos.tga.tool_call"
    schema_version: str = "tga.v1"
    trace_id: uuid.UUID
    plan_id: uuid.UUID
    tool_call_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    supervisor_decision_id: Optional[uuid.UUID] = None
    supervisor_decision_digest: Optional[str] = None
    capability_digest: Optional[str] = None
    args_digest: str
    ts: datetime
    call: Dict[str, Any]
    tool_class: str = "write"
    idempotency_key: uuid.UUID
    digest_alg: str = Field(default="sha256", serialization_alias="_digest_alg", validation_alias="_digest_alg")
    digest: str = Field(..., serialization_alias="_digest", validation_alias="_digest")

class ExecutionLogEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    schema_id: str = "talos.tga.execution_log_entry"
    schema_version: str = "v1"
    trace_id: uuid.UUID
    principal_id: uuid.UUID
    seq: int
    ts: datetime
    prev_entry_digest: str
    entry_digest: str
    from_state: ExecutionState
    to_state: ExecutionState
    artifact_type: ArtifactType
    artifact_id: uuid.UUID
    artifact_digest: str
    artifact_data: Optional[Dict[str, Any]] = None
    tool_call_id: Optional[uuid.UUID] = None
    idempotency_key: Optional[uuid.UUID] = None
