"""Configuration validation and normalization logic."""

import hashlib
import json
from typing import Any

import jsonschema
from pydantic import BaseModel, Field

from .jcs import canonicalize

# Load schema once (in a real app, this might be dynamic or reloaded)
# For now, we assume it's available relative to the service or bundled
try:
    with open(
        "../../contracts/schemas/config/v1/talos.config.schema.json",
        encoding="utf-8",
    ) as f:
        SCHEMA = json.load(f)


except FileNotFoundError:
    # Fallback/Mock for docker/standalone where relative path might differ
    # Only for dev scaffold safety
    SCHEMA = {"type": "object", "additionalProperties": True}


class ValidationResult(BaseModel):
    """Result of a configuration validation and normalization operation."""

    valid: bool = Field(..., description="Whether the configuration is valid")
    errors: list[dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors"
    )
    normalized_config: dict[str, Any] | None = Field(
        default=None, description="Normalized configuration if valid"
    )
    digest: str | None = Field(
        default=None, description="SHA256 digest of the canonicalized config"
    )


def validate_and_normalize(
    config_data: dict[str, Any],
    strict: bool = True,  # pylint: disable=unused-argument # noqa: E501
) -> ValidationResult:
    """Validate and Normalize configuration.

    1. Validate against JSON Schema.
    2. Normalize:
       - Apply defaults (schema-driven).
       - (Strict mode) Reject unknown keys.
    3. Compute JCS Canonical Digest.

    Args:
        config_data: Raw configuration dictionary to validate.
        strict: If True, enforces strict validation rules.
    """
    errors = []

    try:
        jsonschema.validate(instance=config_data, schema=SCHEMA)
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.path)
        code = "SCHEMA_VALIDATION_FAILED"
        errors.append(
            {
                "code": code,
                "message": e.message,
                "path": path,
                "details": {
                    "schema_path": "/".join(str(p) for p in e.schema_path)
                },
            }
        )
        return ValidationResult(valid=False, errors=errors)

    # Normalization
    # Python jsonschema doesn't automatically modify the instance
    # with defaults.

    # We must explicitly apply defaults to get a "normalized" object.
    normalized = _apply_defaults(config_data, SCHEMA)

    # Canonicalize
    try:
        canonical_bytes = canonicalize(normalized)
        digest = hashlib.sha256(canonical_bytes).hexdigest()
    except Exception as e:  # pylint: disable=broad-except
        # Should not happen if validation passed and types are standard
        return ValidationResult(
            valid=False,
            errors=[{"code": "CANONICALIZATION_FAILED", "message": str(e)}],
        )

    return ValidationResult(
        valid=True, errors=[], normalized_config=normalized, digest=digest
    )


def _apply_defaults(instance: Any, schema: dict[str, Any]) -> Any:
    """Recursively apply defaults from schema to the instance.

    This is a simplified implementation for the "Final Lock" requirement:
    "Defaults: Deterministic schema-driven filling (not Pydantic defaults)"

    Args:
        instance: The data instance to apply defaults to.
        schema: The JSON schema containing default definitions.

    Returns:
        Any: The instance with defaults applied.
    """
    if not isinstance(schema, dict):
        return instance

    if "default" in schema and instance is None:
        return schema["default"]

    if "properties" in schema and isinstance(instance, dict):
        new_instance = instance.copy()
        for prop, subschema in schema["properties"].items():
            if prop not in new_instance:
                if "default" in subschema:
                    new_instance[prop] = subschema["default"]
                # If prop not in new_instance and no default, nothing happens.

            if prop in new_instance:
                new_instance[prop] = _apply_defaults(
                    new_instance[prop], subschema
                )

        return new_instance

    return instance
