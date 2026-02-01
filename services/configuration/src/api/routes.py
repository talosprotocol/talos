"""Configuration Service API Routes."""

# Final Quality Sweep

import importlib.metadata
import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any, cast

import yaml  # type: ignore
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Rate Limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..core.config import SETTINGS  # type: ignore
from ..core.redaction import redact_config  # type: ignore
from ..core.storage import (  # type: ignore
    ConfigDraft,
    ConfigHistory,
    Database,
    IdempotencyRecord,
)
from ..core.utils import (  # type: ignore
    check_idempotency_conflict,
    compute_body_digest,
    decode_cursor,
    encode_cursor,
)
from ..core.validation import validate_and_normalize  # type: ignore

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# --- Pydantic Models ---


class HealthResponse(BaseModel):  # type: ignore
    """Health check response model."""

    status: str
    contracts_version: str
    active_config_digest: str | None
    current_config: dict[str, Any] | None
    version: str


class ContractsVersionResponse(BaseModel):  # type: ignore
    """Contracts version response model."""

    contracts_version: str
    config_version_supported: list[str]


class ValidateRequest(BaseModel):  # type: ignore
    """Validation request model."""

    config: dict[str, Any]
    strict: bool = True


class ValidateResponse(BaseModel):  # type: ignore
    """Validation response model."""

    valid: bool
    errors: list[Any]
    normalized_config: dict[str, Any] | None = None


class NormalizeRequest(BaseModel):  # type: ignore
    """Normalization request model."""

    config: dict[str, Any]


class NormalizeResponse(BaseModel):  # type: ignore
    """Normalization response model."""

    normalized_config: dict[str, Any]
    config_digest: str


class DraftCreateRequest(BaseModel):  # type: ignore
    """Draft creation request model."""

    config: dict[str, Any]
    note: str | None = None


class DraftCreateResponse(BaseModel):  # type: ignore
    """Draft creation response model."""

    draft_id: str
    config_digest: str
    created_at: str


class PublishRequest(BaseModel):  # type: ignore
    """Publish request model."""

    draft_id: str


class PublishResponse(BaseModel):  # type: ignore
    """Publish response model."""

    active_config_id: str
    active_config_digest: str


class HistoryItemResponse(BaseModel):  # type: ignore
    """History item response model."""

    id: str
    config_digest: str
    created_at: str
    redacted_config: dict[str, Any]


class HistoryResponse(BaseModel):  # type: ignore
    """History response model."""

    items: list[HistoryItemResponse]
    next_cursor: str | None
    has_more: bool


class ExportRequest(BaseModel):  # type: ignore
    """Export request model."""

    format: str = "yaml"
    source: str = "active"
    redacted: bool = True


class ExportResponse(BaseModel):  # type: ignore
    """Export response model."""

    content: str
    filename: str
    content_type: str


# --- Routes ---


