#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from monitor_parallel_plan import normalize_status, recommend_actions, render_markdown as render_decision_markdown
from parallelize_task import build_report, load_manifest
from schema_utils import validate_payload


PLAN_FILENAME = "plan.json"
STATUS_FILENAME = "status.json"
MANIFEST_FILENAME = "manifest.json"
VALID_STATES = {"pending", "ready", "running", "paused", "blocked", "done", "failed"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize and monitor a Talos parallel-work run directory."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a run directory from a task manifest")
    init_parser.add_argument("manifest", help="Path to the task manifest JSON")
    init_parser.add_argument("run_dir", help="Directory to write manifest/plan/status into")
    init_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )

    decide_parser = subparsers.add_parser("decide", help="Recommend next actions from a run directory")
    decide_parser.add_argument("run_dir", help="Directory containing plan.json and status.json")
    decide_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )

    set_state_parser = subparsers.add_parser("set-state", help="Update one task state in status.json")
    set_state_parser.add_argument("run_dir", help="Directory containing status.json")
    set_state_parser.add_argument("task_id", help="Task identifier")
    set_state_parser.add_argument("state", choices=sorted(VALID_STATES), help="New task state")
    set_state_parser.add_argument("--notes", default="", help="Optional task notes")
    set_state_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )

    status_parser = subparsers.add_parser("status", help="Render current run state")
    status_parser.add_argument("run_dir", help="Directory containing plan.json and status.json")
    status_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )

    handoff_parser = subparsers.add_parser(
        "handoffs",
        help="Emit lane handoffs for tasks that should start or resume",
    )
    handoff_parser.add_argument("run_dir", help="Directory containing plan.json and status.json")
    handoff_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )

    return parser.parse_args(argv)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _run_paths(run_dir: Path) -> tuple[Path, Path, Path]:
    return (
        run_dir / MANIFEST_FILENAME,
        run_dir / PLAN_FILENAME,
        run_dir / STATUS_FILENAME,
    )


def _default_status(plan: dict[str, Any]) -> dict[str, Any]:
    first_stage_index = plan["stages"][0]["index"] if plan["stages"] else None
    first_stage_tasks = set(plan["stages"][0]["tasks"]) if plan["stages"] else set()
    tasks = {}
    for task in plan["tasks"]:
        tasks[task["id"]] = {
            "state": "ready" if task["id"] in first_stage_tasks and first_stage_index == 1 else "pending",
            "notes": "",
        }
    return {"tasks": tasks}


def _render_status_markdown(plan: dict[str, Any], status_payload: dict[str, Any]) -> str:
    lines = ["# Parallel Run Status", ""]
    if plan.get("goal"):
        lines.extend(["## Goal", "", plan["goal"], ""])
    lines.extend(["## Tasks", ""])
    for stage in plan["stages"]:
        lines.append(f"### Stage {stage['index']} ({stage['mode']})")
        lines.append("")
        for task_id in stage["tasks"]:
            task = next(item for item in plan["tasks"] if item["id"] == task_id)
            status = status_payload["tasks"][task_id]
            lines.append(
                f"- `{task_id}` [{status['state']}] {task['summary']} [{task['suggested_skill']}]"
            )
        lines.append("")
    return "\n".join(lines)


def _render_handoffs_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Parallel Lane Handoffs", ""]
    lines.append(f"Active stage: {payload['active_stage'] if payload['active_stage'] is not None else 'complete'}")
    lines.append("")
    if not payload["handoffs"]:
        lines.append("No lanes should start or resume right now.")
        lines.append("")
        return "\n".join(lines)

    for handoff in payload["handoffs"]:
        lines.append(f"## `{handoff['task_id']}`")
        lines.append("")
        lines.append(f"- Action: `{handoff['action']}`")
        lines.append(f"- Skill: `{handoff['suggested_skill']}`")
        lines.append(f"- Summary: {handoff['summary']}")
        if handoff["depends_on"]:
            lines.append(f"- Depends On: {', '.join(handoff['depends_on'])}")
        if handoff["writes"]:
            lines.append(f"- Writes: {', '.join(handoff['writes'])}")
        if handoff["verify"]:
            lines.append(f"- Verify: {' | '.join(handoff['verify'])}")
        lines.append(f"- Reason: {handoff['reason']}")
        lines.append("")
        lines.append("Prompt:")
        lines.append("")
        lines.append("```text")
        lines.append(handoff["prompt"])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _render_init_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Parallel Run Initialized",
        "",
        f"- Run Dir: `{payload['run_dir']}`",
        f"- Plan File: `{payload['plan_file']}`",
        f"- Status File: `{payload['status_file']}`",
        "",
        "## Initial Decision",
        "",
    ]
    decision = payload["initial_decision"]
    lines.append(render_decision_markdown(decision))
    return "\n".join(lines)


