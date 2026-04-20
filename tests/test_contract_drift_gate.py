from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "python" / "check_contract_drift.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("check_contract_drift", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_drift_gate_ignores_local_virtualenvs(tmp_path: Path) -> None:
    gate = load_gate()
    vendor_file = tmp_path / ".venv" / "lib" / "python3.14" / "site-packages" / "vendor.py"
    vendor_file.parent.mkdir(parents=True)
    vendor_file.write_text("def uuidv7():\n    return '018a0000-0000'\n")

    assert gate.check_drift(tmp_path) is False


def test_contract_drift_gate_reports_source_reimplementation(tmp_path: Path) -> None:
    gate = load_gate()
    source_file = tmp_path / "service" / "api.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("def encode_cursor(value):\n    return value\n")

    assert gate.check_drift(tmp_path) is True
