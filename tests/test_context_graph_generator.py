from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "python" / "generate_context_graph.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_context_graph", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_context_graph_contains_core_runtime_boundaries() -> None:
    generator = load_generator()
    graph = generator.make_graph()

    components = {component["id"] for component in graph["components"]}
    assert {
        "contracts",
        "services/ai-gateway",
        "services/audit",
        "services/mcp-connector",
        "site/dashboard",
        "tools/talos-tui",
    }.issubset(components)

    edges = {
        (edge["source"], edge["target"], edge["relation"])
        for edge in graph["edges"]
    }
    assert ("services/ai-gateway", "services/audit", "emits-audit-events") in edges
    assert ("site/dashboard", "services/ai-gateway", "admin-and-data-proxy") in edges
    assert ("tools/talos-tui", "services/ai-gateway", "operator-api") in edges


def test_context_graph_excludes_agent_metadata_from_source_surfaces() -> None:
    generator = load_generator()
    graph = generator.make_graph()

    for component in graph["components"]:
        for route in component["routes"]:
            assert "/.agents/" not in route["source"]
            assert "/.agent/" not in route["source"]
        assert "docs/architecture/context_graph.md" not in component["docs"]
        assert "docs/architecture/context_graph.json" not in component["docs"]

    core = next(component for component in graph["components"] if component["id"] == "core")
    assert "core/.agent/test_manifest.yml" in core["manifests"]


def test_context_graph_artifacts_are_current() -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
