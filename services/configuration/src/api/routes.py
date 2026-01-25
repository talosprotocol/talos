from fastapi import APIRouter
from src.core.config import SETTINGS
import json
import importlib.metadata

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
    # Dynamic check if possible, fallback to setting
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
    # In a real build, this would be loaded from the installed package
    # For now, we mock reading it or read from relative path if in monorepo dev mode
    # Assuming the package 'talos-contracts' includes the schema as package data
    
    # Fallback to local file for dev scaffold
    try:
        with open("../../contracts/schemas/config/v1/talos.config.schema.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Schema not found"}
