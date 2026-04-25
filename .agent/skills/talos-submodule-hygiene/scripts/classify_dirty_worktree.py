#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Iterable


GENERATED_MARKERS = (
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".cache/",
    ".next/",
    ".turbo/",
    ".parcel-cache/",
    "coverage/",
    "htmlcov/",
    "dist/",
    "build/",
    "target/",
    "out/",
    "tmp/",
    "temp/",
)

IGNORE_MARKERS = (
    ".DS_Store",
    ".idea/",
    ".vscode/",
    "*.log",
    "*.pid",
    "*.pyc",
    "*.pyo",
    "*.swp",
    "*.swo",
    "*.tmp",
    "*.bak",
)

IGNORE_EXACT = {
    ".coverage",
}

GENERATED_SUFFIXES = {
    ".class",
    ".log",
    ".pyc",
    ".pyo",
}

IGNORE_SUFFIXES = {
    ".swp",
    ".swo",
    ".tmp",
    ".bak",
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify dirty git worktree entries for cleanup and ignore planning."
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Git repository to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--submodules",
        action="store_true",
        help="Include initialized recursive submodules.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--ignored",
        choices=("matching", "none"),
        default="matching",
        help="Whether to ask git for ignored entries too.",
    )
    return parser.parse_args(argv)


def run_git(repo_path: Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(repo_path), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def list_repo_targets(root: Path, include_submodules: bool) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = [(".", root)]
    if not include_submodules:
        return targets

    try:
        raw = run_git(root, ["submodule", "status", "--recursive"])
    except RuntimeError:
        return targets

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        rel_path = parts[1]
        submodule_path = root / rel_path
        if submodule_path.exists():
            targets.append((rel_path, submodule_path))
    return targets


def normalize_path(text: str) -> str:
    raw = text.strip()
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return PurePosixPath(raw.replace("\\", "/")).as_posix()


def is_match(path: str, patterns: Iterable[str], suffixes: Iterable[str], exact: set[str] | None = None) -> bool:
    exact = exact or set()
    name = PurePosixPath(path).name
    lowered = path.lower()
    lowered_name = name.lower()

    if lowered_name in {item.lower() for item in exact}:
        return True

    for pattern in patterns:
        if pattern.startswith("*.") and lowered_name.endswith(pattern[1:].lower()):
            return True
        if pattern.endswith("/") and f"/{pattern.lower()}" in f"/{lowered}/":
            return True
        if lowered == pattern.lower() or lowered.endswith("/" + pattern.lower()):
            return True

    return any(lowered_name.endswith(suffix.lower()) for suffix in suffixes)


def classify_entry(code: str, path: str) -> tuple[str, str, str]:
    generated_like = is_match(path, GENERATED_MARKERS, GENERATED_SUFFIXES)
    ignore_like = is_match(path, IGNORE_MARKERS, IGNORE_SUFFIXES, IGNORE_EXACT)

    if code == "!!":
        return (
            "already_ignored",
            "none",
            "already ignored by git; only revisit if the ignore rule is too broad",
        )

    if code == "??":
        if ignore_like:
            return (
                "ignore_candidate",
                "consider_ignore",
                "untracked local/editor artifact that likely needs a scoped ignore rule",
            )
        if generated_like:
            return (
                "generated_artifact",
                "clean",
                "untracked generated output or cache that is usually safe to remove after confirming ownership",
            )
        return (
            "inspect_first",
            "inspect",
            "untracked path with unclear ownership; review before cleaning or ignoring",
        )

    if generated_like or ignore_like:
        return (
            "inspect_first",
            "inspect",
            "tracked change in an artifact-like path; verify whether it is committed by design",
        )

    return (
        "tracked_change",
        "keep",
        "tracked modification, rename, or deletion; assume intentional until proven generated",
    )


def parse_status_output(repo_label: str, raw: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        path = normalize_path(line[3:])
        bucket, action, reason = classify_entry(code, path)
        entries.append(
            {
                "repo": repo_label,
                "status": code,
                "path": path,
                "bucket": bucket,
                "action": action,
                "reason": reason,
            }
        )
    return entries


def collect_entries(root: Path, include_submodules: bool, include_ignored: bool) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    status_args = ["status", "--porcelain=v1"]
    if include_ignored:
        status_args.append("--ignored=matching")

    for label, repo_path in list_repo_targets(root, include_submodules):
        raw = run_git(repo_path, status_args)
        entries.extend(parse_status_output(label, raw))

    return entries


def render_markdown(entries: list[dict[str, str]]) -> str:
    if not entries:
        return "No dirty entries found."

    by_repo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        by_repo[entry["repo"]].append(entry)

    lines: list[str] = []
    overall = Counter(entry["bucket"] for entry in entries)
    lines.append("# Dirty Worktree Classification")
    lines.append("")
    lines.append("## Overall")
    for bucket, count in sorted(overall.items()):
        lines.append(f"- `{bucket}`: {count}")

    for repo, repo_entries in sorted(by_repo.items()):
        lines.append("")
        lines.append(f"## Repo `{repo}`")
        buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
        for entry in repo_entries:
            buckets[entry["bucket"]].append(entry)
        for bucket in (
            "tracked_change",
            "generated_artifact",
            "ignore_candidate",
            "inspect_first",
            "already_ignored",
        ):
            items = buckets.get(bucket)
            if not items:
                continue
            lines.append(f"- `{bucket}`")
            for item in items:
                lines.append(
                    f"  - `{item['status']}` `{item['path']}` -> `{item['action']}` ({item['reason']})"
                )

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.repo_path).resolve()
    include_ignored = args.ignored == "matching"

    try:
        entries = collect_entries(root, args.submodules, include_ignored)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = {
        "repo_path": str(root),
        "include_submodules": args.submodules,
        "include_ignored": include_ignored,
        "summary": dict(Counter(entry["bucket"] for entry in entries)),
        "entries": entries,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_markdown(entries))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
