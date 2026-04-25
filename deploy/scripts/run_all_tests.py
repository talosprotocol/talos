#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
SUBMODULES_PATH = ROOT_DIR / "deploy" / "submodules.json"


@dataclass
class Target:
    name: str
    path: Path
    category: str
    required: bool
    raw: dict[str, Any]


@dataclass
class RunnerPlan:
    target: Target
    source: str
    commands: list[list[str]]
    env: dict[str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Talos component tests using the nearest owned test entrypoint. "
            "Manifest-backed repos use .agent/test_manifest.yml when available; "
            "other repos fall back to scripts/test.sh, Makefile targets, or framework defaults."
        )
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run the required component set using manifest CI defaults when available.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the broader/full test mode for selected components when their entrypoints support it.",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Restrict execution to components with local git changes.",
    )
    parser.add_argument(
        "--required-only",
        action="store_true",
        help="Restrict execution to required components from deploy/submodules.json.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="TARGET",
        help=(
            "Restrict execution to a repo name, repo path, basename, or category selector. "
            "May be repeated. Example: --only talos-contracts --only category:sdk"
        ),
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Set TALOS_SKIP_BUILD=true for downstream test entrypoints that honor it.",
    )
    parser.add_argument(
        "--with-live",
        action="store_true",
        help="Alias for a wider integration-oriented run. Sets TALOS_WITH_LIVE=true and implies --full.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Request smoke mode for manifest-backed or standardized script entrypoints.",
    )
    return parser.parse_args()


def load_submodules() -> list[Target]:
    data = json.loads(SUBMODULES_PATH.read_text(encoding="utf-8"))
    targets: list[Target] = []
    for entry in data:
        targets.append(
            Target(
                name=str(entry["name"]),
                path=ROOT_DIR / str(entry["new_path"]),
                category=str(entry["category"]),
                required=bool(entry["required"]),
                raw=entry,
            )
        )
    return targets