def _render_output(payload: dict[str, Any], fmt: str, *, plan: dict[str, Any] | None = None) -> str:
    if fmt == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    if {"run_dir", "plan_file", "status_file", "initial_decision"} <= payload.keys():
        return _render_init_markdown(payload)
    if "handoffs" in payload and "active_stage" in payload:
        return _render_handoffs_markdown(payload)
    if plan is not None and payload.keys() == {"tasks"}:
        return _render_status_markdown(plan, payload)
    return render_decision_markdown(payload)


def init_run(manifest_path: Path, run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_manifest(manifest_path)
    plan = build_report(manifest)
    validate_payload("parallel-plan.schema.json", plan)

    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_out, plan_out, status_out = _run_paths(run_dir)
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    plan_out.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    status_payload = _default_status(plan)
    validate_payload("parallel-status.schema.json", status_payload)
    status_out.write_text(json.dumps(status_payload, indent=2, sort_keys=True) + "\n")
    return plan, status_payload


def load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _manifest_path, plan_path, status_path = _run_paths(run_dir)
    plan = _load_json(plan_path)
    status_payload = _load_json(status_path)
    validate_payload("parallel-plan.schema.json", plan)
    validate_payload("parallel-status.schema.json", status_payload)
    return plan, status_payload


def update_state(run_dir: Path, task_id: str, state: str, notes: str) -> dict[str, Any]:
    plan, status_payload = load_run(run_dir)
    status = normalize_status(plan, status_payload)
    if task_id not in status:
        raise ValueError(f"unknown task id: {task_id}")
    status_payload["tasks"][task_id] = {"state": state, "notes": notes}
    validate_payload("parallel-status.schema.json", status_payload)
    _status_path = _run_paths(run_dir)[2]
    _status_path.write_text(json.dumps(status_payload, indent=2, sort_keys=True) + "\n")
    return status_payload


def decide(run_dir: Path) -> dict[str, Any]:
    plan, status_payload = load_run(run_dir)
    status = normalize_status(plan, status_payload)
    report = recommend_actions(plan, status)
    validate_payload("parallel-decision.schema.json", report)
    return report


def build_handoffs(run_dir: Path) -> dict[str, Any]:
    plan, status_payload = load_run(run_dir)
    status = normalize_status(plan, status_payload)
    decision = recommend_actions(plan, status)
    task_map = {task["id"]: task for task in plan["tasks"]}
    handoffs: list[dict[str, Any]] = []

    for action in decision["actions"]:
        task_id = action["task_id"]
        if task_id is None or action["action"] not in {"start", "resume"}:
            continue
        task = task_map[task_id]
        prompt_lines = [
            f"Use {task['suggested_skill']} for lane `{task_id}`.",
            f"Goal: {task['summary']}",
        ]
        if task["depends_on"]:
            prompt_lines.append(f"Dependencies already satisfied: {', '.join(task['depends_on'])}.")
        if task["writes"]:
            prompt_lines.append(f"Write scope: {', '.join(task['writes'])}.")
        if task["verify"]:
            prompt_lines.append(f"Verify with: {' | '.join(task['verify'])}.")
        if task["done"]:
            prompt_lines.append(f"Done when: {task['done']}")
        prompt_lines.append(f"Reason to act now: {action['reason']}")
        handoffs.append(
            {
                "task_id": task_id,
                "action": action["action"],
                "reason": action["reason"],
                "suggested_skill": task["suggested_skill"],
                "summary": task["summary"],
                "depends_on": task["depends_on"],
                "writes": task["writes"],
                "verify": task["verify"],
                "prompt": " ".join(prompt_lines),
            }
        )

    payload = {
        "active_stage": decision["active_stage"],
        "handoffs": handoffs,
    }
    validate_payload("parallel-handoffs.schema.json", payload)
    return payload


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.command == "init":
        plan, status_payload = init_run(Path(args.manifest), Path(args.run_dir))
        decision = recommend_actions(plan, normalize_status(plan, status_payload))
        output = {
            "run_dir": str(Path(args.run_dir).resolve()),
            "plan_file": str((Path(args.run_dir) / PLAN_FILENAME).resolve()),
            "status_file": str((Path(args.run_dir) / STATUS_FILENAME).resolve()),
            "initial_decision": decision,
        }
        print(_render_output(output, args.format))
        return 0

    if args.command == "decide":
        decision = decide(Path(args.run_dir))
        print(_render_output(decision, args.format))
        return 0

    if args.command == "set-state":
        plan, _ = load_run(Path(args.run_dir))
        status_payload = update_state(Path(args.run_dir), args.task_id, args.state, args.notes)
        print(_render_output(status_payload, args.format, plan=plan))
        return 0

    if args.command == "status":
        plan, status_payload = load_run(Path(args.run_dir))
        print(_render_output(status_payload, args.format, plan=plan))
        return 0

    if args.command == "handoffs":
        handoffs = build_handoffs(Path(args.run_dir))
        print(_render_output(handoffs, args.format))
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
