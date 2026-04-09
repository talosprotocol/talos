from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "talos-parallelize"
    / "scripts"
    / "parallelize_task.py"
)


def run_planner(tmp_path: Path, manifest: dict) -> dict:
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(json.dumps(manifest))
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifest_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout)


def test_parallelize_task_groups_disjoint_lanes_after_serial_freeze(tmp_path: Path) -> None:
    report = run_planner(
        tmp_path,
        {
            "goal": "Ship a contract and two independent consumers.",
            "tasks": [
                {
                    "id": "contract",
                    "summary": "Freeze contract",
                    "owner_hint": "contract",
                    "serial_only": True,
                    "writes": ["contracts/a2a.json"],
                },
                {
                    "id": "python",
                    "summary": "Update Python SDK",
                    "owner_hint": "sdk",
                    "depends_on": ["contract"],
                    "writes": ["sdks/python/src/talos_sdk/a2a_v1.py"],
                },
                {
                    "id": "docs",
                    "summary": "Update docs",
                    "owner_hint": "docs",
                    "depends_on": ["contract"],
                    "writes": ["docs/guides/a2a.md"],
                },
            ],
        },
    )

    assert report["stages"][0]["mode"] == "serial"
    assert report["stages"][0]["tasks"] == ["contract"]
    assert report["stages"][1]["mode"] == "parallel"
    assert report["stages"][1]["tasks"] == ["python", "docs"]

    python_task = next(task for task in report["tasks"] if task["id"] == "python")
    docs_task = next(task for task in report["tasks"] if task["id"] == "docs")
    assert python_task["suggested_skill"] == "$talos-sdk-parity"
    assert docs_task["suggested_skill"] == "$talos-docs-parity"


def test_parallelize_task_serializes_shared_write_and_runtime_conflicts(tmp_path: Path) -> None:
    report = run_planner(
        tmp_path,
        {
            "goal": "Avoid overlapping edits and one shared port.",
            "tasks": [
                {
                    "id": "gateway-auth",
                    "summary": "Edit auth middleware",
                    "owner_hint": "backend",
                    "writes": ["services/ai-gateway/app/middleware/auth_public.py"],
                    "runtime_resources": ["gateway:8000"],
                },
                {
                    "id": "gateway-rpc",
                    "summary": "Edit rpc auth path",
                    "owner_hint": "backend",
                    "writes": ["services/ai-gateway/app/middleware/auth_public.py"],
                    "runtime_resources": ["gateway:8000"],
                },
            ],
        },
    )

    assert report["stages"][0]["tasks"] == ["gateway-auth"]
    assert report["stages"][0]["mode"] == "serial"
    assert report["stages"][1]["tasks"] == ["gateway-rpc"]

    auth_task = next(task for task in report["tasks"] if task["id"] == "gateway-auth")
    conflict_reasons = auth_task["conflicts"][0]["reasons"]
    assert any(reason.startswith("shared_writes:") for reason in conflict_reasons)
    assert any(reason.startswith("shared_runtime:") for reason in conflict_reasons)
