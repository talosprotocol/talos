#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MANIFEST = Path(__file__).with_name("submodules.json")


def _load() -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Manifest must be a JSON array")
    for i, e in enumerate(data):
        if not isinstance(e, dict):
            raise SystemExit(f"Manifest entry {i} must be an object")
        for k in ("name", "repo_url", "branch", "old_path", "new_path", "category", "required"):
            if k not in e:
                raise SystemExit(f"Manifest entry {i} missing required key: {k}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", required=True, choices=["name", "repo_url", "branch", "old_path", "new_path", "category"])
    ap.add_argument("--required-only", action="store_true")
    ap.add_argument("--name", help="Filter by specific submodule name")
    args = ap.parse_args()

    entries = _load()
    if args.name:
        entries = [e for e in entries if e["name"] == args.name]
        if not entries:
            # Silent exit or error? For scripting, empty output is safer unless strict.
            return 1
    elif args.required_only:
        entries = [e for e in entries if bool(e.get("required"))]

    for e in entries:
        v = e.get(args.field)
        if v is None:
            continue
        print(str(v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
