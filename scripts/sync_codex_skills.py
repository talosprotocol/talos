#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def discover_skills(source_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in source_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)


def trees_equal(left: Path, right: Path) -> bool:
    if not right.exists() or not right.is_dir() or right.is_symlink():
        return False

    left_entries = sorted(
        entry.name for entry in left.iterdir() if entry.name != ".DS_Store"
    )
    right_entries = sorted(
        entry.name for entry in right.iterdir() if entry.name != ".DS_Store"
    )
    if left_entries != right_entries:
        return False

    for name in left_entries:
        left_path = left / name
        right_path = right / name
        if left_path.is_dir():
            if not trees_equal(left_path, right_path):
                return False
            continue
        if right_path.is_dir():
            return False
        if left_path.read_bytes() != right_path.read_bytes():
            return False

    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mirror repo-local Codex skills into a Codex skills directory."
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Source skills directory. Defaults to <repo>/.agent/skills.",
    )
    parser.add_argument(
        "--target",
        default=str(Path.home() / ".codex" / "skills"),
        help="Target Codex skills directory. Defaults to ~/.codex/skills.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Only sync the listed skill folder names.",
    )
    parser.add_argument(
        "--mode",
        choices=["copy", "symlink"],
        default="copy",
        help="Mirror mode. 'copy' is the default; 'symlink' keeps global skills live.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing files. Exits non-zero if changes are needed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = repo_root()
    source_dir = (
        Path(args.source).expanduser().resolve()
        if args.source
        else root / ".agent" / "skills"
    )
    if not source_dir.exists():
        print(f"ERROR: source skills directory not found: {source_dir}", file=sys.stderr)
        return 2

    discovered = {path.name: path for path in discover_skills(source_dir)}
    selected_names = args.only if args.only else sorted(discovered)

    missing_sources = [name for name in selected_names if name not in discovered]
    if missing_sources:
        for name in missing_sources:
            print(f"ERROR: unknown skill: {name}", file=sys.stderr)
        return 2

    target_dir = Path(args.target).expanduser()
    if not args.check:
        target_dir.mkdir(parents=True, exist_ok=True)

    changed = False
    for name in selected_names:
        source = discovered[name]
        target = target_dir / name

        if args.mode == "symlink":
            desired = source.resolve()
            if target.is_symlink() and target.resolve() == desired:
                print(f"OK: {name}")
                continue
            changed = True
            if args.check:
                print(f"UPDATE: {target} -> {desired}")
                continue
            if target.exists() or target.is_symlink():
                remove_path(target)
            target.symlink_to(desired, target_is_directory=True)
            print(f"LINK: {name}")
            continue

        if trees_equal(source, target):
            print(f"OK: {name}")
            continue

        changed = True
        if args.check:
            print(f"UPDATE: {target}")
            continue

        if target.exists() or target.is_symlink():
            remove_path(target)
        shutil.copytree(source, target, symlinks=True)
        print(f"COPY: {name}")

    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
