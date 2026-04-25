#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SURFACE_PREFIXES = (
    "contracts/",
    "core/",
    "deploy/",
    "docs/",
    "examples/",
    "proto/",
    "services/",
    "site/",
    "sdks/",
    "src/",
    "tests/",
    "tools/",
)

COMMAND_PATTERNS = (
    re.compile(r"^(?:##\[group\])?Run (?P<command>.+)$"),
    re.compile(r"^\$\s+(?P<command>.+)$"),
    re.compile(r"^\+\s+(?P<command>.+)$"),
)

NOISE_PATTERNS = (
    re.compile(r"process completed with exit code", re.IGNORECASE),
    re.compile(r"error: process completed with exit code", re.IGNORECASE),
    re.compile(r"##\[error\]process completed with exit code", re.IGNORECASE),
)

CATEGORY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "contract_drift",
        (
            re.compile(r"contract drift", re.IGNORECASE),
            re.compile(r"schema mismatch", re.IGNORECASE),
            re.compile(r"vector mismatch", re.IGNORECASE),
            re.compile(r"generated .* out of date", re.IGNORECASE),
        ),
    ),
    (
        "infra",
        (
            re.compile(r"timed out", re.IGNORECASE),
            re.compile(r"connection refused", re.IGNORECASE),
            re.compile(r"service unavailable", re.IGNORECASE),
            re.compile(r"no space left on device", re.IGNORECASE),
            re.compile(r"out of memory", re.IGNORECASE),
            re.compile(r"oomkilled", re.IGNORECASE),
            re.compile(r"temporary failure", re.IGNORECASE),
            re.compile(r"network is unreachable", re.IGNORECASE),
        ),
    ),
    (
        "dependency",
        (
            re.compile(r"modulenotfounderror", re.IGNORECASE),
            re.compile(r"no module named", re.IGNORECASE),
            re.compile(r"cannot find module", re.IGNORECASE),
            re.compile(r"npm err!", re.IGNORECASE),
            re.compile(r"failed to resolve dependency", re.IGNORECASE),
            re.compile(r"could not find a version that satisfies", re.IGNORECASE),
        ),
    ),
    (
        "lint",
        (
            re.compile(r"\bruff\b", re.IGNORECASE),
            re.compile(r"\bflake8\b", re.IGNORECASE),
            re.compile(r"\beslint\b", re.IGNORECASE),
            re.compile(r"\bprettier\b", re.IGNORECASE),
            re.compile(r"\bblack\b", re.IGNORECASE),
            re.compile(r"\blint\b", re.IGNORECASE),
        ),
    ),
    (
        "typecheck",
        (
            re.compile(r"\bmypy\b", re.IGNORECASE),
            re.compile(r"\btsc\b", re.IGNORECASE),
            re.compile(r"\btypecheck\b", re.IGNORECASE),
            re.compile(r"typing error", re.IGNORECASE),
        ),
    ),
    (
        "test",
        (
            re.compile(r"^FAILED\s", re.IGNORECASE),
            re.compile(r"\bFAILURES\b", re.IGNORECASE),
            re.compile(r"assertionerror", re.IGNORECASE),
            re.compile(r"\btraceback\b", re.IGNORECASE),
            re.compile(r"panic:", re.IGNORECASE),
            re.compile(r"^--- FAIL:", re.IGNORECASE),
            re.compile(r"test suites?:\s*\d+\s+failed", re.IGNORECASE),
        ),
    ),
    (
        "build",
        (
            re.compile(r"build failed", re.IGNORECASE),
            re.compile(r"failed to compile", re.IGNORECASE),
            re.compile(r"compilation failed", re.IGNORECASE),
            re.compile(r"^\s*error:", re.IGNORECASE),
        ),
    ),
)

PATH_PATTERN = re.compile(
    r"(?P<path>(?:contracts|core|deploy|docs|examples|proto|services|site|sdks|src|tests|tools)/[A-Za-z0-9._/\-]+)"
)


@dataclass
class FailureSignal:
    category: str
    line_number: int
    line: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the first actionable signal from Talos CI logs."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Log files to inspect. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=2,
        help="Context lines to include before and after the first signal.",
    )
    return parser.parse_args(argv)


def read_lines(paths: list[str]) -> list[str]:
    if not paths:
        return sys.stdin.read().splitlines()

    lines: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        lines.extend(path.read_text().splitlines())
    return lines


def is_noise(line: str) -> bool:
    return any(pattern.search(line) for pattern in NOISE_PATTERNS)


