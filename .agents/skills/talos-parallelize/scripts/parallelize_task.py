#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from schema_utils import validate_payload


HINT_TO_SKILL = {
    "contract": "$talos-contract-first",
    "schema": "$talos-contract-first",
    "auth": "$talos-capability-audit",
    "capability": "$talos-capability-audit",
    "audit": "$talos-capability-audit",
    "sdk": "$talos-sdk-parity",
    "docs": "$talos-docs-parity",
    "local-stack": "$talos-local-stack",
    "runtime": "$talos-local-stack",
    "governance": "$talos-governance-agent",
    "backend": "$talos-backend-architect-agent",
    "api-test": "$talos-api-tester-agent",
    "infra": "$talos-infra-maintainer-agent",
    "frontend": "$talos-frontend-developer-agent",
    "ai": "$talos-ai-engineer-agent",
}

PATH_PREFIX_TO_SKILL = (
    ("contracts/", "$talos-contract-first"),
    ("proto/", "$talos-contract-first"),
    ("sdks/", "$talos-sdk-parity"),
    ("docs/", "$talos-docs-parity"),
    ("examples/", "$talos-docs-parity"),
    ("services/", "$talos-backend-architect-agent"),
    ("src/", "$talos-backend-architect-agent"),
    ("site/", "$talos-frontend-developer-agent"),
    ("deploy/", "$talos-infra-maintainer-agent"),
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a dependency-aware Talos parallelization plan from a task manifest."
    )
    parser.add_argument("manifest", help="Path to a JSON task manifest")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args(argv)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    raise ValueError("expected string or list of strings")


def _normalize_path(value: str) -> str:
    text = value.strip().replace("\\", "/")
    return PurePosixPath(text).as_posix().rstrip("/")


def _normalize_paths(values: Any) -> list[str]:
    return [_normalize_path(value) for value in _string_list(values) if value.strip()]


def _overlaps(left: str, right: str) -> bool:
    return (
        left == right
        or left.startswith(right + "/")
        or right.startswith(left + "/")
    )


def _shared_overlap(left: list[str], right: list[str]) -> list[str]:
    matches: list[str] = []
    for left_item in left:
        for right_item in right:
            if _overlaps(left_item, right_item):
                matches.append(left_item if len(left_item) <= len(right_item) else right_item)
    return sorted(dict.fromkeys(matches))


def _shared_runtime(left: list[str], right: list[str]) -> list[str]:
    left_values = {item for item in left if item not in {"", "none"}}
    right_values = {item for item in right if item not in {"", "none"}}
    return sorted(left_values & right_values)


def _suggest_skill(task: dict[str, Any]) -> str:
    hint = task.get("owner_hint")
    if isinstance(hint, str):
        mapped = HINT_TO_SKILL.get(hint.strip().lower())
        if mapped:
            return mapped

    for path in task["writes"]:
        for prefix, skill in PATH_PREFIX_TO_SKILL:
            if path == prefix.rstrip("/") or path.startswith(prefix):
                return skill

    return "$talos-parallel-orchestrator-agent"


