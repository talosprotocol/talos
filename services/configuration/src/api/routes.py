
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from src.core.config import SETTINGS
from src.core.validation import validate_and_normalize
from src.core.redaction import redact_config
import json
import importlib.metadata

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

@router.get("/health")
@router.get("/ui-bootstrap")
async def health():
    active = DB.get_current_config()
    return {
        "status": "ok",
        "contracts_version": SETTINGS.CONTRACTS_VERSION,
        "active_config_digest": active.config_digest if active else None,
        "current_config": json.loads(active.config_json) if active else None,
        "version": SETTINGS.VERSION
    }

@router.get("/contracts-version")
async def contracts_version():
    try:
        installed_version = importlib.metadata.version("talos-contracts")
    except importlib.metadata.PackageNotFoundError:
        installed_version = "unknown"

    return {
        "contracts_version": installed_version,
        "config_version_supported": ["1.0"]
    }

@router.get("/schema")
async def get_schema():
    try:
        with open("../../contracts/schemas/config/v1/talos.config.schema.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return JSONResponse(status_code=500, content={"error": "Schema not found"})

@router.post("/validate")
@limiter.limit("10/minute")
async def validate(request: Request):
    # Check Body Size (Content-Length header)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > SETTINGS.MAX_BODY_SIZE_BYTES:
         return JSONResponse(
             status_code=413, 
             content={"error": {"code": "REQUEST_TOO_LARGE", "message": "Payload exceeds 256KB"}}
         )
    
    # Check Body Size (Actual Read)
    body = await request.body()
    if len(body) > SETTINGS.MAX_BODY_SIZE_BYTES:
         return JSONResponse(
             status_code=413, 
             content={"error": {"code": "REQUEST_TOO_LARGE", "message": "Payload exceeds 256KB"}}
         )
         
    try:
        payload = json.loads(body)
        config = payload.get("config")
        if not config:
            return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Missing 'config' field"}})
            
        strict = payload.get("strict", True) # Default true
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Invalid JSON"}})

    valid, errors, normalized, _ = validate_and_normalize(config, strict=strict)
    
    if not valid:
        # 400 with Schema Errors
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "errors": errors
            }
        )
        
    return {
        "valid": True,
        "errors": [],
        "normalized_config": redact_config(normalized)
    }

@router.post("/normalize")
@limiter.limit("50/minute")
async def normalize(request: Request):
     # Size Check
    body = await request.body()
    if len(body) > SETTINGS.MAX_BODY_SIZE_BYTES:
         return JSONResponse(
             status_code=413, 
             content={"error": {"code": "REQUEST_TOO_LARGE", "message": "Payload exceeds 256KB"}}
         )

    try:
        payload = json.loads(body)
        config = payload.get("config")
        if not config:
             return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Missing 'config' field"}})
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Invalid JSON"}})

    valid, errors, normalized, digest = validate_and_normalize(config, strict=True)
    
    if not valid:
        return JSONResponse(
             status_code=400,
             content={"error": {"code": "SCHEMA_VALIDATION_FAILED", "message": "Invalid config", "details": errors}}
        )


    return {
        "normalized_config": redact_config(normalized),
        "config_digest": digest
    }

from src.core.storage import Database, ConfigDraft, ConfigHistory, IdempotencyRecord
from src.core.utils import encode_cursor, decode_cursor, check_idempotency_conflict, compute_body_digest
from datetime import datetime, timezone
from typing import Optional
import uuid

# Global DB instance (Singleton for this worker)
DB = Database()

@router.post("/drafts")
async def create_draft(request: Request):
    # Idempotency Check
    key = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
    if not key:
        return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Missing Idempotency-Key"}})
    
    principal = request.headers.get("X-Talos-Principal-Id", "dev" if SETTINGS.DEV_MODE else None)
    if not principal:
        return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHORIZED", "message": "Missing Principal ID"}})
        
    body_bytes = await request.body()
    body_digest = compute_body_digest(body_bytes)
    
    # Check Replay
    record = DB.get_idempotency_record(key, principal, "POST", "/api/config/drafts")
    if record:
        if check_idempotency_conflict(record, body_digest):
             return JSONResponse(status_code=409, content={"error": {"code": "IDEMPOTENCY_KEY_REUSE_CONFLICT", "message": "Conflict"}})
        else:
             # Replay
             return Response(content=record.response_body, status_code=record.response_code, media_type="application/json")

    # Create Draft
    try:
        payload = json.loads(body_bytes)
        config = payload.get("config")
        note = payload.get("note")
        if not config: return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Missing config"}})
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Invalid JSON"}})

    valid, errors, normalized, digest = validate_and_normalize(config, strict=True)
    if not valid:
         return JSONResponse(status_code=400, content={"error": {"code": "SCHEMA_VALIDATION_FAILED", "message": "Invalid config", "details": errors}})
         
    draft_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    
    draft = ConfigDraft(
        draft_id=draft_id,
        principal=principal,
        config_digest=digest,
        config_json=json.dumps(normalized),
        note=note,
        created_at=created_at
    )
    
    DB.save_draft(draft)
    
    response_data = {
        "draft_id": draft_id,
        "config_digest": digest,
        "created_at": created_at.isoformat()
    }
    response_body = json.dumps(response_data)
    
    # Save Idempotency
    DB.save_idempotency_record(IdempotencyRecord(
        key=key, principal=principal, method="POST", path="/api/config/drafts",
        request_digest=body_digest, response_code=200, response_body=response_body, created_at=created_at
    ))
    
    return Response(content=response_body, media_type="application/json")

