from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PLAN_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "talos-parallelize"
    / "scripts"
    / "parallelize_task.py"
)

MONITOR_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "talos-parallelize"
    / "scripts"
    / "monitor_parallel_plan.py"
)


def make_plan(tmp_path: Path, manifest: dict) -> Path:
    manifest_path = tmp_path / "task.json"
    plan_path = tmp_path / "plan.json"
    manifest_path.write_text(json.dumps(manifest))
    proc = subprocess.run(
        [sys.executable, str(PLAN_SCRIPT), str(manifest_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    plan_path.write_text(proc.stdout)
    return plan_path


def run_monitor(tmp_path: Path, plan_path: Path, status: dict) -> dict:
    status_path = tmp_path / "status.json"
    status_path.write_text(json.dumps(status))
    proc = subprocess.run(
        [sys.executable, str(MONITOR_SCRIPT), str(plan_path), str(status_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout)


def test_monitor_parallel_plan_recommends_stage_actions(tmp_path: Path) -> None:
    plan_path = make_plan(
        tmp_path,
        {
            "goal": "Freeze a contract and then fan out.",
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
        },
    )

    report = run_monitor(
        tmp_path,
        plan_path,
        {"tasks": {"contract": {"state": "done"}, "python": {"state": "running"}, "docs": {"state": "pending"}}},
    )

    assert report["active_stage"] == 2
    actions = {(item["task_id"], item["action"]) for item in report["actions"]}
    assert ("python", "continue") in actions
    assert ("docs", "start") in actions


def test_monitor_parallel_plan_recommends_pause_on_conflicting_running_lanes(tmp_path: Path) -> None:
    plan_path = make_plan(
        tmp_path,
        {
            "goal": "Two conflicting backend lanes.",
            "tasks": [
                {
                    "id": "auth-a",
                    "summary": "First edit",
                    "owner_hint": "backend",
                    "writes": ["services/ai-gateway/app/dependencies.py"],
                    "runtime_resources": ["gateway:8000"],
                },
                {
                    "id": "auth-b",
                    "summary": "Second edit",
                    "owner_hint": "backend",
                    "writes": ["services/ai-gateway/app/dependencies.py"],
                    "runtime_resources": ["gateway:8000"],
                },
            ],
        },
    )

    report = run_monitor(
        tmp_path,
        plan_path,
        {"tasks": {"auth-a": {"state": "running"}, "auth-b": {"state": "running"}}},
    )

    pause_actions = [item for item in report["actions"] if item["action"] == "pause"]
    assert pause_actions
    assert "shared_writes:" in pause_actions[0]["reason"]


def test_monitor_parallel_plan_recommends_merge_when_complete(tmp_path: Path) -> None:
    plan_path = make_plan(
        tmp_path,
        {
            "goal": "One simple task.",
            "tasks": [
                {
                    "id": "docs",
                    "summary": "Update docs",
                    "owner_hint": "docs",
                    "writes": ["docs/guide.md"],
                }
            ],
        },
    )

    report = run_monitor(tmp_path, plan_path, {"tasks": {"docs": {"state": "done"}}})
    assert report["active_stage"] is None
    assert report["actions"][0]["action"] == "merge_and_verify"
