from __future__ import annotations

import re
from pathlib import Path


def bump_patch(v: str) -> str:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(.*)?", v.strip())
    if not m:
        raise ValueError(f"Invalid semver: {v}")
    major, minor, patch, suffix = m.group(1), m.group(2), m.group(3), m.group(4) or ""
    return f"{int(major)}.{int(minor)}.{int(patch) + 1}{suffix}"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return

    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
    if not m:
        raise RuntimeError("pyproject.toml missing version")

    old = m.group(1)
    new = bump_patch(old)
    pyproject.write_text(text[: m.start(1)] + new + text[m.end(1) :], encoding="utf-8")
    print(f"version-sync: {old} -> {new}")


if __name__ == "__main__":
    main()