def changed_paths() -> set[str]:
    commands = [
        ["git", "diff", "--name-only", "--relative", "HEAD"],
        ["git", "diff", "--name-only", "--relative", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    changed: set[str] = set()
    for command in commands:
        try:
            proc = subprocess.run(
                command,
                cwd=ROOT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            continue
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line:
                changed.add(line)
    return changed


def matches_only(target: Target, selector: str) -> bool:
    if selector.startswith("category:"):
        return target.category == selector.split(":", 1)[1]
    path_str = target.raw["new_path"]
    old_path = target.raw["old_path"]
    basename = Path(path_str).name
    return selector in {target.name, path_str, old_path, basename}


def is_changed_target(target: Target, paths: set[str]) -> bool:
    prefix = f"{target.raw['new_path'].rstrip('/')}/"
    exact = target.raw["new_path"].rstrip("/")
    return any(path == exact or path.startswith(prefix) for path in paths)


def determine_mode(args: argparse.Namespace) -> str:
    if args.with_live or args.full:
        return "full"
    if args.ci:
        return "ci"
    if args.smoke:
        return "smoke"
    return "unit"


def select_targets(args: argparse.Namespace) -> list[Target]:
    targets = load_submodules()
    if args.only:
        targets = [
            target
            for target in targets
            if any(matches_only(target, selector) for selector in args.only)
        ]
    if args.required_only or (args.ci and not args.only):
        targets = [target for target in targets if target.required]
    if args.changed:
        paths = changed_paths()
        targets = [target for target in targets if is_changed_target(target, paths)]
    return [target for target in targets if target.path.exists()]


def supports_standardized_flags(script_path: Path) -> bool:
    try:
        text = script_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return all(flag in text for flag in ("--unit", "--ci", "--full"))


def manifest_plan(target: Target, mode: str, env: dict[str, str]) -> RunnerPlan | None:
    manifest_path = target.path / ".agent" / "test_manifest.yml"
    if not manifest_path.exists():
        return None
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"Failed to parse {manifest_path}: {exc}") from exc
    entrypoint = manifest.get("commands", {}).get("test_entrypoint")
    if not isinstance(entrypoint, str) or not entrypoint:
        return None
    args: list[str]
    if mode == "ci":
        ci_args = manifest.get("ci", {}).get("default")
        if isinstance(ci_args, list) and ci_args:
            args = [str(item) for item in ci_args]
        else:
            args = ["--ci"]
    elif mode == "full":
        args = ["--full"]
    elif mode == "smoke":
        args = ["--smoke"]
    else:
        args = ["--unit"]
    commands = [["bash", entrypoint, arg] for arg in args]
    return RunnerPlan(
        target=target,
        source=".agent/test_manifest.yml",
        commands=commands,
        env=env,
    )


def fallback_plan(target: Target, mode: str, env: dict[str, str]) -> RunnerPlan | None:
    script_path = target.path / "scripts" / "test.sh"
    if script_path.exists():
        command = ["bash", "scripts/test.sh"]
        if supports_standardized_flags(script_path):
            flag = {
                "ci": "--ci",
                "full": "--full",
                "smoke": "--smoke",
                "unit": "--unit",
            }[mode]
            command.append(flag)
        return RunnerPlan(target=target, source="scripts/test.sh", commands=[command], env=env)

    if (target.path / "Makefile").exists():
        return RunnerPlan(
            target=target,
            source="Makefile",
            commands=[["make", "test"]],
            env=env,
        )

    if (target.path / "package.json").exists():
        return RunnerPlan(
            target=target,
            source="package.json#scripts.test",
            commands=[["npm", "test", "--silent"]],
            env=env,
        )

    if (target.path / "pyproject.toml").exists():
        return RunnerPlan(
            target=target,
            source="pyproject.toml",
            commands=[["pytest", "-q"]],
            env=env,
        )

    return None


def build_plan(target: Target, mode: str, args: argparse.Namespace) -> RunnerPlan | None:
    import shutil
    env = os.environ.copy()
    env.setdefault("TALOS_RUN_ID", "local")
    if args.skip_build:
        env["TALOS_SKIP_BUILD"] = "true"
    if args.with_live:
        env["TALOS_WITH_LIVE"] = "true"

    if target.name == "talos-core-rs":
        env["DYLD_FALLBACK_LIBRARY_PATH"] = "/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9"

    plan = manifest_plan(target, mode, env) or fallback_plan(target, mode, env)
    
    # Universal Docker Wrapping
    if plan and plan.commands:
        # Node fallback
        if not shutil.which("npm") and (
            any(command[0] == "npm" for command in plan.commands)
            or (target.category in ["dashboard", "site"])
        ):
            plan.commands = [["bash", str(ROOT_DIR / "scripts" / "test_ui.sh")]]
        
        # Python fallback (if host python is too old)
        elif target.category in ["service", "sdk", "contracts", "core"] or (target.path / "pyproject.toml").exists():
            # If it's a python project and we are on host 3.9, wrap it
            import sys
            if sys.version_info < (3, 10):
                plan.commands = [
                    ["bash", str(ROOT_DIR / "scripts" / "test_py.sh"), *command]
                    for command in plan.commands
                ]

    return plan


def run_plan(plan: RunnerPlan) -> int:
    rel_path = plan.target.raw["new_path"]
    rendered_command = " && ".join(
        " ".join(shlex.quote(part) for part in command)
        for command in plan.commands
    )
    print(f"[tests] {plan.target.name} ({rel_path}, {plan.source})")
    print(f"[tests] -> {rendered_command}")
    for command in plan.commands:
        proc = subprocess.run(command, cwd=plan.target.path, env=plan.env)
        if proc.returncode != 0:
            return proc.returncode
    return 0


def main() -> int:
    args = parse_args()
    mode = determine_mode(args)
    targets = select_targets(args)

    if not targets:
        print("[tests] No matching components selected.")
        return 0

    failures: list[str] = []
    skipped: list[str] = []
    for target in targets:
        plan = build_plan(target, mode, args)
        if plan is None:
            skipped.append(target.name)
            print(
                f"[tests] Skipping {target.name} ({target.raw['new_path']}): "
                "no owned test entrypoint found"
            )
            continue
        if run_plan(plan) != 0:
            failures.append(target.name)

    if skipped:
        print(f"[tests] Skipped {len(skipped)} component(s): {', '.join(skipped)}")
    if failures:
        print(f"[tests] Failed {len(failures)} component(s): {', '.join(failures)}")
        return 1

    print(f"[tests] Completed {len(targets) - len(skipped)} component(s) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