@router.get("/health", response_model=HealthResponse)
@router.get("/ui-bootstrap", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Retrieve service health status."""
    active = DB.get_current_config()
    return HealthResponse(
        status="ok",
        contracts_version=SETTINGS.CONTRACTS_VERSION,
        active_config_digest=active.config_digest if active else None,
        current_config=json.loads(active.config_json) if active else None,
        version=SETTINGS.VERSION,
    )


@router.get("/contracts-version", response_model=ContractsVersionResponse)
async def contracts_version() -> ContractsVersionResponse:
    """Retrieve the installed versions of Talos contracts.

    Supported config versions are also included.

    Returns:
        ContractsVersionResponse: Version information.
    """
    try:
        installed_version = importlib.metadata.version("talos-contracts")
    except importlib.metadata.PackageNotFoundError:
        installed_version = "unknown"

    return ContractsVersionResponse(
        contracts_version=installed_version, config_version_supported=["1.0"]
    )


@router.get("/schema", response_model=dict[str, Any])  # type: ignore
async def get_schema() -> dict[str, Any] | JSONResponse:
    """Retrieve the Talos configuration JSON schema.

    Returns:
        Union[dict[str, Any], JSONResponse]: The JSON schema or an error.
    """
    try:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "talos-contracts",
            "schemas",
            "config",
            "v1",
            "talos.config.schema.json",
        )
        if not os.path.exists(schema_path):
            # Fallback for alternative layouts
            schema_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "contracts",
                "schemas",
                "config",
                "v1",
                "talos.config.schema.json",
            )

        with open(schema_path, encoding="utf-8") as f:
            return cast(dict[str, Any], json.load(f))
    except FileNotFoundError:
        return JSONResponse(
            status_code=500, content={"error": "Schema not found"}
        )


@router.post("/validate", response_model=ValidateResponse)  # type: ignore
@limiter.limit("10/minute")  # type: ignore
async def validate(
    request: Request, body: ValidateRequest
) -> ValidateResponse | JSONResponse:
    """Validate a configuration against the Talos schema.

    Args:
        request: The incoming FastAPI request.
        body: The validation request containing the config to check.

    Returns:
        Union[ValidateResponse, JSONResponse]: Validation results or an error
            response.
    """
    # Check Body Size (Content-Length header) is still handled by starlette
    # for security, but we can rely on FastAPI/Pydantic for structure.
    raw_body = await request.body()
    if len(raw_body) > SETTINGS.MAX_BODY_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Payload exceeds 256KB",
                }
            },
        )

    result = validate_and_normalize(body.config, strict=body.strict)

    if not result.valid:
        return JSONResponse(
            status_code=400, content={"valid": False, "errors": result.errors}
        )

    if result.normalized_config is None:
        raise RuntimeError("Normalized config is None after validation")
    return ValidateResponse(
        valid=True,
        errors=[],
        normalized_config=redact_config(result.normalized_config),
    )


@router.post("/normalize", response_model=NormalizeResponse)
@limiter.limit("50/minute")
async def normalize(
    request: Request, body: NormalizeRequest
) -> NormalizeResponse | JSONResponse:
    """Normalize a configuration and compute its canonical digest.

    Args:
        request: The incoming FastAPI request.
        body: The normalization request containing the config.

    Returns:
        NormalizeResponse | JSONResponse: Normalization results or an error.
    """
    raw_body = await request.body()
    if len(raw_body) > SETTINGS.MAX_BODY_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Payload exceeds 256KB",
                }
            },
        )

    result = validate_and_normalize(body.config, strict=True)

    if not result.valid:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "SCHEMA_VALIDATION_FAILED",
                    "message": "Invalid config",
                    "details": result.errors,
                }
            },
        )

    if result.normalized_config is None:
        raise RuntimeError("Normalization failed")
    if result.digest is None:
        raise RuntimeError("Digest computation failed")
    return NormalizeResponse(
        normalized_config=redact_config(result.normalized_config),
        config_digest=result.digest,
    )


# Global DB instance (Singleton for this worker)
DB = Database()


@router.post("/drafts", response_model=DraftCreateResponse)  # type: ignore
async def create_draft(
    request: Request, body: DraftCreateRequest
) -> DraftCreateResponse | JSONResponse | Response:
    """Create a new configuration draft.

    This endpoint is idempotent and requires a valid principal ID.

    Args:
        request: The incoming FastAPI request.
        body: The draft creation request.

    Returns:
        Union[DraftCreateResponse, JSONResponse, Response]: The created draft,
            an error response, or a replayed response for idempotent requests.
    """
    # Idempotency Check
    key = request.headers.get("Idempotency-Key") or request.headers.get(
        "X-Idempotency-Key"
    )
    if not key:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Missing Idempotency-Key",
                }
            },
        )

    principal = request.headers.get(
        "X-Talos-Principal-Id", "dev" if SETTINGS.DEV_MODE else None
    )
    if not principal:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Missing Principal ID",
                }
            },
        )

    body_bytes = await request.body()
    body_digest = compute_body_digest(body_bytes)

    # Check Replay
    record = DB.get_idempotency_record(
        key, principal, "POST", "/api/config/drafts"
    )

    if record:
        if check_idempotency_conflict(record, body_digest):
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "IDEMPOTENCY_KEY_REUSE_CONFLICT",
                        "message": "Conflict",
                    }
                },
            )
        else:
            # Replay
            return Response(
                content=record.response_body,
                status_code=record.response_code,
                media_type="application/json",
            )

    result = validate_and_normalize(body.config, strict=True)
    if not result.valid:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "SCHEMA_VALIDATION_FAILED",
                    "message": "Invalid config",
                    "details": result.errors,
                }
            },
        )

    draft_id = str(uuid.uuid4())
    created_at = datetime.now(UTC)

    if result.digest is None:
        raise RuntimeError("Config digest is None during draft creation")
    draft = ConfigDraft(
        draft_id=draft_id,
        principal=principal,
        config_digest=result.digest,
        config_json=json.dumps(result.normalized_config),
        note=body.note,
        created_at=created_at,
    )

    DB.save_draft(draft)

    response = DraftCreateResponse(
        draft_id=draft_id,
        config_digest=result.digest,
        created_at=created_at.isoformat(),
    )
    response_body = response.model_dump_json()

    # Save Idempotency
    DB.save_idempotency_record(
        IdempotencyRecord(
            key=key,
            principal=principal,
            method="POST",
            path="/api/config/drafts",
            request_digest=body_digest,
            response_code=200,
            response_body=response_body,
            created_at=created_at,
        )
    )

    return response


@router.post("/publish", response_model=PublishResponse)  # type: ignore
async def publish_draft(
    request: Request, body: PublishRequest
) -> PublishResponse | JSONResponse | Response:
    """Publish a configuration draft as the new active configuration.

    This endpoint is idempotent.

    Args:
        request: The incoming FastAPI request.
        body: The publish request containing the draft ID.

    Returns:
        Union[PublishResponse, JSONResponse, Response]: Publish result or
            error.
    """
    key = request.headers.get("Idempotency-Key") or request.headers.get(
        "X-Idempotency-Key"
    )
    if not key:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Missing Idempotency-Key",
                }
            },
        )

    principal = request.headers.get(
        "X-Talos-Principal-Id", "dev" if SETTINGS.DEV_MODE else None
    )
    if not principal:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Missing Principal ID",
                }
            },
        )

    body_bytes = await request.body()
    body_digest = compute_body_digest(body_bytes)

    record = DB.get_idempotency_record(
        key, principal, "POST", "/api/config/publish"
    )

    if record:
        if check_idempotency_conflict(record, body_digest):
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "IDEMPOTENCY_KEY_REUSE_CONFLICT",
                        "message": "Conflict",
                    }
                },
            )
        else:
            return Response(
                content=record.response_body,
                status_code=record.response_code,
                media_type="application/json",
            )

    draft = DB.get_draft(body.draft_id)
    if not draft:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Draft not found",
                }
            },
        )

    # Promote to History
    config_id = str(uuid.uuid4())
    created_at = datetime.now(UTC)

    history = ConfigHistory(
        id=config_id,
        draft_id=draft.draft_id,
        config_digest=draft.config_digest,
        config_json=draft.config_json,
        principal=principal,
        created_at=created_at,
    )

    DB.publish_draft(history)

    response = PublishResponse(
        active_config_id=config_id, active_config_digest=draft.config_digest
    )
    response_body = response.model_dump_json()

    DB.save_idempotency_record(
        IdempotencyRecord(
            key=key,
            principal=principal,
            method="POST",
            path="/api/config/publish",
            request_digest=body_digest,
            response_code=200,
            response_body=response_body,
            created_at=created_at,
        )
    )

    return response


@router.get("/history", response_model=HistoryResponse)  # type: ignore
async def list_history(
    limit: int = 50, cursor: str | None = None
) -> HistoryResponse | JSONResponse:
    """List historical configurations with cursor-based pagination.

    Args:
        limit: Number of items to return (max 200).
        cursor: Opaque cursor for pagination.

    Returns:
        Union[HistoryResponse, JSONResponse]: The history list or an error.
    """
    if limit > 200:
        limit = 200
    if limit < 1:
        limit = 50

    before_created_at = None
    before_id = None

    if cursor:
        try:
            before_created_at, before_id = decode_cursor(cursor)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Invalid cursor",
                    }
                },
            )

    items = DB.list_history(limit, before_created_at, before_id)

    next_cursor = None
    if items:
        last = items[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    records = []
    for item in items:
        # Redact config before returning
        config = json.loads(item.config_json)
        redacted = redact_config(config)
        records.append(
            HistoryItemResponse(
                id=item.id,
                config_digest=item.config_digest,
                created_at=item.created_at.isoformat(),
                redacted_config=redacted,
            )
        )

    return HistoryResponse(
        items=records, next_cursor=next_cursor, has_more=len(items) == limit
    )


@router.post("/export", response_model=ExportResponse)  # noqa: E501
async def export_config(
    _request: Request, body: ExportRequest
) -> ExportResponse | JSONResponse:
    """Export a specific configuration.

    Args:
        request: The incoming FastAPI request.
        body: The export request.

    Returns:
        Union[ExportResponse, JSONResponse]: The exported config or an error.
    """
    config_data = None
    digest = None

    if body.source == "active":
        active = DB.get_current_config()
        if not active:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "No active config",
                    }
                },
            )
        config_data = json.loads(active.config_json)
        digest = active.config_digest
    else:
        # draft logic not strictly required by spec for export but nice to
        # have?
        # Spec says: enum: [active, draft]. So yes.
        # But we need ID for draft.
        return JSONResponse(
            status_code=501,
            content={
                "error": {
                    "code": "NOT_IMPLEMENTED",
                    "message": "Draft export not implemented yet",
                }
            },
        )

    if body.redacted:
        config_data = redact_config(config_data)

    content = ""
    if body.format == "json":
        content = json.dumps(config_data, indent=2)
        content_type = "application/json"
        filename = f"talos.config.{digest[:8]}.json"
    else:
        # Need yaml dump. Standard json->yaml
        # Import moved to top
        content = yaml.safe_dump(config_data, sort_keys=False)
        content_type = "text/yaml"
        filename = f"talos.config.{digest[:8]}.yaml"

    return ExportResponse(
        content=content, filename=filename, content_type=content_type
    )


@router.get("/active", response_model=HealthResponse)  # type: ignore
async def active_config() -> HealthResponse:
    """Retrieve the currently active configuration status.

    Returns:
        HealthResponse: Current service health and configuration.
    """
    return await health()
