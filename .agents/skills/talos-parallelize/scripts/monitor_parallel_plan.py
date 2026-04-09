#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from schema_utils import validate_payload


VALID_STATES = {"pending", "ready", "running", "paused", "blocked", "done", "failed"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recommend start/pause/advance decisions for a Talos parallelization plan."
    )
    parser.add_argument("plan", help="Path to a plan JSON emitted by parallelize_task.py")
    parser.add_argument("status", help="Path to a task status JSON file")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def normalize_status(plan: dict[str, Any], status_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_tasks = status_payload.get("tasks", {})
    if not isinstance(raw_tasks, dict):
        raise ValueError("status file must contain a tasks object")

    normalized: dict[str, dict[str, Any]] = {}
    for task in plan["tasks"]:
        raw_entry = raw_tasks.get(task["id"], {})
        if raw_entry is None:
            raw_entry = {}
        if not isinstance(raw_entry, dict):
            raise ValueError(f"status entry for {task['id']} must be an object")
        state = raw_entry.get("state", "pending")
        if not isinstance(state, str) or state not in VALID_STATES:
            raise ValueError(f"invalid state for {task['id']}: {state!r}")
        normalized[task["id"]] = {
            "state": state,
            "notes": raw_entry.get("notes", "") if isinstance(raw_entry.get("notes"), str) else "",
        }
    return normalized


def conflict_map(plan: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    mapping: dict[str, dict[str, list[str]]] = {}
    for task in plan["tasks"]:
        mapping[task["id"]] = {
            item["task_id"]: item["reasons"]
            for item in task.get("conflicts", [])
            if isinstance(item, dict) and isinstance(item.get("task_id"), str)
        }
    return mapping


def stage_lookup(plan: dict[str, Any]) -> dict[str, int]:
    lookup: dict[str, int] = {}
    for stage in plan["stages"]:
        for task_id in stage["tasks"]:
            lookup[task_id] = stage["index"]
    return lookup


def active_stage(plan: dict[str, Any], status: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    for stage in plan["stages"]:
        if not all(status[task_id]["state"] == "done" for task_id in stage["tasks"]):
            return stage
    return None


def recommend_actions(plan: dict[str, Any], status: dict[str, dict[str, Any]]) -> dict[str, Any]:
    conflicts = conflict_map(plan)
    stages = stage_lookup(plan)
    actions: list[dict[str, Any]] = []
    stage = active_stage(plan, status)

    running = [task_id for task_id, entry in status.items() if entry["state"] == "running"]
    failed = [task_id for task_id, entry in status.items() if entry["state"] == "failed"]

    if failed:
        for task_id in failed:
            actions.append(
                {
                    "task_id": task_id,
                    "action": "collapse_to_serial",
                    "reason": "A lane failed and needs focused recovery before parallel work continues.",
                }
            )

    for i, left in enumerate(running):
        for right in running[i + 1:]:
            reasons = conflicts.get(left, {}).get(right, [])
            if reasons:
                actions.append(
                    {
                        "task_id": right,
                        "action": "pause",
                        "reason": f"Conflicts with running lane {left}: {', '.join(reasons)}",
                    }
                )

    if stage is None:
        actions.append(
            {
                "task_id": None,
                "action": "merge_and_verify",
                "reason": "All planned stages are done. Run the final integration and verification pass.",
            }
        )
        return {
            "active_stage": None,
            "actions": actions,
            "summary": "All planned tasks are marked done.",
        }

    stage_index = stage["index"]
    stage_tasks = stage["tasks"]

    for task_id, entry in status.items():
        if entry["state"] == "running" and stages[task_id] > stage_index:
            actions.append(
                {
                    "task_id": task_id,
                    "action": "pause",
                    "reason": f"Task is running ahead of active stage {stage_index}.",
                }
            )

    if all(status[task_id]["state"] == "done" for task_id in stage_tasks):
        next_stage_index = stage_index + 1
        next_stage = next((item for item in plan["stages"] if item["index"] == next_stage_index), None)
        if next_stage is None:
            actions.append(
                {
                    "task_id": None,
                    "action": "merge_and_verify",
                    "reason": "The final stage is complete.",
                }
            )
        else:
            actions.append(
                {
                    "task_id": None,
                    "action": "advance_stage",
                    "reason": f"Stage {stage_index} is complete. Move to stage {next_stage_index}.",
                }
            )
        return {
            "active_stage": stage_index,
            "actions": actions,
            "summary": f"Stage {stage_index} is complete.",
        }

    for task_id in stage_tasks:
        entry = status[task_id]
        if entry["state"] == "pending":
            actions.append(
                {
                    "task_id": task_id,
                    "action": "start",
                    "reason": f"Task is ready in active stage {stage_index}.",
                }
            )
        elif entry["state"] == "ready":
            actions.append(
                {
                    "task_id": task_id,
                    "action": "start",
                    "reason": f"Task is marked ready in active stage {stage_index}.",
                }
            )
        elif entry["state"] == "running":
            actions.append(
                {
                    "task_id": task_id,
                    "action": "continue",
                    "reason": f"Task is already running in active stage {stage_index}.",
                }
            )
        elif entry["state"] == "paused":
            actions.append(
                {
                    "task_id": task_id,
                    "action": "resume",
                    "reason": f"Task belongs to active stage {stage_index}.",
                }
            )
        elif entry["state"] == "blocked":
            actions.append(
                {
                    "task_id": task_id,
                    "action": "wait",
                    "reason": f"Task is blocked inside active stage {stage_index}.",
                }
            )

    waiting_tasks = [
        task["id"]
        for task in plan["tasks"]
        if stages[task["id"]] > stage_index and status[task["id"]]["state"] in {"pending", "ready"}
    ]
    for task_id in waiting_tasks:
        actions.append(
            {
                "task_id": task_id,
                "action": "wait",
                "reason": f"Task belongs to a later stage than active stage {stage_index}.",
            }
        )

    return {
        "active_stage": stage_index,
        "actions": actions,
        "summary": f"Stage {stage_index} is active.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Parallel Monitoring Decision", ""]
    if report["active_stage"] is None:
        lines.append("Active stage: complete")
    else:
        lines.append(f"Active stage: {report['active_stage']}")
    lines.extend(["", report["summary"], "", "## Actions", ""])
    for action in report["actions"]:
        task_label = action["task_id"] if action["task_id"] is not None else "plan"
        lines.append(f"- `{task_label}` -> `{action['action']}`: {action['reason']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    plan = load_json(Path(args.plan))
    status_payload = load_json(Path(args.status))
    validate_payload("parallel-plan.schema.json", plan)
    validate_payload("parallel-status.schema.json", status_payload)
    status = normalize_status(plan, status_payload)
    report = recommend_actions(plan, status)
    validate_payload("parallel-decision.schema.json", report)
    if args.format == "markdown":
        print(render_markdown(report))
        return 0
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
