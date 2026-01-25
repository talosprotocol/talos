
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
async def health():
    return {
        "status": "ok",
        "contracts_version": SETTINGS.CONTRACTS_VERSION,
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
