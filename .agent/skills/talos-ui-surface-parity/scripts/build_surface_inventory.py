#!/usr/bin/env python3
"""Emit a lightweight Talos UI surface inventory for parity reviews."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def repo_root_from(script_path: Path) -> Path:
    return script_path.resolve().parents[4]


def normalize_app_route(page_path: Path, shell_root: Path) -> str:
    rel_parent = page_path.relative_to(shell_root).parent
    if str(rel_parent) == ".":
        return "/"
    parts = [part for part in rel_parent.parts if not (part.startswith("(") and part.endswith(")"))]
    return "/" + "/".join(parts)


def collect_dashboard_routes(repo_root: Path) -> list[dict[str, str]]:
    shell_root = repo_root / "site/dashboard/src/app/(shell)"
    routes: list[dict[str, str]] = []
    if not shell_root.exists():
        return routes

    for page in sorted(shell_root.glob("**/page.tsx")):
        routes.append(
            {
                "route": normalize_app_route(page, shell_root),
                "file": str(page.relative_to(repo_root)),
            }
        )
    return routes


def collect_workbench_routes(repo_root: Path) -> list[dict[str, object]]:
    workbench = repo_root / "site/dashboard/src/lib/api/workbench.ts"
    if not workbench.exists():
        return []

    content = workbench.read_text(encoding="utf-8")
    pattern = re.compile(
        r"""\{
    \s*id:\s*"(?P<id>[^"]+)",
    \s*path:\s*"(?P<path>[^"]+)",
    \s*title:\s*"(?P<title>[^"]+)",
    \s*description:\s*"(?P<description>[^"]+)",
    \s*group:\s*"(?P<group>[^"]+)",
    \s*methods:\s*\[(?P<methods>[^\]]+)\]""",
        re.MULTILINE | re.DOTALL,
    )

    routes: list[dict[str, object]] = []
    for match in pattern.finditer(content):
        routes.append(
            {
                "id": match.group("id"),
                "path": match.group("path"),
                "title": match.group("title"),
                "group": match.group("group"),
                "methods": re.findall(r'"([^"]+)"', match.group("methods")),
            }
        )
    return routes


def collect_tui_inventory(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    app_path = repo_root / "tools/talos-tui/python/src/talos_tui/app.py"
    inventory = {"bindings": [], "screens": []}
    if not app_path.exists():
        return inventory

    content = app_path.read_text(encoding="utf-8")
    binding_pattern = re.compile(
        r'Binding\("(?P<key>[^"]+)",\s*"(?P<action>[^"]+)",\s*"(?P<label>[^"]+)"\)'
    )
    screen_pattern = re.compile(r'install_screen\([^,]+,\s*name="(?P<name>[^"]+)"\)')

    inventory["bindings"] = [match.groupdict() for match in binding_pattern.finditer(content)]
    inventory["screens"] = [{"name": match.group("name")} for match in screen_pattern.finditer(content)]
    return inventory


def build_inventory(repo_root: Path) -> dict[str, object]:
    return {
        "repo_root": str(repo_root),
        "dashboard_shell_routes": collect_dashboard_routes(repo_root),
        "api_workbench_routes": collect_workbench_routes(repo_root),
        "tui": collect_tui_inventory(repo_root),
    }


def render_markdown(inventory: dict[str, object]) -> str:
    dashboard_routes = inventory["dashboard_shell_routes"]
    workbench_routes = inventory["api_workbench_routes"]
    tui = inventory["tui"]
    lines = [
        "# Talos UI surface inventory",
        "",
        f"- Dashboard shell pages: {len(dashboard_routes)}",
        f"- API Workbench routes: {len(workbench_routes)}",
        f"- TUI bindings: {len(tui['bindings'])}",
        f"- TUI screens: {len(tui['screens'])}",
        "",
        "## Dashboard shell pages",
    ]

    for route in dashboard_routes:
        lines.append(f"- `{route['route']}` -> `{route['file']}`")

    lines.extend(["", "## API Workbench catalog"])
    for route in workbench_routes:
        methods = "/".join(route["methods"])
        lines.append(
            f"- `[{route['group']}] {route['title']}` `{methods} {route['path']}` id=`{route['id']}`"
        )

    lines.extend(["", "## TUI bindings"])
    for binding in tui["bindings"]:
        lines.append(f"- `{binding['key']}` `{binding['label']}` -> `{binding['action']}`")

    lines.extend(["", "## TUI screens"])
    for screen in tui["screens"]:
        lines.append(f"- `{screen['name']}`")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a lightweight dashboard/workbench/TUI inventory for parity reviews."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root_from(Path(__file__)),
        help="Talos repository root. Defaults to the parent repo of this script.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory = build_inventory(args.repo_root.resolve())
    if args.format == "json":
        json.dump(inventory, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(render_markdown(inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
