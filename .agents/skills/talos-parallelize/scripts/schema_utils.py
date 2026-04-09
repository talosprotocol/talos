#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "assets" / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    payload = json.loads((SCHEMA_DIR / name).read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"schema {name} must be a JSON object")
    Draft7Validator.check_schema(payload)
    return payload


def validate_payload(name: str, payload: Any) -> None:
    Draft7Validator(load_schema(name)).validate(payload)