def classify_line(line: str) -> str | None:
    if is_noise(line):
        return None

    for category, patterns in CATEGORY_PATTERNS:
        if any(pattern.search(line) for pattern in patterns):
            return category

    return None


def find_signal(lines: list[str]) -> FailureSignal | None:
    for index, line in enumerate(lines, start=1):
        category = classify_line(line)
        if category:
            return FailureSignal(category=category, line_number=index, line=line.strip())
    return None


def find_command(lines: list[str], signal_line: int | None) -> str | None:
    if signal_line is None:
        search_window: Iterable[tuple[int, str]] = enumerate(lines, start=1)
    else:
        start = max(0, signal_line - 25)
        search_window = enumerate(lines[start:signal_line], start=start + 1)

    last_command: str | None = None
    for _, line in search_window:
        stripped = line.strip()
        for pattern in COMMAND_PATTERNS:
            match = pattern.match(stripped)
            if match:
                last_command = match.group("command").strip()
                break
        else:
            if re.match(r"^(make|npm|pnpm|yarn|pytest|python3|bash|go test|cargo test|mvn|gradle)\b", stripped):
                last_command = stripped

    return last_command


def is_command_line(line: str) -> bool:
    stripped = line.strip()
    if any(pattern.match(stripped) for pattern in COMMAND_PATTERNS):
        return True
    return bool(
        re.match(
            r"^(make|npm|pnpm|yarn|pytest|python3|bash|go test|cargo test|mvn|gradle)\b",
            stripped,
        )
    )


def find_surface(lines: list[str], signal_line: int | None) -> str | None:
    ordered_lines: list[str] = []
    if signal_line is not None:
        start = max(0, signal_line - 5)
        end = min(len(lines), signal_line + 5)
        window = lines[start:end]
        if 0 <= signal_line - 1 - start < len(window):
            ordered_lines.extend(window[signal_line - 1 - start :])
            ordered_lines.extend(window[: signal_line - 1 - start])
        else:
            ordered_lines.extend(window)
    ordered_lines.extend(lines)

    for prefer_commands in (False, True):
        for line in ordered_lines:
            if is_command_line(line) != prefer_commands:
                continue
            match = PATH_PATTERN.search(line)
            if match:
                path = match.group("path")
                for prefix in SURFACE_PREFIXES:
                    if path.startswith(prefix):
                        return prefix.rstrip("/")
    return None


def context_lines(lines: list[str], signal_line: int | None, count: int) -> list[dict[str, object]]:
    if signal_line is None:
        return []

    start = max(1, signal_line - count)
    end = min(len(lines), signal_line + count)
    return [
        {"line_number": index, "line": lines[index - 1]}
        for index in range(start, end + 1)
    ]


def suggest_repro(category: str | None, surface: str | None, command: str | None) -> str:
    if command:
        return command

    if category == "contract_drift":
        return "python3 scripts/python/check_contract_drift.py"
    if surface == "site":
        if category == "lint":
            return "npm run lint"
        if category == "typecheck":
            return "npm run typecheck"
        if category == "test":
            return "npm run test"
        return "npm run build"
    if category in {"lint", "typecheck", "build"}:
        return "make build"
    if category == "test":
        return "bash deploy/scripts/run_all_tests.sh --ci --changed"
    if category == "infra":
        return "bash deploy/scripts/run_all_tests.sh --ci --changed"
    return "make test"


def build_summary(lines: list[str], context_count: int) -> dict[str, object]:
    signal = find_signal(lines)
    signal_line = signal.line_number if signal else None
    command = find_command(lines, signal_line)
    surface = find_surface(lines, signal_line)
    category = signal.category if signal else None

    return {
        "category": category or "unknown",
        "first_signal": asdict(signal) if signal else None,
        "owning_surface": surface or "unknown",
        "likely_command": command or "unknown",
        "suggested_repro": suggest_repro(category, surface, command),
        "context": context_lines(lines, signal_line, context_count),
    }


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        f"Category: {summary['category']}",
        f"Owning surface: {summary['owning_surface']}",
        f"Likely command: {summary['likely_command']}",
        f"Suggested repro: {summary['suggested_repro']}",
    ]

    first_signal = summary["first_signal"]
    if isinstance(first_signal, dict):
        lines.append(
            "First signal: "
            f"line {first_signal['line_number']} - {first_signal['line']}"
        )
    else:
        lines.append("First signal: not found")

    context = summary["context"]
    if isinstance(context, list) and context:
        lines.append("Context:")
        for item in context:
            lines.append(f"- {item['line_number']}: {item['line']}")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    lines = read_lines(args.paths)
    summary = build_summary(lines, args.context)

    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(render_markdown(summary))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