@router.post("/publish")
async def publish_draft(request: Request):
    key = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
    if not key: return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Missing Idempotency-Key"}})
    
    principal = request.headers.get("X-Talos-Principal-Id", "dev" if SETTINGS.DEV_MODE else None)
    if not principal: return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHORIZED", "message": "Missing Principal ID"}})

    body_bytes = await request.body()
    body_digest = compute_body_digest(body_bytes)
    
    record = DB.get_idempotency_record(key, principal, "POST", "/api/config/publish")
    if record:
        if check_idempotency_conflict(record, body_digest):
             return JSONResponse(status_code=409, content={"error": {"code": "IDEMPOTENCY_KEY_REUSE_CONFLICT", "message": "Conflict"}})
        else:
             return Response(content=record.response_body, status_code=record.response_code, media_type="application/json")

    try:
        payload = json.loads(body_bytes)
        draft_id = payload.get("draft_id")
        if not draft_id: return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Missing draft_id"}})
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Invalid JSON"}})

    draft = DB.get_draft(draft_id)
    if not draft:
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Draft not found"}})
        
    # Promote to History
    config_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    
    history = ConfigHistory(
        id=config_id,
        draft_id=draft.draft_id,
        config_digest=draft.config_digest,
        config_json=draft.config_json,
        principal=principal,
        created_at=created_at
    )
    
    DB.publish_draft(history)
    
    response_data = {
        "active_config_id": config_id,
        "active_config_digest": draft.config_digest
    }
    response_body = json.dumps(response_data)
    
    DB.save_idempotency_record(IdempotencyRecord(
        key=key, principal=principal, method="POST", path="/api/config/publish",
        request_digest=body_digest, response_code=200, response_body=response_body, created_at=created_at
    ))
    
    return Response(content=response_body, media_type="application/json")

@router.get("/history")
async def list_history(limit: int = 50, cursor: Optional[str] = None):
    if limit > 200: limit = 200
    if limit < 1: limit = 50
    
    before_created_at = None
    before_id = None
    
    if cursor:
        try:
            before_created_at, before_id = decode_cursor(cursor)
        except ValueError:
            return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Invalid cursor"}})
            
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
        records.append({
            "id": item.id,
            "config_digest": item.config_digest,
            "created_at": item.created_at.isoformat(),
            "redacted_config": redacted
        })
        
    return {
        "items": records,
        "next_cursor": next_cursor,
        "has_more": len(items) == limit
    }

@router.post("/export")
async def export_config(request: Request):
    try:
        body = await request.json()
        format = body.get("format", "yaml")
        src = body.get("source", "active")
        redacted = body.get("redacted", True)
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": {"code": "BAD_REQUEST", "message": "Invalid JSON"}})

    config_data = None
    digest = None
    
    if src == "active":
        active = DB.get_current_config()
        if not active:
             return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "No active config"}})
        config_data = json.loads(active.config_json)
        digest = active.config_digest
    else:
        # draft logic not strictly required by spec for export but nice to have?
        # Spec says: enum: [active, draft]. So yes.
        # But we need ID for draft.
        return JSONResponse(status_code=501, content={"error": {"code": "NOT_IMPLEMENTED", "message": "Draft export not implemented yet"}})

    if redacted:
        config_data = redact_config(config_data)
        
    content = ""
    if format == "json":
        content = json.dumps(config_data, indent=2)
        content_type = "application/json"
        filename = f"talos.config.{digest[:8]}.json"
    else:
        # Need yaml dump. Standard json->yaml
        # Import yaml locally since we didn't add it to routes imports yet
        import yaml
        content = yaml.safe_dump(config_data, sort_keys=False)
        content_type = "text/yaml"
        filename = f"talos.config.{digest[:8]}.yaml"
        
    return {
        "content": content,
        "filename": filename,
        "content_type": content_type
    }
