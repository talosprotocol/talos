from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "talos-parallelize"
SCHEMA_DIR = SKILL_ROOT / "assets" / "schemas"
TASK_TEMPLATE = SKILL_ROOT / "assets" / "task-template.json"
STATUS_TEMPLATE = SKILL_ROOT / "assets" / "status-template.json"
PLANNER = SKILL_ROOT / "scripts" / "parallelize_task.py"
MONITOR = SKILL_ROOT / "scripts" / "monitor_parallel_plan.py"
RUNNER = SKILL_ROOT / "scripts" / "orchestrate_parallel_run.py"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _validate(schema_name: str, payload: dict) -> None:
    schema = _load_json(SCHEMA_DIR / schema_name)
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(payload)


def test_parallelize_skill_templates_validate_against_schemas() -> None:
    _validate("task-manifest.schema.json", _load_json(TASK_TEMPLATE))
    _validate("parallel-status.schema.json", _load_json(STATUS_TEMPLATE))


def test_parallelize_skill_generated_artifacts_validate_against_schemas(tmp_path: Path) -> None:
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(TASK_TEMPLATE.read_text())

    planner = subprocess.run(
        [sys.executable, str(PLANNER), str(manifest_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    plan = json.loads(planner.stdout)
    _validate("parallel-plan.schema.json", plan)

    run_dir = tmp_path / "run"
    subprocess.run(
        [sys.executable, str(RUNNER), "init", str(manifest_path), str(run_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    _validate("parallel-plan.schema.json", _load_json(run_dir / "plan.json"))
    _validate("parallel-status.schema.json", _load_json(run_dir / "status.json"))

    monitor = subprocess.run(
        [sys.executable, str(MONITOR), str(run_dir / "plan.json"), str(run_dir / "status.json")],
        check=True,
        text=True,
        capture_output=True,
    )
    _validate("parallel-decision.schema.json", json.loads(monitor.stdout))

    subprocess.run(
        [sys.executable, str(RUNNER), "set-state", str(run_dir), "contract-freeze", "done"],
        check=True,
        text=True,
        capture_output=True,
    )
    handoffs = subprocess.run(
        [sys.executable, str(RUNNER), "handoffs", str(run_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    _validate("parallel-handoffs.schema.json", json.loads(handoffs.stdout))
