import json
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "schemas" / "inventory" / "surface_inventory.schema.json"
PYTHON_SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "python"
    / "talos_contracts"
    / "assets"
    / "schemas"
    / "inventory"
    / "surface_inventory.schema.json"
)
INVENTORY_PATH = ROOT / "contracts" / "inventory" / "gateway_surface.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_gateway_surface_inventory_validates_against_schema():
    schema = _load_json(SCHEMA_PATH)
    inventory = _load_json(INVENTORY_PATH)

    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(inventory)


def test_python_asset_surface_inventory_schema_matches_root_schema():
    assert _load_json(PYTHON_SCHEMA_PATH) == _load_json(SCHEMA_PATH)


def test_a2a_v1_rpc_inventory_declares_method_level_permissions():
    inventory = _load_json(INVENTORY_PATH)

    a2a_v1_rpc = next(item for item in inventory["items"] if item["id"] == "a2a.v1.rpc")
    rpc_methods = a2a_v1_rpc["rpc_methods"]

    assert rpc_methods["SendMessage"]["required_scopes"] == ["a2a.send"]
    assert rpc_methods["SendStreamingMessage"]["required_scopes"] == [
        "a2a.send",
        "a2a.subscribe",
    ]
    assert rpc_methods["GetExtendedAgentCard"]["aliases"] == [
        "agent/getAuthenticatedExtendedCard"
    ]
