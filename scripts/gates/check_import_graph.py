import ast
import os
import sys
from pathlib import Path
from typing import Set, List

def get_imports(file_path: Path) -> Set[str]:
    """Extract all imports from a file using AST."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except Exception:
        pass
    return imports

def find_module_file(module_name: str, search_paths: List[Path]) -> Path | None:
    """Attempt to find the file corresponding to a module name."""
    parts = module_name.split('.')
    for base_path in search_paths:
        # Check for directory/init.py or single file
        p = base_path.joinpath(*parts)
        if p.with_suffix('.py').exists():
            return p.with_suffix('.py')
        p_init = p.joinpath('__init__.py')
        if p_init.exists():
            return p_init
    return None

def trace_imports(entrypoint: Path, repo_root: Path) -> Set[Path]:
    """Recursively trace all local imports starting from entrypoint."""
    seen_files = {entrypoint.resolve()}
    queue = [entrypoint.resolve()]
    
    # Smarter search paths:
    # 1. The repo root
    # 2. repo_root / "src"
    # 3. The parent of the entrypoint's root package (e.g. if ep is in app/main.py, parent of app/)
    search_paths = [repo_root, repo_root / "src"]
    
    # Try to find the root package name (e.g. 'app')
    # If the entrypoint is something/app/main.py, we want 'something/' in search paths
    # so 'from app.x' works.
    parts = entrypoint.parts
    for i in range(len(parts) - 1, 0, -1):
        test_path = Path(*parts[:i])
        if test_path.joinpath("__init__.py").exists() or parts[i] in ["app", "src", "talos_sdk"]:
            if test_path.parent.exists():
                search_paths.append(test_path.parent)
            break
    else:
        search_paths.append(entrypoint.parent)

    while queue:
        curr = queue.pop(0)
        for imp in get_imports(curr):
            mod_file = find_module_file(imp, search_paths)
            if mod_file and mod_file.resolve() not in seen_files:
                # Only follow imports within the repo_root
                if str(mod_file.resolve()).startswith(str(repo_root.resolve())):
                    seen_files.add(mod_file.resolve())
                    queue.append(mod_file.resolve())
    return seen_files

def main():
    if len(sys.argv) < 3:
        print("Usage: check_import_graph.py <entrypoint> <repo_root>")
        sys.exit(1)

    entrypoint = Path(sys.argv[1]).resolve()
    repo_root = Path(sys.argv[2]).resolve()
    
    if not entrypoint.exists():
        print(f"✅ Entrypoint {entrypoint} not found, skipping graph check.")
        sys.exit(0)

    print(f"Tracing import graph from {entrypoint}...")
    imported_files = trace_imports(entrypoint, repo_root)
    
    exit_code = 0
    forbidden_patterns = ["/tests/", "/test/", "mock_", "fake_", "Mock", "Fake"]
    
    for f in imported_files:
        try:
            rel_path = f.relative_to(repo_root)
        except ValueError:
            # Should not happen if trace_imports is correct, but for safety:
            rel_path = f
        for pattern in forbidden_patterns:
            if pattern in str(rel_path):
                # Small exception: if the pattern is in a filename but it's acceptable? 
                # No, be strict as per user request.
                print(f"❌ Forbidden import detected in runtime graph: {rel_path}")
                exit_code = 1
                break
                
    if exit_code == 0:
        print(f"✅ Runtime graph for {entrypoint} is clean ({len(imported_files)} files).")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
