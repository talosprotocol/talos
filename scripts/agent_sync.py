#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable, TypedDict


class ModuleContext(TypedDict):
    current_state: str
    expected_state: str
    behavior: str


SUBMODULE_PATHS = [
    "contracts",
    "core",
    "sdks/python",
    "sdks/typescript",
    "services/ai-gateway",
    "services/audit",
    "services/mcp-connector",
    "site/dashboard",
    "examples",
    "docs",
    "sdks/go",
    "sdks/java",
    "site/marketing",
    "services/gateway",
    "services/ai-chat-agent",
    "services/aiops",
    "services/governance-agent",
    "services/ucp-connector",
    "sdks/rust",
    "tools/talos-tui",
    "site/configuration-dashboard",
]

SUBMODULE_CONTEXT: dict[str, ModuleContext] = {
    "contracts": {
        "current_state": (
            "Source of truth for schemas and contract-first invariants. Capability auth, RBAC, TGA, and A2A phase specs are active. "
            "Schemas, OpenAPI, and test vectors are treated as normative integration boundaries."
        ),
        "expected_state": (
            "Strict backward compatibility and versioned evolution. All new protocol or API features start here first. "
            "Consumers must not reimplement contract logic."
        ),
        "behavior": (
            "Defines JSON Schemas, OpenAPI specs, error codes, and cross-language test vectors. "
            "Publishes artifacts that all SDKs and services must comply with."
        ),
    },
    "core": {
        "current_state": (
            "Protocol kernel and shared primitives. Canonical encoding and security invariants are defined here or delegated to contracts artifacts. "
            "Focus is on correctness, determinism, and minimal coupling."
        ),
        "expected_state": (
            "Stable kernel with strict interfaces and replaceable adapters. Performance-sensitive work is isolated and well tested."
        ),
        "behavior": (
            "Provides core protocol utilities and abstractions used by services and SDKs, without deep-linking across repos. "
            "Acts as a coordination point for kernel-level behavior."
        ),
    },
    "sdks/python": {
        "current_state": (
            "Python client SDK with typed models and security primitives in place. TGA compliance is expected in client flows. "
            "Focus on correctness and predictable behavior across environments."
        ),
        "expected_state": (
            "Feature parity with other SDKs and strong typing discipline. Strict tests against published test vectors."
        ),
        "behavior": (
            "Client library for interacting with Talos services. Implements request shaping, auth handshakes, and contract-aligned models."
        ),
    },
    "sdks/typescript": {
        "current_state": (
            "TypeScript SDK used by dashboards and web-based tooling. Must track contracts closely and avoid local reimplementation of invariants."
        ),
        "expected_state": (
            "Parity with other SDKs, stable public API, and contract-driven codegen or strict typing where applicable."
        ),
        "behavior": (
            "Client library for browser and Node consumers. Provides typed bindings to service APIs and contract artifacts."
        ),
    },
    "sdks/go": {
        "current_state": (
            "Go SDK is present or under active development. Contract compliance is the primary correctness requirement."
        ),
        "expected_state": (
            "Parity with Python and TypeScript. Uses test vectors as hard gates for crypto, encoding, and API behavior."
        ),
        "behavior": (
            "Go client library for Talos services. Exposes stable types and helpers aligned with published contracts."
        ),
    },
    "sdks/java": {
        "current_state": (
            "Java SDK is present or under active development. Focus is on enterprise-friendly usage and strict contract alignment."
        ),
        "expected_state": (
            "Parity across SDKs, strong typing, and compliance tests driven by published vectors."
        ),
        "behavior": (
            "Java client library for Talos services. Provides typed APIs, error handling, and integration helpers."
        ),
    },
    "sdks/rust": {
        "current_state": (
            "Rust SDK is present or staged. Rust is also a candidate for a narrow performance wedge once DI boundaries are stable."
        ),
        "expected_state": (
            "Clear separation between kernel-grade primitives and SDK ergonomics. Vector-driven compliance is mandatory."
        ),
        "behavior": (
            "Rust client SDK and potential home for performance-critical primitives, depending on architecture decisions."
        ),
    },
    "services/gateway": {
        "current_state": (
            "Edge entry point. Multi-region read and write split is active or in progress, with rate limiting and request validation expected. "
            "A2A and capability enforcement paths are implemented in the gateway layer."
        ),
        "expected_state": (
            "High availability with minimal overhead and strict fail-closed security. All inputs validated against contracts before dispatch."
        ),
        "behavior": (
            "Routes and mediates requests to internal services and tool servers. Enforces authN, authZ, auditing hooks, and safety limits."
        ),
    },
    "services/ai-gateway": {
        "current_state": (
            "AI Gateway that routes agent and tool traffic with strict read and write separation, budgeting, and contract-first enforcement. "
            "Multi-region behavior and read replica fallback patterns are part of the active roadmap."
        ),
        "expected_state": (
            "Operationally safe by default, with strong policy enforcement and observability. "
            "All tool dispatch and agent flows validated and audited."
        ),
        "behavior": (
            "Provides agent-facing APIs and tool routing. Applies budgets, allowlists, and security invariants before invoking downstream tools."
        ),
    },
    "services/audit": {
        "current_state": (
            "Audit service produces verifiable event streams and integrity signals. SSE endpoints and meta-first semantics are expected where used."
        ),
        "expected_state": (
            "Strong integrity guarantees with clear failure modes and robust backfill and cursor handling where applicable."
        ),
        "behavior": (
            "Stores and serves audit events, proofs, and integrity state. Exposes event streaming and query APIs for dashboards and services."
        ),
    },
    "services/mcp-connector": {
        "current_state": (
            "MCP connector wraps tool interactions with policy enforcement. Read and write tool separation and tool registry policies are active."
        ),
        "expected_state": (
            "Strict least privilege and deterministic auditing. Robust error handling and compatibility with multiple tool servers."
        ),
        "behavior": (
            "Acts as a policy and transport adapter for MCP tools. Enforces registry constraints, idempotency, and audit-friendly hashing."
        ),
    },
    "services/governance-agent": {
        "current_state": (
            "Talos owner agent that governs policy and operational invariants. Domain logic has been migrated into a standalone Python project."
        ),
        "expected_state": (
            "Production-grade policy enforcement with strong tests, pinned dependencies, and CI gates. Fail-closed on misconfiguration."
        ),
        "behavior": (
            "Evaluates and enforces governance decisions, manages session and state stores, and provides owner-level controls and automation."
        ),
    },
    "services/ucp-connector": {
        "current_state": (
            "UCP checkout lifecycle implementation with strict signing rules and locked security invariants. Reference merchant behavior exists or is staged."
        ),
        "expected_state": (
            "Spec-complete lifecycle coverage, robust idempotency, and strong signature verification on all operations including GET."
        ),
        "behavior": (
            "Implements the UCP integration surface with ES256 signing, canonical payload rules, and strict request validation and auditing."
        ),
    },
    "services/ai-chat-agent": {
        "current_state": (
            "Agent-facing chat service or wrapper. Uses streaming semantics and must respect meta-first and terminal done or error rules."
        ),
        "expected_state": (
            "Stable streaming behavior, safe request limits, and strict allowlists. Clean integration with gateway and audit pipelines."
        ),
        "behavior": (
            "Provides chat agent capabilities, message routing, conversation management, and streaming responses for UI and API consumers."
        ),
    },
    "services/aiops": {
        "current_state": (
            "AIOps automation and operational intelligence service is present or emerging. Focus is on safe automation and observability-first behavior."
        ),
        "expected_state": (
            "Policy constrained automation with explicit approvals, auditability, and predictable rollback paths."
        ),
        "behavior": (
            "Ingests operational signals, produces recommendations or actions, and integrates with governance constraints and audit logging."
        ),
    },
    "site/dashboard": {
        "current_state": (
            "Security dashboard with locked route rules. Browser must call only /api/* routes. Audit stream uses EventSource proxy patterns. "
            "Agent chat uses fetch streaming with abort propagation and meta-first semantics."
        ),
        "expected_state": (
            "Strict proxy boundaries, no direct upstream calls, and stable SSE parsing. "
            "All data displayed should be traceable to audit integrity and contract versions."
        ),
        "behavior": (
            "Web UI for audit, agent interactions, and operational visibility. Uses BFF routes and enforces allowlisted proxy patterns."
        ),
    },
    "site/configuration-dashboard": {
        "current_state": (
            "Configuration dashboard that relies on a BFF service for safe scaling. "
            "Focus includes templates and visual builders and fixing proxy routing and header forwarding issues."
        ),
        "expected_state": (
            "Production-grade configuration editing with schema validation, safe publish workflows, and redacted exports. "
            "Strict boundaries where the browser calls only dashboard APIs."
        ),
        "behavior": (
            "Web UI for editing and publishing configurations. Integrates with configuration BFF and validates changes against schemas."
        ),
    },
    "site/marketing": {
        "current_state": (
            "Marketing site content and assets. Primary goal is clarity and accurate positioning without leaking internal-only details."
        ),
        "expected_state": (
            "Up-to-date messaging aligned with product reality, clear calls to action, and stable build and deploy pipeline."
        ),
        "behavior": (
            "Public-facing website with product narrative, documentation links, and onboarding entry points."
        ),
    },
    "tools/talos-tui": {
        "current_state": (
            "TUI tool is undergoing redesign focused on stability and contract alignment. "
            "Separation of side effects and UI state is a primary architecture theme."
        ),
        "expected_state": (
            "Stable polling, resilient adapters, and full keyboard-accessible UI with strong tests. "
            "No handshake loops, no rendering bugs, and strict contract compliance."
        ),
        "behavior": (
            "Terminal UI for interacting with Talos services and audit streams. "
            "Acts as an operator tool with strong error handling and observability."
        ),
    },
    "docs": {
        "current_state": (
            "Repository documentation, specifications, and architecture notes. May include locked specs and operational runbooks."
        ),
        "expected_state": (
            "Accurate, structured, and kept in sync with contracts and implementation. "
            "Clear upgrade paths and strong separation of normative versus descriptive text."
        ),
        "behavior": (
            "Houses docs that explain system architecture, behavior, invariants, and operational guidance."
        ),
    },
    "examples": {
        "current_state": (
            "Reference examples for using SDKs and services. Demonstrations should be correct and aligned with current contracts."
        ),
        "expected_state": (
            "Minimal, trustworthy examples that are tested. Avoid stale behavior or undocumented shortcuts."
        ),
        "behavior": (
            "Provides runnable sample code and integration examples that help validate developer workflows."
        ),
    },
}


