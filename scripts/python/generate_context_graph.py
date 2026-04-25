#!/usr/bin/env python3
"""Generate the Talos project context graph from current source files.

The output is intentionally plain JSON and Markdown so it can be reviewed,
diffed, and consumed by lightweight tools without introducing another graph
runtime into the monorepo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON = ROOT / "docs" / "architecture" / "context_graph.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "architecture" / "context_graph.md"
GENERATED_ARTIFACTS = {
    "docs/architecture/context_graph.json",
    "docs/architecture/context_graph.md",
}

IGNORE_DIRS = {
    ".agent",
    ".agents",
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "__pycache__",
    "artifacts",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "test-results",
}

SOURCE_EXTENSIONS = {
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rs",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
    ".json",
}

KNOWN_COMPONENTS = [
    "contracts",
    "core",
    "libs/talos-config",
    "src",
    "talos",
    "services/ai-gateway",
    "services/gateway",
    "services/audit",
    "services/mcp-connector",
    "services/ai-chat-agent",
    "services/aiops",
    "services/governance-agent",
    "services/ucp-connector",
    "services/terminal-adapter",
    "services/configuration",
    "site/dashboard",
    "site/configuration-dashboard",
    "site/marketing",
    "tools/talos-tui",
    "tools/setup-helper",
    "sdks/python",
    "sdks/typescript",
    "sdks/go",
    "sdks/java",
    "sdks/rust",
    "docs",
    "examples",
    "api-testing",
    "deploy",
    "scripts",
    "proto",
]

COMPONENT_ROLES = {
    "contracts": "Schema, inventory, and vector source of truth",
    "core": "Rust security kernel and protocol primitives",
    "libs/talos-config": "Shared configuration library",
    "src": "Root Python gateway/demo API and protocol surface",
    "talos": "Root Python package mirror for protocol modules",
    "services/ai-gateway": "Primary AI Gateway control and data plane",
    "services/gateway": "Legacy/consolidated gateway and local control plane",
    "services/audit": "Tamper-evident audit ingestion and Merkle proofs",
    "services/mcp-connector": "MCP server registry, tool discovery, and invocation bridge",
    "services/ai-chat-agent": "Secure chat example agent service",
    "services/aiops": "DevOps/AIOps example agent service",
    "services/governance-agent": "Talos Governance Agent runtime and supervisor logic",
    "services/ucp-connector": "UCP commerce MCP connector",
    "services/terminal-adapter": "Structured terminal MCP adapter",
    "services/configuration": "Configuration validation, draft, publish, and export service",
    "site/dashboard": "Operator dashboard and BFF proxy",
    "site/configuration-dashboard": "Deprecated configuration dashboard",
    "site/marketing": "Public marketing site",
    "tools/talos-tui": "Terminal operator UI",
    "tools/setup-helper": "Local setup helper",
    "sdks/python": "Python client SDK and reference implementation",
    "sdks/typescript": "TypeScript/Node SDK and client packages",
    "sdks/go": "Go SDK",
    "sdks/java": "Java/JVM SDK",
    "sdks/rust": "Rust SDK and UCP crate",
    "docs": "Documentation and operator guides",
    "examples": "Runnable examples and demos",
    "api-testing": "API test suites and Postman/Karate assets",
    "deploy": "Deployment, Docker, Helm, and local stack scripts",
    "scripts": "Repository automation and verification scripts",
    "proto": "Protocol buffers and generated interface inputs",
}

KEYWORDS = {
    "a2a": "A2A messaging",
    "agent-card": "A2A discovery",
    "audit": "Audit and evidence",
    "budget": "Adaptive budgets",
    "capability": "Capability authorization",
    "chat": "LLM/chat",
    "config": "Configuration management",
    "cursor": "Cursor pagination",
    "gateway": "Gateway runtime",
    "governance": "Governance agent",
    "health": "Health checks",
    "kek": "Secrets rotation",
    "llm": "LLM management",
    "mcp": "MCP tools",
    "metrics": "Metrics and telemetry",
    "policy": "Policy enforcement",
    "rbac": "RBAC",
    "secret": "Secrets management",
    "session": "Session management",
    "terminal": "Terminal tools",
    "ucp": "Commerce/UCP",
    "webauthn": "Dashboard auth",
}

INTERNAL_IMPORT_HINTS = {
    "talos_contracts": "contracts",
    "@talosprotocol/contracts": "contracts",
    "contracts/": "contracts",
    "talos_sdk": "sdks/python",
    "talos-sdk-py": "sdks/python",
    "@talosprotocol/sdk": "sdks/typescript",
    "@talosprotocol/client": "sdks/typescript",
    "talos-core-rs": "core",
    "talos_config": "libs/talos-config",
    "talos-governance-agent": "services/governance-agent",
    "services/governance-agent": "services/governance-agent",
}


@dataclass
class Component:
    id: str
    path: str
    role: str
    kind: str = "module"
    exists: bool = False
    submodule: dict[str, str] | None = None
    manifests: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    routes: list[dict[str, str]] = field(default_factory=list)
    ui_routes: list[str] = field(default_factory=list)
    api_routes: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    internal_refs: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "role": self.role,
            "kind": self.kind,
            "exists": self.exists,
            "submodule": self.submodule,
            "manifests": self.manifests,
            "entrypoints": self.entrypoints,
            "routes": self.routes,
            "ui_routes": self.ui_routes,
            "api_routes": self.api_routes,
            "features": self.features,
            "dependencies": self.dependencies,
            "internal_refs": self.internal_refs,
            "tests": self.tests,
            "docs": self.docs,
            "source_counts": self.source_counts,
        }


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_generated_artifact(path: Path) -> bool:
    try:
        return rel(path) in GENERATED_ARTIFACTS
    except ValueError:
        return False


def read_text(path: Path, limit: int | None = None) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if limit is not None:
        return data[:limit]
    return data


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            path = current / filename
            if is_generated_artifact(path):
                continue
            if path.suffix in SOURCE_EXTENSIONS or filename in {
                "Dockerfile",
                "Makefile",
                "go.mod",
                "pom.xml",
                "package.json",
                "pyproject.toml",
            }:
                yield path


def load_submodules() -> dict[str, dict[str, str]]:
    modules: dict[str, dict[str, str]] = {}
    gitmodules = ROOT / ".gitmodules"
    if not gitmodules.exists():
        return modules

    current: dict[str, str] | None = None
    for raw in gitmodules.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("[submodule "):
            current = {}
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        current[key] = value
        if key == "path" and value:
            modules[value] = current

    try:
        output = subprocess.check_output(
            ["git", "submodule", "status", "--recursive"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return modules

    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        sha = parts[0].lstrip("+-")
        path = parts[1]
        modules.setdefault(path, {})["sha"] = sha
        if len(parts) >= 3:
            modules[path]["ref"] = " ".join(parts[2:])
    return modules


def classify_component(component_id: str) -> str:
    if component_id == "contracts":
        return "contract-source"
    if component_id.startswith("services/"):
        return "service"
    if component_id.startswith("sdks/"):
        return "sdk"
    if component_id.startswith("site/"):
        return "ui"
    if component_id.startswith("tools/"):
        return "tool"
    if component_id in {"deploy", "scripts", "api-testing"}:
        return "tooling"
    if component_id == "docs":
        return "docs"
    return "module"


def parse_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def parse_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def manifest_dependencies(path: Path) -> list[str]:
    name = path.name
    deps: set[str] = set()
    if name == "package.json":
        data = parse_json(path)
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            values = data.get(section)
            if isinstance(values, dict):
                deps.update(str(key) for key in values.keys())
        for workspace in data.get("workspaces", []) if isinstance(data.get("workspaces"), list) else []:
            deps.add(f"workspace:{workspace}")
    elif name == "pyproject.toml":
        data = parse_toml(path)
        project = data.get("project", {})
        if isinstance(project, dict):
            for item in project.get("dependencies", []) or []:
                deps.add(str(item).split()[0])
            optional = project.get("optional-dependencies", {})
            if isinstance(optional, dict):
                for values in optional.values():
                    if isinstance(values, list):
                        for item in values:
                            deps.add(str(item).split()[0])
    elif name == "Cargo.toml":
        data = parse_toml(path)
        for section in ("dependencies", "dev-dependencies"):
            values = data.get(section, {})
            if isinstance(values, dict):
                deps.update(str(key) for key in values.keys())
    elif name == "go.mod":
        for line in read_text(path).splitlines():
            stripped = line.strip()
            if stripped.startswith("require "):
                parts = stripped.split()
                if len(parts) >= 2:
                    deps.add(parts[1])
            elif stripped and not stripped.startswith(("module ", "go ", "//", "(", ")")):
                parts = stripped.split()
                if len(parts) >= 2 and "." in parts[0]:
                    deps.add(parts[0])
    elif name == "pom.xml":
        text = read_text(path)
        for group, artifact in re.findall(
            r"<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?</dependency>",
            text,
            flags=re.DOTALL,
        ):
            deps.add(f"{group.strip()}:{artifact.strip()}")
    return sorted(deps)


FASTAPI_ROUTE_RE = re.compile(r"@(?:app|router)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']")
FASTAPI_PREFIX_RE = re.compile(r"APIRouter\(\s*prefix=[\"']([^\"']+)[\"']")
INCLUDE_ROUTER_RE = re.compile(r"include_router\(([^,\n]+).*?prefix=[\"']([^\"']*)[\"']")


def extract_fastapi_routes(component_path: Path) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    for path in iter_files(component_path):
        if path.suffix != ".py":
            continue
        text = read_text(path)
        prefix_match = FASTAPI_PREFIX_RE.search(text)
        file_prefix = prefix_match.group(1) if prefix_match else ""
        for method, route_path in FASTAPI_ROUTE_RE.findall(text):
            full_path = normalize_route_path(file_prefix, route_path)
            routes.append(
                {
                    "method": method.upper(),
                    "path": full_path,
                    "source": rel(path),
                }
            )
        for router_ref, prefix in INCLUDE_ROUTER_RE.findall(text):
            routes.append(
                {
                    "method": "MOUNT",
                    "path": prefix or "/",
                    "source": rel(path),
                    "target": router_ref.strip(),
                }
            )
    return sorted(routes, key=lambda item: (item["path"], item["method"], item["source"]))


def normalize_route_path(prefix: str, path: str) -> str:
    if not prefix:
        return path or "/"
    if path in {"", "/"}:
        return prefix
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def next_route_from_path(path: Path, marker: str) -> str:
    parts = list(path.parts)
    try:
        index = parts.index(marker)
    except ValueError:
        return rel(path)
    route_parts = parts[index + 1 : -1]
    cleaned: list[str] = []
    for part in route_parts:
        if part.startswith("(") and part.endswith(")"):
            continue
        if part.startswith("[[...") and part.endswith("]]"):
            cleaned.append(f"*{part[5:-2]}")
        elif part.startswith("[...") and part.endswith("]"):
            cleaned.append(f"*{part[4:-1]}")
        elif part.startswith("[") and part.endswith("]"):
            cleaned.append(f":{part[1:-1]}")
        else:
            cleaned.append(part)
    return "/" + "/".join(cleaned) if cleaned else "/"


def extract_next_routes(component_path: Path) -> tuple[list[str], list[str]]:
    ui_routes: set[str] = set()
    api_routes: set[str] = set()
    app_dir = component_path / "src" / "app"
    if not app_dir.exists():
        return [], []
    for path in iter_files(app_dir):
        if path.name == "page.tsx":
            ui_routes.add(next_route_from_path(path, "app"))
        elif path.name == "route.ts":
            api_routes.add(next_route_from_path(path, "app"))
    return sorted(ui_routes), sorted(api_routes)


def extract_readme_features(component_path: Path) -> list[str]:
    readme = component_path / "README.md"
    text = read_text(readme, limit=24000)
    if not text:
        return []

    features: list[str] = []
    in_features = False
    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^#{1,4}\s+.*features", line, flags=re.IGNORECASE):
            in_features = True
            continue
        if in_features and line.startswith("#"):
            break
        if in_features and line.startswith(("-", "*")):
            feature = re.sub(r"^[-*]\s+", "", line)
            feature = re.sub(r"\*\*", "", feature)
            feature = feature.strip()
            if feature:
                features.append(feature[:180])
    return dedupe(features)[:16]


def infer_features(component_id: str, component_path: Path, routes: list[dict[str, str]], ui_routes: list[str]) -> list[str]:
    features = extract_readme_features(component_path)
    text_fragments: list[str] = []
    for route in routes:
        text_fragments.extend(route["path"].lower().strip("/").split("/"))
    for route in ui_routes:
        text_fragments.extend(route.lower().strip("/").split("/"))

    joined = " ".join(text_fragments + [component_id.lower()])
    for key, label in KEYWORDS.items():
        if key in joined and label not in features:
            features.append(label)

    if component_id == "contracts":
        schema_count = len(list((component_path / "schemas").rglob("*.json"))) if (component_path / "schemas").exists() else 0
        vector_count = len(list((component_path / "test_vectors").rglob("*.json"))) if (component_path / "test_vectors").exists() else 0
        features.extend([f"{schema_count} JSON schemas", f"{vector_count} test vector files"])

    return dedupe(features)[:24]


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def source_counts(component_path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in iter_files(component_path):
        suffix = path.suffix or path.name
        counts[suffix] = counts.get(suffix, 0) + 1
    return dict(sorted(counts.items()))


def tests_for(component_path: Path) -> list[str]:
    results: list[str] = []
    for candidate in (
        component_path / "tests",
        component_path / "src" / "__tests__",
        component_path / "__tests__",
    ):
        if candidate.exists():
            results.append(rel(candidate))
    for manifest in (
        component_path / "scripts" / "test.sh",
        component_path / ".agent" / "test_manifest.yml",
        component_path / "Makefile",
    ):
        if manifest.exists():
            results.append(rel(manifest))
    return sorted(set(results))


def docs_for(component_id: str) -> list[str]:
    docs: set[str] = set()
    slug = component_id.split("/")[-1].replace("ai-", "").replace("talos-", "")
    for path in (ROOT / "docs").rglob("*.md") if (ROOT / "docs").exists() else []:
        if is_generated_artifact(path):
            continue
        lower = rel(path).lower()
        if slug and slug in lower:
            docs.add(rel(path))
        elif component_id == "services/ai-gateway" and ("gateway" in lower or "a2a" in lower):
            docs.add(rel(path))
        elif component_id == "services/audit" and "audit" in lower:
            docs.add(rel(path))
    return sorted(docs)[:16]


def entrypoints_for(component_path: Path) -> list[str]:
    candidates = [
        "main.py",
        "app/main.py",
        "src/main.py",
        "src/adapters/http/main.py",
        "api/src/main.py",
        "src/api/server.py",
        "src/app/page.tsx",
        "src/app/layout.tsx",
        "python/src/talos_tui/app.py",
        "src/terminal_adapter/main.py",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "package.json",
        "pyproject.toml",
    ]
    found = [rel(component_path / candidate) for candidate in candidates if (component_path / candidate).exists()]
    return found[:8]


def detect_internal_refs(component_id: str, component_path: Path) -> list[str]:
    refs: set[str] = set()
    sample = []
    for path in iter_files(component_path):
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".mjs", ".rs", ".go", ".java", ".toml", ".json", ".md"}:
            continue
        sample.append(read_text(path, limit=40000))
        if len(sample) >= 120:
            break
    text = "\n".join(sample)
    for hint, target in INTERNAL_IMPORT_HINTS.items():
        if target != component_id and hint in text:
            refs.add(target)
    return sorted(refs)


def build_components() -> dict[str, Component]:
    submodules = load_submodules()
    component_ids = sorted(set(KNOWN_COMPONENTS) | set(submodules.keys()))
    components: dict[str, Component] = {}
    for component_id in component_ids:
        path = ROOT / component_id
        if not path.exists():
            continue
        component = Component(
            id=component_id,
            path=component_id,
            role=COMPONENT_ROLES.get(component_id, "Talos module"),
            kind=classify_component(component_id),
            exists=True,
            submodule=submodules.get(component_id),
        )
        manifests = []
        dependencies: set[str] = set()
        for candidate in (
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "Makefile",
            "scripts/test.sh",
            ".agent/test_manifest.yml",
        ):
            manifest = path / candidate
            if manifest.exists():
                manifests.append(rel(manifest))
                dependencies.update(manifest_dependencies(manifest))
        component.manifests = manifests
        component.dependencies = sorted(dependencies)
        component.entrypoints = entrypoints_for(path)
        component.routes = extract_fastapi_routes(path)
        component.ui_routes, component.api_routes = extract_next_routes(path)
        component.features = infer_features(component_id, path, component.routes, component.ui_routes)
        component.internal_refs = detect_internal_refs(component_id, path)
        component.tests = tests_for(path)
        component.docs = docs_for(component_id)
        component.source_counts = source_counts(path)
        components[component_id] = component
    return components


def build_edges(components: dict[str, Component]) -> list[dict[str, str]]:
    edges: set[tuple[str, str, str]] = set()

    def add(src: str, dst: str, relation: str) -> None:
        if src in components and dst in components and src != dst:
            edges.add((src, dst, relation))

    for component in components.values():
        for ref in component.internal_refs:
            add(component.id, ref, "imports-or-bundles")
        if component.id != "contracts" and (
            component.kind in {"service", "sdk", "ui", "tool"} or "contracts" in component.internal_refs
        ):
            add(component.id, "contracts", "validates-against")

    # Known runtime topology from source routes, Dockerfiles, README, and dashboard envs.
    add("services/ai-gateway", "services/audit", "emits-audit-events")
    add("services/ai-gateway", "services/mcp-connector", "proxies-mcp-tools")
    add("services/ai-gateway", "services/governance-agent", "validates-capabilities")
    add("services/ai-gateway", "libs/talos-config", "loads-config")
    add("services/gateway", "services/audit", "emits-audit-events")
    add("services/gateway", "services/mcp-connector", "proxies-mcp-tools")
    add("services/audit", "contracts", "verifies-audit-schema")
    add("services/configuration", "contracts", "validates-config-schema")
    add("site/dashboard", "services/ai-gateway", "admin-and-data-proxy")
    add("site/dashboard", "services/audit", "audit-proxy")
    add("site/dashboard", "services/mcp-connector", "mcp-resource-proxy")
    add("site/dashboard", "services/ai-chat-agent", "example-proxy")
    add("site/dashboard", "services/aiops", "example-proxy")
    add("site/dashboard", "services/configuration", "configuration-proxy")
    add("site/configuration-dashboard", "services/configuration", "configuration-ui")
    add("tools/talos-tui", "services/ai-gateway", "operator-api")
    add("tools/talos-tui", "services/audit", "audit-reader")
    add("services/ucp-connector", "sdks/python", "uses-sdk-primitives")
    add("services/terminal-adapter", "services/governance-agent", "policy-supervision")
    add("sdks/rust", "core", "uses-core-kernel")
    add("sdks/python", "contracts", "contract-vectors")
    add("sdks/typescript", "contracts", "contract-vectors")
    add("sdks/go", "contracts", "contract-vectors")
    add("sdks/java", "contracts", "contract-vectors")
    add("sdks/rust", "contracts", "contract-vectors")
    add("api-testing", "services/ai-gateway", "black-box-tests")
    add("api-testing", "services/audit", "black-box-tests")
    add("deploy", "services/ai-gateway", "deploys")
    add("deploy", "services/audit", "deploys")
    add("deploy", "site/dashboard", "deploys")

    return [
        {"source": src, "target": dst, "relation": relation}
        for src, dst, relation in sorted(edges)
    ]


def feature_index(components: dict[str, Component]) -> dict[str, list[str]]:
    index: dict[str, set[str]] = {}
    for component in components.values():
        for feature in component.features:
            index.setdefault(feature, set()).add(component.id)
    return {key: sorted(values) for key, values in sorted(index.items())}


def make_graph() -> dict[str, Any]:
    components = build_components()
    edges = build_edges(components)
    return {
        "schema": "talos.context_graph.v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generator": rel(Path(__file__)),
        "source": {
            "root": str(ROOT),
            "notes": [
                "Generated from current checked-out source, manifests, routes, docs, and submodule metadata.",
                "No third-party graph dependencies are required.",
            ],
        },
        "components": [component.to_json() for component in components.values()],
        "edges": edges,
        "feature_index": feature_index(components),
    }


def mermaid_id(component_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", component_id)
    if safe and safe[0].isdigit():
        safe = f"n_{safe}"
    return safe


def mermaid_label(component_id: str) -> str:
    return component_id.replace("/", "<br/>")


def make_mermaid(graph: dict[str, Any]) -> str:
    components = {item["id"]: item for item in graph["components"]}
    buckets = [
        ("Contracts", ["contracts", "core", "libs/talos-config", "proto"]),
        ("Runtime Services", [cid for cid in components if cid.startswith("services/")]),
        ("SDKs And Tools", [cid for cid in components if cid.startswith("sdks/") or cid.startswith("tools/")]),
        ("Operator And Public UI", [cid for cid in components if cid.startswith("site/")]),
        ("Docs Examples Testing Deploy", ["docs", "examples", "api-testing", "deploy", "scripts"]),
    ]

    lines = ["```mermaid", "graph TD"]
    emitted: set[str] = set()
    for title, ids in buckets:
        present = [cid for cid in ids if cid in components]
        if not present:
            continue
        lines.append(f"  subgraph {mermaid_id(title)}[\"{title}\"]")
        for cid in present:
            emitted.add(cid)
            lines.append(f"    {mermaid_id(cid)}[\"{mermaid_label(cid)}\"]")
        lines.append("  end")

    for cid in components:
        if cid not in emitted:
            lines.append(f"  {mermaid_id(cid)}[\"{mermaid_label(cid)}\"]")

    for edge in graph["edges"]:
        src = mermaid_id(edge["source"])
        dst = mermaid_id(edge["target"])
        relation = edge["relation"].replace('"', "'")
        lines.append(f"  {src} -->|\"{relation}\"| {dst}")

    lines.append("```")
    return "\n".join(lines)


def compact_list(values: list[str], limit: int = 6) -> str:
    if not values:
        return "-"
    clipped = values[:limit]
    rendered = ", ".join(f"`{value}`" for value in clipped)
    if len(values) > limit:
        rendered += f", plus {len(values) - limit} more"
    return rendered


def feature_summary(features: list[str]) -> str:
    if not features:
        return "-"
    return "; ".join(features[:5]) + (f"; plus {len(features) - 5} more" if len(features) > 5 else "")


def make_markdown(graph: dict[str, Any]) -> str:
    components = graph["components"]
    lines: list[str] = []
    lines.append("# Talos Context Graph")
    lines.append("")
    lines.append("This graph is generated from the current checked-out Talos source tree. It is intended to be the durable MVP context map for code navigation, planning, drift checks, and onboarding.")
    lines.append("")
    lines.append(f"- Generated at: `{graph['generated_at']}`")
    lines.append(f"- Generator: `{graph['generator']}`")
    lines.append("- Regenerate: `python3 scripts/python/generate_context_graph.py`")
    lines.append("- Scope: submodule metadata, manifests, FastAPI routes, Next.js routes, README feature bullets, docs links, tests, and source-level internal references.")
    lines.append("")
    lines.append("## System Graph")
    lines.append("")
    lines.append(make_mermaid(graph))
    lines.append("")
    lines.append("## MVP Boundaries")
    lines.append("")
    lines.append("- `contracts` remains the source of truth for schemas, inventory, and vectors.")
    lines.append("- Gateway services own runtime enforcement: public data plane, admin RBAC/session JWTs, A2A RPC, MCP tools, budgets, secrets, and audit emission.")
    lines.append("- `services/audit` owns event hash verification, dedupe, Merkle roots, proofs, and audit read APIs.")
    lines.append("- Dashboard browser code should stay behind dashboard-owned `/api/*` BFF routes before reaching runtime services.")
    lines.append("- SDKs and tools must consume published contract artifacts and vectors instead of copying protocol rules.")
    lines.append("")
    lines.append("## Component Matrix")
    lines.append("")
    lines.append("| Component | Kind | Role | Features | Entrypoints | Tests | Internal refs |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for component in components:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{component['id']}`",
                    component["kind"],
                    component["role"].replace("|", "\\|"),
                    feature_summary(component["features"]).replace("|", "\\|"),
                    compact_list(component["entrypoints"], 4).replace("|", "\\|"),
                    compact_list(component["tests"], 3).replace("|", "\\|"),
                    compact_list(component["internal_refs"], 4).replace("|", "\\|"),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Route And Surface Inventory")
    lines.append("")
    for component in components:
        routes = component["routes"]
        ui_routes = component["ui_routes"]
        api_routes = component["api_routes"]
        if not routes and not ui_routes and not api_routes:
            continue
        lines.append(f"### `{component['id']}`")
        if routes:
            lines.append("")
            lines.append("| Method | Path | Source |")
            lines.append("| --- | --- | --- |")
            for route in routes[:80]:
                lines.append(f"| `{route['method']}` | `{route['path']}` | `{route['source']}` |")
            if len(routes) > 80:
                lines.append(f"| ... | ... | {len(routes) - 80} more routes in JSON artifact |")
        if ui_routes:
            lines.append("")
            lines.append(f"- UI routes: {compact_list(ui_routes, 24)}")
        if api_routes:
            lines.append(f"- API routes: {compact_list(api_routes, 24)}")
        lines.append("")

    lines.append("## Feature Index")
    lines.append("")
    lines.append("| Feature | Components |")
    lines.append("| --- | --- |")
    for feature, owners in graph["feature_index"].items():
        feature_escaped = feature.replace('|', '\\|')
        lines.append(f"| {feature_escaped} | {compact_list(owners, 12)} |")

    lines.append("")
    lines.append("## Drift Notes")
    lines.append("")
    lines.append("- This graph is source-derived and should be regenerated after route, contract, SDK, dashboard, or service-boundary changes.")
    lines.append("- The JSON artifact contains the fuller machine-readable graph for tooling, including route sources and dependency summaries.")
    lines.append("- Generated route prefixes are static best-effort extraction; dynamic FastAPI router composition should still be verified with service tests.")
    lines.append("- Submodule paths are included as checked out locally, so dirty submodule worktrees can affect graph content before parent pointers move.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Talos context graph artifacts")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true", help="Fail if generated artifacts differ from disk")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    graph = make_graph()

    # Keep --check deterministic: the graph payload can be stale, but the
    # generated timestamp alone should not make the guard fail.
    if args.check and args.json_out.exists():
        existing_graph = parse_json(args.json_out)
        existing_generated_at = existing_graph.get("generated_at")
        if isinstance(existing_generated_at, str):
            graph["generated_at"] = existing_generated_at

    json_text = json.dumps(graph, indent=2, sort_keys=True) + "\n"
    markdown_text = make_markdown(graph)

    if args.check:
        failures: list[str] = []
        if not args.json_out.exists():
            failures.append(f"{args.json_out} (missing)")
        elif args.json_out.read_text(encoding="utf-8") != json_text:
            failures.append(str(args.json_out))
        if not args.markdown_out.exists():
            failures.append(f"{args.markdown_out} (missing)")
        elif args.markdown_out.read_text(encoding="utf-8") != markdown_text:
            failures.append(str(args.markdown_out))
        if failures:
            print("Context graph artifacts are stale:")
            for failure in failures:
                print(f"  {failure}")
            return 1
        print("Context graph artifacts are current.")
        return 0

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json_text, encoding="utf-8")
    args.markdown_out.write_text(markdown_text, encoding="utf-8")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.markdown_out}")
    print(f"Components: {len(graph['components'])}")
    print(f"Edges: {len(graph['edges'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
