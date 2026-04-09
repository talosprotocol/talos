import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RecipeExecutor:
    """
    Executes real recipe logic within a jailed job directory.
    """
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir

    def execute(self, recipe_id: str, args: Dict[str, Any]):
        """Dispatch to specific recipe implementation"""
        if recipe_id == "talos-sdk-init":
            self._talos_sdk_init(args)
        else:
            raise ValueError(f"No execution logic for recipe '{recipe_id}'")

    def _talos_sdk_init(self, args: Dict[str, Any]):
        project_name = args.get("project_name")
        language = args.get("language")
        
        if not project_name or not language:
            raise ValueError("Missing project_name or language")

        project_path = self.job_dir / project_name
        project_path.mkdir()

        if language == "typescript":
            self._init_typescript(project_path, project_name)
        elif language == "python":
            self._init_python(project_path, project_name)
        else:
            raise ValueError(f"Language '{language}' not supported by talos-sdk-init")

    def _init_typescript(self, path: Path, name: str):
        package_json = {
            "name": name,
            "version": "0.1.0",
            "dependencies": {
                "@talosprotocol/sdk": "latest"
            }
        }
        with open(path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        (path / "src").mkdir()
        with open(path / "src" / "index.ts", "w") as f:
            f.write("// Talos SDK Project\n")

    def _init_python(self, path: Path, name: str):
        pyproject = f"""[project]
name = "{name}"
version = "0.1.0"
dependencies = [
    "talos-sdk"
]
"""
        with open(path / "pyproject.toml", "w") as f:
            f.write(pyproject)
            
        (path / name.replace("-", "_")).mkdir()
        with open(path / name.replace("-", "_") / "__init__.py", "w") as f:
            f.write("# Talos SDK Project\n")
