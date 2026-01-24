import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "src" / "talos_tui"

DOMAIN = ROOT / "domain"
PORTS = ROOT / "ports"

BANNED_IN_DOMAIN_PREFIXES = (
    "aiohttp",
    "textual",
    "rich",
    "talos_sdk",
    "talos_tui.adapters",
    "talos_tui.ui",
)
BANNED_IN_PORTS_PREFIXES = (
    "aiohttp",
    "textual",
    "rich",
    "talos_sdk",
    "talos_tui.adapters",
    "talos_tui.ui",
)

def _imports_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def _assert_no_banned(dir_path: Path, banned_prefixes: tuple[str, ...]) -> None:
    for py in dir_path.rglob("*.py"):
        for imp in _imports_in_file(py):
            if any(imp.startswith(p) for p in banned_prefixes):
                raise AssertionError(f"{py} imports banned module '{imp}'")

def test_domain_has_no_infra_imports():
    _assert_no_banned(DOMAIN, BANNED_IN_DOMAIN_PREFIXES)

def test_ports_have_no_infra_imports():
    _assert_no_banned(PORTS, BANNED_IN_PORTS_PREFIXES)
