#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_sync import SUBMODULE_PATHS


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync the root AGENTS.md into existing submodule AGENTS.md files."
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Only sync the listed module paths.",
    )
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="Create AGENTS.md in submodules that do not already have one.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing files. Exits non-zero if changes are needed.",
    )
    parser.add_argument(
        "--strict-missing",
        action="store_true",
        help="Fail if a selected module path does not exist in the checkout.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = repo_root()
    source = root / "AGENTS.md"
    if not source.exists():
        print(f"ERROR: missing canonical AGENTS.md: {source}", file=sys.stderr)
        return 2

    source_text = source.read_text(encoding="utf-8")
    selected = args.only if args.only else SUBMODULE_PATHS

    updated: list[str] = []
    created: list[str] = []
    unchanged: list[str] = []
    skipped: list[str] = []
    missing_modules: list[str] = []

    for rel in selected:
        module_dir = root / rel
        if not module_dir.exists():
            missing_modules.append(rel)
            continue

        target = module_dir / "AGENTS.md"
        if not target.exists() and not args.create_missing:
            skipped.append(rel)
            continue

        if target.exists():
            current_text = target.read_text(encoding="utf-8")
            if current_text == source_text:
                unchanged.append(rel)
                continue
            if args.check:
                updated.append(rel)
                continue
            target.write_text(source_text, encoding="utf-8")
            updated.append(rel)
            continue

        if args.check:
            created.append(rel)
            continue
        target.write_text(source_text, encoding="utf-8")
        created.append(rel)

    for rel in updated:
        print(f"UPDATE: {rel}/AGENTS.md")
    for rel in created:
        print(f"CREATE: {rel}/AGENTS.md")
    for rel in unchanged:
        print(f"OK: {rel}/AGENTS.md")
    for rel in skipped:
        print(f"SKIP: {rel} has no AGENTS.md")

    if missing_modules:
        for rel in missing_modules:
            print(f"MISSING MODULE: {rel}", file=sys.stderr)
        if args.strict_missing:
            return 3

    if args.check and (updated or created):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
