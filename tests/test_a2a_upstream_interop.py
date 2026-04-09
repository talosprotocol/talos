from __future__ import annotations

import json
import subprocess
import sys
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "python" / "run_a2a_upstream_interop.py"


def test_a2a_upstream_interop_lists_pinned_targets():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--list", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["primary_target"] == "official-python-helloworld"
    assert payload["targets"][0]["protocol_spec_version"] == "v0.3.0"

    ids = {target["id"] for target in payload["targets"]}
    assert "official-python-helloworld" in ids
    assert "official-a2a-tck" in ids


def test_a2a_upstream_interop_plan_includes_local_smokes():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--target",
            "official-python-helloworld",
            "--gateway-url",
            "http://127.0.0.1:8011",
            "--api-token",
            "sdk-token",
            "--prompt",
            "hello",
            "--exercise-streams",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["run_mode"] == "plan"
    assert payload["selected_target"] == "official-python-helloworld"
    assert payload["target"]["id"] == "official-python-helloworld"
    assert payload["gateway_url"] == "http://127.0.0.1:8011"

    commands = payload["talos_validation_commands"]
    assert [command["id"] for command in commands] == [
        "python-live-smoke",
        "typescript-build",
        "typescript-live-smoke",
    ]
    assert "--interop-profile" in commands[0]["argv"]
    assert "upstream_v0_3" in commands[0]["argv"]
    assert "--exercise-streams" in commands[0]["argv"]
    assert "--interop-profile" in commands[2]["argv"]
    assert "upstream_v0_3" in commands[2]["argv"]
    assert "--exercise-streams" in commands[2]["argv"]


def test_a2a_upstream_interop_java_plan_uses_hybrid_profile():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--target",
            "official-java-helloworld-server",
            "--gateway-url",
            "http://127.0.0.1:9999",
            "--prompt",
            "hello",
            "--exercise-streams",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["selected_target"] == "official-java-helloworld-server"
    commands = payload["talos_validation_commands"]
    assert "--interop-profile" in commands[0]["argv"]
    assert "upstream_java_hybrid" in commands[0]["argv"]
    assert "--interop-profile" in commands[2]["argv"]
    assert "upstream_java_hybrid" in commands[2]["argv"]


def test_a2a_upstream_interop_tck_plan_requires_local_checkout():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--target",
            "official-a2a-tck",
            "--gateway-url",
            "http://127.0.0.1:8000",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["selected_target"] == "official-a2a-tck"
    assert payload["tck_enabled"] is True

    commands = payload["talos_validation_commands"]
    assert [command["id"] for command in commands] == ["official-a2a-tck"]
    assert commands[0]["missing_requirements"] == ["tck_dir"]
    assert commands[0]["argv"][:2] == [sys.executable, "run_tck.py"]
    assert "--sut-url" in commands[0]["argv"]
    assert "--category" in commands[0]["argv"]


def test_a2a_upstream_interop_plan_can_append_tck(tmp_path):
    tck_dir = tmp_path / "a2a-tck"
    tck_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--target",
            "official-python-helloworld",
            "--gateway-url",
            "http://127.0.0.1:8011",
            "--api-token",
            "sdk-token",
            "--include-tck",
            "--tck-dir",
            str(tck_dir),
            "--tck-compliance-report",
            "compliance/report.json",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    commands = payload["talos_validation_commands"]
    assert [command["id"] for command in commands] == [
        "python-live-smoke",
        "typescript-build",
        "typescript-live-smoke",
        "official-a2a-tck",
    ]
    tck_command = commands[-1]
    assert tck_command["workdir"] == str(tck_dir.resolve())
    assert tck_command["report_path"] == str((tck_dir / "compliance" / "report.json").resolve())
    assert tck_command["env"] == {
        "A2A_AUTH_TYPE": "bearer",
        "A2A_AUTH_TOKEN": "sdk-token",
    }


