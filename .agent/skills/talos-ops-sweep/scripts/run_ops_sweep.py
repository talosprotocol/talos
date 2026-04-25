#!/usr/bin/env python3
"""Run the Talos ops sweep by composing local automation helpers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def repo_root_from(script_path: Path) -> Path:
    return script_path.resolve().parents[4]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Talos CI triage, UI surface parity, and submodule hygiene in one pass."
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=repo_root_from(Path(__file__)),
        help="Talos repository root. Defaults to this script's parent repo.",
    )
    parser.add_argument(
        "--ci-log",
        type=Path,
        default=None,
        help="Optional CI or local failure log to triage.",
    )
    parser.add_argument(
        "--submodules",
        action="store_true",
        help="Include recursive submodules in the hygiene pass.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args()


def run_helper(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "helper command failed")
    return result.stdout.strip()


def build_commands(repo_root: Path, repo_path: Path, ci_log: Path | None, submodules: bool) -> dict[str, list[str] | None]:
    commands: dict[str, list[str] | None] = {
        "hygiene": [
            "python3",
            str(repo_root / ".agent/skills/talos-submodule-hygiene/scripts/classify_dirty_worktree.py"),
            "--repo-path",
            str(repo_path),
            "--format",
            "markdown",
        ],
        "ui_surface_parity": [
            "python3",
            str(repo_root / ".agent/skills/talos-ui-surface-parity/scripts/build_surface_inventory.py"),
            "--repo-root",
            str(repo_root),
            "--format",
            "markdown",
        ],
        "ci_triage": None,
    }
    if submodules:
        assert commands["hygiene"] is not None
        commands["hygiene"].append("--submodules")
    if ci_log:
        commands["ci_triage"] = [
            "python3",
            str(repo_root / ".agent/skills/talos-ci-triage/scripts/triage_ci_failure.py"),
            str(ci_log),
            "--format",
            "markdown",
        ]
    return commands


def run_ops_sweep(repo_root: Path, repo_path: Path, ci_log: Path | None, submodules: bool) -> dict[str, object]:
    commands = build_commands(repo_root, repo_path, ci_log, submodules)
    results: dict[str, object] = {
        "repo_root": str(repo_root),
        "repo_path": str(repo_path),
        "ci_log": str(ci_log) if ci_log else None,
        "reports": {},
    }
    for section, command in commands.items():
        if command is None:
            results["reports"][section] = {"status": "skipped", "reason": "no ci log supplied"}
            continue
        results["reports"][section] = {
            "status": "ok",
            "command": command,
            "output": run_helper(command),
        }
    return results


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Talos Ops Sweep",
        "",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo path: `{report['repo_path']}`",
        f"- CI log: `{report['ci_log'] or 'not supplied'}`",
    ]
    reports = report["reports"]
    assert isinstance(reports, dict)
    for section in ("hygiene", "ci_triage", "ui_surface_parity"):
        section_report = reports[section]
        assert isinstance(section_report, dict)
        lines.extend(["", f"## {section.replace('_', ' ').title()}"])
        if section_report["status"] != "ok":
            lines.append(f"- {section_report['reason']}")
            continue
        output = str(section_report["output"]).strip()
        lines.append(output if output else "- No output")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    repo_root = repo_root_from(Path(__file__)).resolve()
    report = run_ops_sweep(
        repo_root=repo_root,
        repo_path=args.repo_path.resolve(),
        ci_log=args.ci_log.resolve() if args.ci_log else None,
        submodules=args.submodules,
    )
    if args.format == "json":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
