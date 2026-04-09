import json
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA_ROOT = ROOT / "contracts" / "schemas" / "a2a"
SOURCE_VECTOR_ROOT = ROOT / "contracts" / "test_vectors" / "a2a"
PYTHON_SCHEMA_ROOT = (
    ROOT
    / "contracts"
    / "python"
    / "talos_contracts"
    / "assets"
    / "schemas"
    / "a2a"
)
PYTHON_VECTOR_ROOT = (
    ROOT
    / "contracts"
    / "python"
    / "talos_contracts"
    / "assets"
    / "test_vectors"
    / "a2a"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*.json"))


def test_a2a_schema_index_matches_python_assets():
    assert _load_json(PYTHON_SCHEMA_ROOT / "index.json") == _load_json(
        SOURCE_SCHEMA_ROOT / "index.json"
    )


def test_a2a_v1_schema_assets_match_root():
    source_root = SOURCE_SCHEMA_ROOT / "v1"
    asset_root = PYTHON_SCHEMA_ROOT / "v1"
    source_files = _json_files(source_root)
    assert source_files == _json_files(asset_root)

    for rel_path in source_files:
        assert _load_json(asset_root / rel_path) == _load_json(source_root / rel_path)


def test_a2a_v1_vector_assets_match_root():
    source_root = SOURCE_VECTOR_ROOT / "v1"
    asset_root = PYTHON_VECTOR_ROOT / "v1"
    source_files = _json_files(source_root)
    assert source_files == _json_files(asset_root)

    for rel_path in source_files:
        assert _load_json(asset_root / rel_path) == _load_json(source_root / rel_path)


def test_a2a_v1_schemas_are_structurally_valid():
    for rel_path in _json_files(SOURCE_SCHEMA_ROOT / "v1"):
        Draft7Validator.check_schema(_load_json(SOURCE_SCHEMA_ROOT / "v1" / rel_path))