def _normalize_task(raw: dict[str, Any], index: int) -> dict[str, Any]:
    task_id = raw.get("id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError(f"task {index} is missing a string id")
    summary = raw.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError(f"task {task_id} is missing a string summary")

    task = {
        "id": task_id,
        "summary": summary,
        "depends_on": _string_list(raw.get("depends_on")),
        "writes": _normalize_paths(raw.get("writes")),
        "generated_outputs": _normalize_paths(raw.get("generated_outputs")),
        "runtime_resources": [item.strip().lower() for item in _string_list(raw.get("runtime_resources")) if item.strip()],
        "verify": _string_list(raw.get("verify")),
        "done": raw.get("done") if isinstance(raw.get("done"), str) else "",
        "serial_only": bool(raw.get("serial_only", False)),
        "owner_hint": raw.get("owner_hint") if isinstance(raw.get("owner_hint"), str) else "",
        "exclusive_boundaries": [item.strip().lower() for item in _string_list(raw.get("exclusive_boundaries")) if item.strip()],
        "notes": _string_list(raw.get("notes")),
    }
    task["suggested_skill"] = _suggest_skill(task)
    return task


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    validate_payload("task-manifest.schema.json", payload)
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("manifest must contain a non-empty tasks list")

    normalized_tasks = [_normalize_task(task, index) for index, task in enumerate(tasks)]
    task_ids = {task["id"] for task in normalized_tasks}
    for task in normalized_tasks:
        missing = [dep for dep in task["depends_on"] if dep not in task_ids]
        if missing:
            raise ValueError(f"task {task['id']} depends on unknown tasks: {', '.join(missing)}")

    return {
        "goal": payload.get("goal") if isinstance(payload.get("goal"), str) else "",
        "tasks": normalized_tasks,
    }


def conflict_reasons(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    if left["serial_only"] or right["serial_only"]:
        reasons.append("serial_only")

    shared_writes = _shared_overlap(left["writes"], right["writes"])
    if shared_writes:
        reasons.append(f"shared_writes:{', '.join(shared_writes)}")

    shared_generated = _shared_overlap(left["generated_outputs"], right["generated_outputs"])
    if shared_generated:
        reasons.append(f"shared_generated:{', '.join(shared_generated)}")

    shared_runtime = _shared_runtime(left["runtime_resources"], right["runtime_resources"])
    if shared_runtime:
        reasons.append(f"shared_runtime:{', '.join(shared_runtime)}")

    shared_boundaries = sorted(set(left["exclusive_boundaries"]) & set(right["exclusive_boundaries"]))
    if shared_boundaries:
        reasons.append(f"shared_boundary:{', '.join(shared_boundaries)}")

    return reasons


def build_stages(tasks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    remaining = {task["id"]: task for task in tasks}
    completed: set[str] = set()
    stages: list[dict[str, Any]] = []
    conflict_index: dict[str, list[dict[str, Any]]] = {task["id"]: [] for task in tasks}

    for i, left in enumerate(tasks):
        for right in tasks[i + 1:]:
            reasons = conflict_reasons(left, right)
            if reasons:
                left_entry = {"task_id": right["id"], "reasons": reasons}
                right_entry = {"task_id": left["id"], "reasons": reasons}
                conflict_index[left["id"]].append(left_entry)
                conflict_index[right["id"]].append(right_entry)

    while remaining:
        ready = [
            task for task in tasks
            if task["id"] in remaining and all(dep in completed for dep in task["depends_on"])
        ]
        if not ready:
            unresolved = ", ".join(sorted(remaining))
            raise ValueError(f"cyclic or blocked dependencies among: {unresolved}")

        stage_tasks: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []

        for task in ready:
            reasons = [
                {
                    "task_id": active["id"],
                    "reasons": conflict_reasons(task, active),
                }
                for active in stage_tasks
                if conflict_reasons(task, active)
            ]
            if reasons:
                blocked.append({"task_id": task["id"], "blocked_by": reasons})
                continue
            stage_tasks.append(task)

        if not stage_tasks:
            stage_tasks = [ready[0]]
            blocked = [
                {
                    "task_id": task["id"],
                    "blocked_by": [{"task_id": ready[0]["id"], "reasons": conflict_reasons(task, ready[0])}],
                }
                for task in ready[1:]
            ]

        stages.append(
            {
                "index": len(stages) + 1,
                "mode": "parallel" if len(stage_tasks) > 1 else "serial",
                "tasks": [task["id"] for task in stage_tasks],
                "blocked_candidates": blocked,
            }
        )

        for task in stage_tasks:
            completed.add(task["id"])
            remaining.pop(task["id"], None)

    return stages, conflict_index


def build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    stages, conflict_index = build_stages(manifest["tasks"])
    tasks = []
    for task in manifest["tasks"]:
        tasks.append(
            {
                **task,
                "conflicts": conflict_index[task["id"]],
            }
        )
    return {
        "goal": manifest["goal"],
        "stages": stages,
        "tasks": tasks,
        "monitoring": [
            "Poll active lanes for new overlap in writes, generated outputs, and runtime resources.",
            "Collapse back to serial execution if a later prerequisite mutates an active lane's inputs.",
            "Run one merged verification pass after the final stage completes.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Parallelization Plan", ""]
    if report["goal"]:
        lines.extend(["## Goal", "", report["goal"], ""])

    lines.extend(["## Stages", ""])
    for stage in report["stages"]:
        lines.append(f"### Stage {stage['index']} ({stage['mode']})")
        lines.append("")
        for task_id in stage["tasks"]:
            task = next(item for item in report["tasks"] if item["id"] == task_id)
            lines.append(f"- `{task['id']}`: {task['summary']} [{task['suggested_skill']}]")
        if stage["blocked_candidates"]:
            lines.append("")
            lines.append("Blocked candidates:")
            for blocked in stage["blocked_candidates"]:
                reasons = []
                for blocker in blocked["blocked_by"]:
                    reasons.append(
                        f"{blocker['task_id']} ({'; '.join(blocker['reasons'])})"
                    )
                lines.append(f"- `{blocked['task_id']}` blocked by {', '.join(reasons)}")
        lines.append("")

    lines.extend(["## Task Details", ""])
    for task in report["tasks"]:
        lines.append(f"### `{task['id']}`")
        lines.append("")
        lines.append(f"- Summary: {task['summary']}")
        lines.append(f"- Suggested Skill: {task['suggested_skill']}")
        if task["depends_on"]:
            lines.append(f"- Depends On: {', '.join(task['depends_on'])}")
        if task["writes"]:
            lines.append(f"- Writes: {', '.join(task['writes'])}")
        if task["generated_outputs"]:
            lines.append(f"- Generated Outputs: {', '.join(task['generated_outputs'])}")
        if task["runtime_resources"]:
            lines.append(f"- Runtime Resources: {', '.join(task['runtime_resources'])}")
        if task["verify"]:
            lines.append(f"- Verify: {' | '.join(task['verify'])}")
        if task["done"]:
            lines.append(f"- Done: {task['done']}")
        if task["conflicts"]:
            rendered = ", ".join(
                f"{item['task_id']} ({'; '.join(item['reasons'])})"
                for item in task["conflicts"]
            )
            lines.append(f"- Conflicts: {rendered}")
        lines.append("")

    lines.extend(["## Monitoring", ""])
    for item in report["monitoring"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    manifest = load_manifest(Path(args.manifest))
    report = build_report(manifest)
    validate_payload("parallel-plan.schema.json", report)
    if args.format == "markdown":
        print(render_markdown(report))
        return 0
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
