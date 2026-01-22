#!/usr/bin/env python3
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, ValidationError, validator

class ContractsPin(BaseModel):
    type: str # "artifact"
    name: str # "talos-contracts"
    version: str # e.g. "1.2.3"

class InteropConfig(BaseModel):
    enabled: bool = False
    command: Optional[str] = None
    contracts_pin: Optional[ContractsPin] = None
    required: bool = False

    @validator('contracts_pin')
    def validate_pin_if_enabled(cls, v, values):
        if values.get('enabled') and not v:
            raise ValueError("contracts_pin is required when interop is enabled")
        return v

class Thresholds(BaseModel):
    line: float = Field(..., ge=0, le=1)
    branch: Optional[float] = Field(None, ge=0, le=1)

class CriticalPath(BaseModel):
    path: str
    line: float = Field(..., ge=0, le=1)
    branch: Optional[float] = Field(None, ge=0, le=1)

class CoverageThresholds(BaseModel):
    unit: Thresholds
    critical_paths: List[CriticalPath] = []

class CoverageConfig(BaseModel):
    tool: str
    reports: Dict[str, str]
    thresholds: CoverageThresholds
    exclusions: List[str] = []

class Entrypoints(BaseModel):
    unit: str
    integration: Optional[str] = None
    smoke: Optional[str] = None
    lint: Optional[str] = None
    typecheck: Optional[str] = None

class InfraRequirements(BaseModel):
    requires_postgres: Dict[str, bool] = {}
    compose_file: Optional[str] = None

class CIConfig(BaseModel):
    timeout_seconds: Dict[str, int] = {}
    parallelism: Dict[str, int] = {}
    flake_retries: Dict[str, int] = {}

class TestManifest(BaseModel):
    manifest_version: str = "v1"
    repo_id: str
    entrypoints: Entrypoints
    interop: InteropConfig = Field(default_factory=InteropConfig)
    coverage: Optional[CoverageConfig] = None
    infra: Optional[InfraRequirements] = None
    ci: Optional[CIConfig] = None

    @validator('manifest_version')
    def validate_version(cls, v):
        if v != 'v1':
            raise ValueError("Only manifest_version 'v1' is supported")
        return v

def validate_manifest(path: Path):
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        
        manifest = TestManifest(**data)
        print(f"✅ Manifest valid: {manifest.repo_id}")
        return 0
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return 1
    except yaml.YAMLError as e:
        print(f"❌ YAML Error: {e}")
        return 1
    except ValidationError as e:
        print(f"❌ Validation Error in {path}:")
        for err in e.errors():
            loc = " -> ".join(str(l) for l in err['loc'])
            print(f"  - {loc}: {err['msg']}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate_manifest.py <path_to_manifest>")
        sys.exit(1)
    
    sys.exit(validate_manifest(Path(sys.argv[1])))
