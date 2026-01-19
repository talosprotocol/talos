"""A2A Pydantic models aligned with Phase 10.0 contracts."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_HEX64 = re.compile(r"^[a-f0-9]{64}$")
_B64U_NOPAD = re.compile(r"^[A-Za-z0-9_-]+$")  # no '=' allowed, non-empty


class ContractModel(BaseModel):
    """Base model with contract validation rules."""

    model_config = {"extra": "forbid"}

    @field_validator("*", mode="before")
    @classmethod
    def validate_hashes_and_digests(cls, v, info):
        """Validate digest and hash fields are lowercase hex sha256."""
        name = (info.field_name or "").lower()
        if isinstance(v, str) and ("digest" in name or "hash" in name):
            if not _HEX64.fullmatch(v):
                raise ValueError(f"{info.field_name} must be lowercase hex sha256 (64 chars)")
        return v


class EncryptedFrame(ContractModel):
    """E2E encrypted frame per talos.a2a.encrypted_frame schema."""

    schema_id: Literal["talos.a2a.encrypted_frame"] = "talos.a2a.encrypted_frame"
    schema_version: Literal["v1"] = "v1"
    session_id: str
    sender_id: str
    sender_seq: int = Field(ge=0)
    header_b64u: str
    ciphertext_b64u: str
    frame_digest: str
    ciphertext_hash: str
    created_at: datetime | None = None  # Server assigns if not provided

    @field_validator("header_b64u", "ciphertext_b64u", mode="before")
    @classmethod
    def validate_b64url_no_pad(cls, v):
        """Validate base64url encoding without padding."""
        if not isinstance(v, str) or not _B64U_NOPAD.fullmatch(v):
            raise ValueError("Must be non-empty base64url without padding")
        return v


class SessionResponse(ContractModel):
    """Session state response from gateway."""

    session_id: str
    state: str
    initiator_id: str
    responder_id: str
    expires_at: datetime | None = None


class FrameSendResponse(ContractModel):
    """Response after successful frame send."""

    session_id: str
    sender_seq: int
    frame_digest: str


class FrameListResponse(ContractModel):
    """Paginated list of frames."""

    items: list[EncryptedFrame]
    next_cursor: str | None = None


class GroupResponse(ContractModel):
    """Group state response from gateway."""

    group_id: str
    owner_id: str
    state: str


class ErrorResponse(BaseModel):
    """Gateway error response."""

    error_code: str
    message: str
    details: dict | None = None