def test_a2a_upstream_interop_tck_run_loads_compliance_report(tmp_path):
    tck_dir = tmp_path / "a2a-tck"
    tck_dir.mkdir()
    runner = tck_dir / "run_tck.py"
    runner.write_text(
        "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                "",
                "argv = sys.argv[1:]",
                "report = Path(argv[argv.index('--compliance-report') + 1])",
                "report.parent.mkdir(parents=True, exist_ok=True)",
                "report.write_text(json.dumps({'summary': {'compliance_level': 'PASS'}}))",
            ]
        )
        + "\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--target",
            "official-a2a-tck",
            "--gateway-url",
            "http://127.0.0.1:8000",
            "--run",
            "--tck-dir",
            str(tck_dir),
            "--tck-compliance-report",
            "reports/official.json",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["selected_target"] == "official-a2a-tck"
    assert "upstream_probe" not in payload

    results = payload["results"]
    assert len(results) == 1
    assert results[0]["id"] == "official-a2a-tck"
    assert results[0]["exit_code"] == 0
    assert results[0]["compliance_report"] == {
        "summary": {"compliance_level": "PASS"}
    }


def test_a2a_upstream_v03_probe_remaps_localhost_rpc_url(monkeypatch):
    spec = importlib.util.spec_from_file_location("a2a_upstream_runner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def fake_http_json(url, *, method="GET", payload=None, headers=None):
        if method == "GET":
            return 200, {
                "protocolVersion": "0.3.0",
                "url": "http://localhost:9999/",
            }
        if payload["method"] == "agent/getAuthenticatedExtendedCard":
            return 200, {"result": {"name": "Extended"}}
        if payload["method"] == "message/send":
            return 200, {"result": {"kind": "message"}}
        raise AssertionError(f"unexpected payload: {payload}")

    def fake_http_sse(url, payload):
        assert payload["method"] == "message/stream"
        return 200, [{"result": {"kind": "message"}}]

    monkeypatch.setattr(module, "_http_json", fake_http_json)
    monkeypatch.setattr(module, "_http_sse", fake_http_sse)

    result = module.probe_v03_target("http://127.0.0.1:9999", "hello")

    assert result["detected_rpc_url"] == "http://127.0.0.1:9999/"
    assert result["authenticated_extended_card_status"] == 200
    assert result["message_send_status"] == 200
    assert result["message_stream_status"] == 200


def test_a2a_upstream_java_hybrid_probe_uses_root_rpc_and_role_user(monkeypatch):
    spec = importlib.util.spec_from_file_location("a2a_upstream_runner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def fake_http_json(url, *, method="GET", payload=None, headers=None):
        if method == "GET":
            return 200, {
                "supportedInterfaces": [
                    {
                        "url": "http://localhost:9999/",
                        "protocolBinding": "JSONRPC",
                        "protocolVersion": "1.0",
                    }
                ],
                "capabilities": {"extendedAgentCard": False},
            }
        assert url == "http://127.0.0.1:9999/"
        assert payload["method"] == "SendMessage"
        assert payload["params"]["message"]["role"] == "ROLE_USER"
        return 200, {"result": {"message": {"messageId": "msg-1"}}}

    def fake_http_sse(url, payload):
        assert url == "http://127.0.0.1:9999/"
        assert payload["method"] == "SendStreamingMessage"
        assert payload["params"]["message"]["role"] == "ROLE_USER"
        return 200, [{"result": {"delta": "java-one"}}]

    monkeypatch.setattr(module, "_http_json", fake_http_json)
    monkeypatch.setattr(module, "_http_sse", fake_http_sse)

    result = module.probe_java_hybrid_target("http://127.0.0.1:9999", "hello")

    assert result["detected_rpc_url"] == "http://127.0.0.1:9999/"
    assert result["extended_agent_card"]["skipped"] is True
    assert result["message_send_status"] == 200
    assert result["message_stream_status"] == 200
