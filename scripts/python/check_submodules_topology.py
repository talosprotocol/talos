#!/usr/bin/env python3
from __future__ import annotations

import configparser
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "deploy" / "submodules.json"
GITMODULES = ROOT / ".gitmodules"
LEGACY = ROOT / "deploy" / "repos"

ALLOWED_LEGACY_FILES = {"README.md", ".gitkeep"}


def die(msg: str) -> None:
    raise SystemExit(msg)


def load_manifest() -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        die(f"Missing {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        die("deploy/submodules.json must be a JSON array")
    return data


def load_gitmodules_paths() -> dict[str, str]:
    if not GITMODULES.exists():
        die("Missing .gitmodules")
    cp = configparser.ConfigParser()
    cp.read(GITMODULES)
    out: dict[str, str] = {}
    for section in cp.sections():
        if not section.startswith('submodule "'):
            continue
        name = section[len('submodule "') : -1]
        path = cp.get(section, "path", fallback=None)
        if not path:
            die(f".gitmodules submodule {name} missing path")
        out[name] = path
    return out


def main() -> int:
    manifest = load_manifest()
    by_name = {e["name"]: e for e in manifest}

    gm = load_gitmodules_paths()

    # 1) Name parity
    missing_in_gm = sorted(set(by_name.keys()) - set(gm.keys()))
    missing_in_manifest = sorted(set(gm.keys()) - set(by_name.keys()))
    if missing_in_gm:
        die(f"Manifest entries missing in .gitmodules: {missing_in_gm}")
    if missing_in_manifest:
        die(f".gitmodules entries missing in manifest: {missing_in_manifest}")

    # 2) Path parity and no deploy/repos gitlinks
    for name, entry in by_name.items():
        expected = entry["new_path"]
        actual = gm.get(name)
        if actual != expected:
            die(f"Path mismatch for {name}: .gitmodules={actual} manifest={expected}")
        if actual.startswith(""):
            die(f"Submodule {name} still under deploy/repos: {actual}")

    # 3) Legacy stub-only
    if LEGACY.exists():
        for p in LEGACY.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(LEGACY)
            if rel.parts and rel.parts[0].startswith("."):
                continue
            if p.name not in ALLOWED_LEGACY_FILES:
                die(f"Legacy path contains non-stub file: {p}")

    print("OK: manifest parity + legacy stubs enforcement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
