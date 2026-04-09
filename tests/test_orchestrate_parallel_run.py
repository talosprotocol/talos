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
    / "orchestrate_parallel_run.py"
)


def run_cli(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout)


def test_orchestrate_parallel_run_init_creates_run_dir_and_initial_decision(tmp_path: Path) -> None:
    manifest = {
        "goal": "Freeze contract then fan out.",
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
                "writes": ["sdks/python/client.py"],
            },
        ],
    }
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(json.dumps(manifest))
    run_dir = tmp_path / "parallel-run"

    output = run_cli("init", str(manifest_path), str(run_dir))

    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "plan.json").exists()
    assert (run_dir / "status.json").exists()
    first_action = output["initial_decision"]["actions"][0]
    assert first_action["task_id"] == "contract"
    assert first_action["action"] == "start"


def test_orchestrate_parallel_run_set_state_and_decide_advances_stage(tmp_path: Path) -> None:
    manifest = {
        "goal": "Freeze contract then fan out.",
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
                "writes": ["sdks/python/client.py"],
            },
            {
                "id": "docs",
                "summary": "Update docs",
                "owner_hint": "docs",
                "depends_on": ["contract"],
                "writes": ["docs/a2a.md"],
            },
        ],
    }
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(json.dumps(manifest))
    run_dir = tmp_path / "parallel-run"

    run_cli("init", str(manifest_path), str(run_dir))
    run_cli("set-state", str(run_dir), "contract", "done")

    decision = run_cli("decide", str(run_dir))
    actions = {(item["task_id"], item["action"]) for item in decision["actions"]}
    assert ("python", "start") in actions
    assert ("docs", "start") in actions

    status = run_cli("set-state", str(run_dir), "python", "running")
    assert status["tasks"]["python"]["state"] == "running"


def test_orchestrate_parallel_run_status_renders_current_task_states(tmp_path: Path) -> None:
    manifest = {
        "goal": "One task.",
        "tasks": [
            {
                "id": "docs",
                "summary": "Update docs",
                "owner_hint": "docs",
                "writes": ["docs/guide.md"],
            }
        ],
    }
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(json.dumps(manifest))
    run_dir = tmp_path / "parallel-run"
    run_cli("init", str(manifest_path), str(run_dir))

    status = run_cli("status", str(run_dir))
    assert status["tasks"]["docs"]["state"] == "ready"


def test_orchestrate_parallel_run_handoffs_emit_startable_lane_prompts(tmp_path: Path) -> None:
    manifest = {
        "goal": "Freeze contract then fan out.",
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
                "writes": ["sdks/python/client.py"],
                "verify": ["cd sdks/python && pytest -q tests/test_a2a_v1_client.py"],
                "done": "Python SDK slice is green.",
            },
            {
                "id": "docs",
                "summary": "Update docs",
                "owner_hint": "docs",
                "depends_on": ["contract"],
                "writes": ["docs/a2a.md"],
            },
        ],
    }
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(json.dumps(manifest))
    run_dir = tmp_path / "parallel-run"

    run_cli("init", str(manifest_path), str(run_dir))
    run_cli("set-state", str(run_dir), "contract", "done")

    handoffs = run_cli("handoffs", str(run_dir))
    assert handoffs["active_stage"] == 2
    task_ids = {item["task_id"] for item in handoffs["handoffs"]}
    assert task_ids == {"python", "docs"}

    python_handoff = next(item for item in handoffs["handoffs"] if item["task_id"] == "python")
    assert python_handoff["suggested_skill"] == "$talos-sdk-parity"
    assert "Use $talos-sdk-parity for lane `python`." in python_handoff["prompt"]
    assert "Verify with: cd sdks/python && pytest -q tests/test_a2a_v1_client.py." in python_handoff["prompt"]