def _git_root() -> Path:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(out)
    except subprocess.CalledProcessError:
        return Path.cwd()


def _git_sha_short(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
        return out
    except Exception:
        return "unknown"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _render_readme(module_path: str, ctx: ModuleContext | None) -> str:
    current_state = ctx["current_state"] if ctx else "-"
    expected_state = ctx["expected_state"] if ctx else "-"
    behavior = ctx["behavior"] if ctx else "-"

    return (
        f"# Agent workspace: {module_path}\n"
        f"> **Project**: {module_path}\n\n"
        "This folder contains agent-facing context, tasks, workflows, and planning artifacts for this submodule.\n\n"
        "## Current State\n"
        f"{current_state}\n\n"
        "## Expected State\n"
        f"{expected_state}\n\n"
        "## Behavior\n"
        f"{behavior}\n\n"
        "## How to work here\n"
        "- Run/tests:\n"
        "- Local dev:\n"
        "- CI notes:\n\n"
        "## Interfaces and dependencies\n"
        "- Owned APIs/contracts:\n"
        "- Depends on:\n"
        "- Data stores/events (if any):\n\n"
        "## Global context\n"
        "See `.agent/context.md` for monorepo-wide invariants and architecture.\n"
    )


TASK_TEMPLATE = """# Task

## Objective
-

## Constraints
-

## Plan
1.
2.
3.

## Done criteria
-
"""


def ensure_agent_layout(
    module_dir: Path,
    module_path: str,
    context_src: str,
    context_body: str,
    sha: str,
    force_readme: bool,
    root_agent_dir: Path,
) -> None:
    agent_dir = module_dir / ".agent"
    (agent_dir / "agents").mkdir(parents=True, exist_ok=True)
    (agent_dir / "planning").mkdir(parents=True, exist_ok=True)
    (agent_dir / "workflows").mkdir(parents=True, exist_ok=True)

    # Git does not track empty dirs, so keep placeholders.
    for d in ["planning"]:
        keep = agent_dir / d / ".gitkeep"
        keep.touch(exist_ok=True)

    # Junk filter
    ignore_junk = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', '.git', '.venv', 'node_modules')

    # --- NEW: Recursive Copy of Agents and Workflows ---
    # Copy .agent/agents from root to .agent/agents (overwrite existing)
    src_agents = root_agent_dir / "agents"
    dst_agents = agent_dir / "agents"
    if src_agents.exists() and src_agents.is_dir():
        shutil.copytree(src_agents, dst_agents, dirs_exist_ok=True, ignore=ignore_junk)

        # Post-process agents to inject submodule context
        # We rely on the copy above to reset the file to clean state, so we just append.
        ctx = SUBMODULE_CONTEXT.get(module_path)
        if ctx:
            for agent_file in dst_agents.rglob("*.md"):
                content = agent_file.read_text(encoding="utf-8")
                # Safety check to prevent double injection if logic changes later
                if "## Submodule Context" not in content:
                    injection = (
                        "\n\n## Submodule Context\n"
                        f"**Current State**: {ctx['current_state']}\n\n"
                        f"**Expected State**: {ctx['expected_state']}\n\n"
                        f"**Behavior**: {ctx['behavior']}\n"
                    )
                    agent_file.write_text(content + injection, encoding="utf-8")
    else:
        # Fallback if source missing: ensure .gitkeep
        (dst_agents / ".gitkeep").touch(exist_ok=True)

    # Copy .agent/workflows from root to .agent/workflows (overwrite existing)
    src_workflows = root_agent_dir / "workflows"
    dst_workflows = agent_dir / "workflows"
    if src_workflows.exists() and src_workflows.is_dir():
        shutil.copytree(src_workflows, dst_workflows, dirs_exist_ok=True, ignore=ignore_junk)
    else:
        # Fallback if source missing: ensure .gitkeep
        (dst_workflows / ".gitkeep").touch(exist_ok=True)
    
    # --- NEW: Scope Injection (Lock project scope) ---
    # Iterate over all .md files in agents and workflows to inject project scope
    for target_dir in [dst_agents, dst_workflows]:
        if not target_dir.exists():
            continue
        for md_file in target_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            
            # Case 1: YAML Frontmatter exists
            if content.startswith("---"):
                # Avoid double injection
                if f"project: {module_path}" not in content:
                    # Inject 'project: <module>' after the first '---' line
                    lines = content.splitlines()
                    if len(lines) > 0 and lines[0].strip() == "---":
                        lines.insert(1, f"project: {module_path}")
                        content = "\n".join(lines) + "\n" # Ensure trailing newline logic matches
                        md_file.write_text(content, encoding="utf-8")
            
            # Case 2: No Frontmatter
            else:
                 # Avoid double injection
                header_marker = f"> **Project**: {module_path}"
                if header_marker not in content:
                    # Prepend header
                    injection = f"{header_marker}\n\n"
                    md_file.write_text(injection + content, encoding="utf-8")
    # ---------------------------------------------------


    readme = agent_dir / "README.md"
    if force_readme or not readme.exists():
        readme.write_text(
            _render_readme(module_path, SUBMODULE_CONTEXT.get(module_path)),
            encoding="utf-8",
        )

    task = agent_dir / "task.md"
    if not task.exists():
        task.write_text(TASK_TEMPLATE, encoding="utf-8")

    header = (
        "<!--\n"
        "GENERATED FILE. Do not edit directly in submodules.\n"
        f"Source: {context_src}\n"
        f"Source revision: {sha}\n"
        f"Generated at: {_utc_now()}\n"
        "-->\n\n"
    )
    context = agent_dir / "context.md"
    context.write_text(header + context_body.strip() + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--context-source", default="AGENTS.md", help="Root canonical context file path")
    ap.add_argument("--strict", action="store_true", help="Fail if any listed module path is missing")
    ap.add_argument("--only", nargs="*", default=None, help="Only process specific module paths")
    ap.add_argument("--force-readme", action="store_true", help="Overwrite existing .agent/README.md files")
    args = ap.parse_args(argv)

    repo_root = _git_root()
    root_agent_dir = repo_root / ".agent"

    context_path = (repo_root / args.context_source).resolve()
    if not context_path.exists():
        print(f"ERROR: canonical context file not found: {context_path}", file=sys.stderr)
        return 2

    context_body = context_path.read_text(encoding="utf-8")
    if not context_body.strip():
        print("ERROR: canonical context file is empty", file=sys.stderr)
        return 2

    sha = _git_sha_short(repo_root)
    selected: Iterable[str] = args.only if args.only else SUBMODULE_PATHS

    missing: list[str] = []
    
    print("Syncing agent roles and workflows to submodules...")

    for rel in selected:
        module_dir = repo_root / rel
        if not module_dir.exists():
            missing.append(rel)
            continue

        ensure_agent_layout(
            module_dir=module_dir,
            module_path=rel,
            context_src=args.context_source,
            context_body=context_body,
            sha=sha,
            force_readme=args.force_readme,
            root_agent_dir=root_agent_dir,
        )
        print(f"OK: {rel}")

    if missing:
        msg = "Missing module paths:\n" + "\n".join(f"- {m}" for m in missing)
        if args.strict:
            print("ERROR:\n" + msg, file=sys.stderr)
            return 3
        print("WARN:\n" + msg, file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
