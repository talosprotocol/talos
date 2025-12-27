"""
Validation Report Generation.

Generates detailed audit reports for block and chain validation,
useful for debugging, compliance, and transparency.
"""

import json
import logging
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Any, Optional

from ..blockchain import Block

logger = logging.getLogger(__name__)


class ValidationReport(BaseModel):
    """
    Comprehensive validation audit report.
    
    Contains detailed information about validation results
    for compliance and debugging purposes.
    """

    # Identification
    report_id: str = ""
    generated_at: str = ""
    validator_version: str = "2.0.0"

    # Subject
    block_hash: str = ""
    block_index: int = 0
    block_timestamp: float = 0.0

    # Results
    is_valid: bool = False
    validation_level: str = ""
    duration_ms: float = 0.0

    # Layer results
    layer_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # Errors and warnings
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Cryptographic verification
    hash_verified: bool = False
    merkle_verified: bool = False
    pow_verified: bool = False
    signatures_verified: int = 0
    signatures_failed: int = 0

    # Chain context
    previous_block_hash: Optional[str] = None
    chain_height: int = 0
    total_work: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "validator_version": self.validator_version,
            "subject": {
                "block_hash": self.block_hash,
                "block_index": self.block_index,
                "block_timestamp": self.block_timestamp,
            },
            "result": {
                "is_valid": self.is_valid,
                "validation_level": self.validation_level,
                "duration_ms": self.duration_ms,
            },
            "layer_results": self.layer_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "cryptographic": {
                "hash_verified": self.hash_verified,
                "merkle_verified": self.merkle_verified,
                "pow_verified": self.pow_verified,
                "signatures_verified": self.signatures_verified,
                "signatures_failed": self.signatures_failed,
            },
            "chain_context": {
                "previous_block_hash": self.previous_block_hash,
                "chain_height": self.chain_height,
                "total_work": self.total_work,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Generate markdown-formatted report."""
        lines = [
            "# Block Validation Report",
            "",
            f"**Report ID**: `{self.report_id}`",
            f"**Generated**: {self.generated_at}",
            f"**Validator Version**: {self.validator_version}",
            "",
            "---",
            "",
            "## Subject Block",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| **Hash** | `{self.block_hash[:16]}...` |",
            f"| **Index** | {self.block_index} |",
            f"| **Timestamp** | {datetime.fromtimestamp(self.block_timestamp).isoformat()} |",
            "",
            "## Validation Result",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| **Valid** | {'✅ Yes' if self.is_valid else '❌ No'} |",
            f"| **Level** | {self.validation_level} |",
            f"| **Duration** | {self.duration_ms:.2f}ms |",
            "",
        ]

        # Layer results table
        if self.layer_results:
            lines.extend([
                "## Layer Results",
                "",
                "| Layer | Status | Details |",
                "|-------|--------|---------|",
            ])
            for layer, result in self.layer_results.items():
                status = "✅" if result.get("passed") else "❌"
                details = result.get("message", "-")
                lines.append(f"| {layer} | {status} | {details} |")
            lines.append("")

        # Errors
        if self.errors:
            lines.extend([
                "## Errors",
                "",
            ])
            for err in self.errors:
                lines.append(f"- **{err.get('code')}**: {err.get('message')}")
            lines.append("")

        # Cryptographic details
        lines.extend([
            "## Cryptographic Verification",
            "",
            "| Check | Result |",
            "|-------|--------|",
            f"| Hash Integrity | {'✅' if self.hash_verified else '❌'} |",
            f"| Merkle Root | {'✅' if self.merkle_verified else '❌'} |",
            f"| Proof of Work | {'✅' if self.pow_verified else '❌'} |",
            f"| Signatures | {self.signatures_verified} passed, {self.signatures_failed} failed |",
            "",
        ])

        return "\n".join(lines)


def generate_audit_report(
    block: Block,
    validation_result: Any,
    chain_context: Optional[dict[str, Any]] = None,
) -> ValidationReport:
    """
    Generate a comprehensive audit report for a validated block.
    
    Args:
        block: The validated block
        validation_result: ValidationResult from the engine
        chain_context: Optional chain metadata
        
    Returns:
        ValidationReport with full details
    """
    import uuid

    report = ValidationReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        block_hash=block.hash,
        block_index=block.index,
        block_timestamp=block.timestamp,
        is_valid=validation_result.is_valid,
        validation_level=getattr(validation_result, 'level', 'STRICT'),
        duration_ms=validation_result.duration_ms,
        errors=[e.to_dict() if hasattr(e, 'to_dict') else e for e in validation_result.errors],
        warnings=validation_result.warnings,
    )

    # Layer results
    for layer in validation_result.layers_passed:
        report.layer_results[layer] = {"passed": True, "message": "OK"}
    for layer in validation_result.layers_failed:
        report.layer_results[layer] = {"passed": False, "message": "Failed"}

    # Crypto verification flags
    report.hash_verified = "cryptographic" in validation_result.layers_passed
    report.merkle_verified = report.hash_verified  # Included in crypto layer
    report.pow_verified = "consensus" in validation_result.layers_passed

    # Chain context
    if chain_context:
        report.previous_block_hash = chain_context.get("previous_hash")
        report.chain_height = chain_context.get("height", 0)
        report.total_work = chain_context.get("total_work", 0)

    return report


def generate_chain_report(
    blocks: list[Block],
    validation_results: list[Any],
    chain_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Generate a summary report for chain validation.
    
    Args:
        blocks: List of validated blocks
        validation_results: List of ValidationResult for each block
        chain_metadata: Optional chain metadata
        
    Returns:
        Summary report dict
    """
    import uuid

    total_blocks = len(blocks)
    valid_blocks = sum(1 for r in validation_results if r.is_valid)
    total_time = sum(r.duration_ms for r in validation_results)

    all_errors = []
    for i, result in enumerate(validation_results):
        for error in result.errors:
            err_dict = error.to_dict() if hasattr(error, 'to_dict') else dict(error)
            err_dict['block_index'] = i
            all_errors.append(err_dict)

    return {
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "chain_summary": {
            "total_blocks": total_blocks,
            "valid_blocks": valid_blocks,
            "invalid_blocks": total_blocks - valid_blocks,
            "validation_rate": valid_blocks / total_blocks if total_blocks else 0,
        },
        "performance": {
            "total_time_ms": total_time,
            "avg_time_per_block_ms": total_time / total_blocks if total_blocks else 0,
            "blocks_per_second": 1000 * total_blocks / total_time if total_time else 0,
        },
        "errors": all_errors,
        "chain_metadata": chain_metadata or {},
    }
