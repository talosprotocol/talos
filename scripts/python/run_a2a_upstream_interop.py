#!/usr/bin/env python3
"""Plan or run Talos A2A upstream interoperability validation."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urljoin, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[2]
TARGETS_PATH = Path(__file__).with_name("a2a_upstream_targets.json")
PYTHON_SDK_ROOT = ROOT / "sdks" / "python"
TYPESCRIPT_SDK_ROOT = ROOT / "sdks" / "typescript"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or run Talos A2A upstream interoperability validation")
    parser.add_argument("--list", action="store_true", help="List known upstream targets and exit")
    parser.add_argument("--target", default=None, help="Target id to inspect or validate")
    parser.add_argument("--gateway-url", default=None, help="Base URL for the running upstream A2A server")
    parser.add_argument("--api-token", default=None, help="Bearer token for the upstream server")
    parser.add_argument("--prompt", default="hello from Talos interop", help="Prompt for send-message validation")
    parser.add_argument(
        "--sdk",
        choices=("python", "typescript", "both", "none"),
        default="both",
        help="Which Talos SDK smoke clients to use",
    )
    parser.add_argument(
        "--exercise-streams",
        action="store_true",
        help="Exercise SendStreamingMessage and SubscribeToTask in addition to unary RPCs",
    )
    parser.add_argument("--run", action="store_true", help="Run the local Talos smoke commands instead of only printing the plan")
    parser.add_argument(
        "--include-tck",
        action="store_true",
        help="Append the official A2A TCK run to the generated plan. Enabled automatically for validation-tool targets.",
    )
    parser.add_argument(
        "--tck-dir",
        default=os.getenv("A2A_TCK_DIR"),
        help="Path to a local a2a-tck checkout. Defaults to $A2A_TCK_DIR if set.",
    )
    parser.add_argument(
        "--tck-category",
        default="mandatory",
        help="TCK category to run when the official A2A TCK is enabled.",
    )
    parser.add_argument(
        "--tck-compliance-report",
        default="report.json",
        help="Compliance report path for the TCK run. Relative paths resolve inside --tck-dir.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--report-file", default=None, help="Optional path to write the generated plan or execution report")
    return parser.parse_args()


def load_targets() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    payload = json.loads(TARGETS_PATH.read_text())
    targets = payload.get("targets")
    if not isinstance(targets, list):
        raise ValueError("a2a upstream target manifest must contain a targets list")
    by_id: dict[str, dict[str, Any]] = {}
    for entry in targets:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("invalid target manifest entry")
        by_id[entry["id"]] = entry
    return payload, by_id


def select_target(args: argparse.Namespace, manifest: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    target_id = args.target or manifest.get("primary_target")
    if not isinstance(target_id, str) or target_id not in by_id:
        raise SystemExit(f"unknown target: {target_id!r}")
    return by_id[target_id]


def _should_include_tck(args: argparse.Namespace, target: dict[str, Any]) -> bool:
    return bool(args.include_tck or target.get("kind") == "validation-tool")


def _resolve_tck_dir(args: argparse.Namespace) -> Path | None:
    if not args.tck_dir:
        return None
    return Path(args.tck_dir).expanduser().resolve()


def _resolve_tck_report_path(tck_dir: Path | None, path: str) -> str:
    report_path = Path(path).expanduser()
    if report_path.is_absolute() or tck_dir is None:
        return str(report_path)
    return str((tck_dir / report_path).resolve())


def _make_tck_command(args: argparse.Namespace) -> dict[str, Any]:
    tck_dir = _resolve_tck_dir(args)
    report_path = _resolve_tck_report_path(tck_dir, args.tck_compliance_report)
    env: dict[str, str] = {}
    if args.api_token:
        env["A2A_AUTH_TYPE"] = "bearer"
        env["A2A_AUTH_TOKEN"] = args.api_token
    command = {
        "id": "official-a2a-tck",
        "kind": "validation-tool",
        "workdir": str(tck_dir) if tck_dir else "<set --tck-dir or A2A_TCK_DIR>",
        "env": env,
        "argv": [
            sys.executable,
            "run_tck.py",
            "--sut-url",
            args.gateway_url,
            "--category",
            args.tck_category,
            "--compliance-report",
            report_path,
        ],
        "timeout_seconds": 300,
        "report_path": report_path,
    }
    if tck_dir is None:
        command["missing_requirements"] = ["tck_dir"]
    return command


def make_command_plan(args: argparse.Namespace, target: dict[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    if args.gateway_url is None:
        return commands
    interop_profile = target.get("talos_smoke_profile")

    if target.get("kind") != "validation-tool" and args.sdk in {"python", "both"}:
        argv = [
            sys.executable,
            "examples/a2a_v1_live_interop.py",
            "--gateway-url",
            args.gateway_url,
            "--prompt",
            args.prompt,
        ]
        if args.api_token:
            argv.extend(["--api-token", args.api_token])
        if isinstance(interop_profile, str):
            argv.extend(["--interop-profile", interop_profile])
        if args.exercise_streams:
            argv.append("--exercise-streams")
        commands.append(
            {
                "id": "python-live-smoke",
                "workdir": str(PYTHON_SDK_ROOT),
                "env": {"PYTHONPATH": str(PYTHON_SDK_ROOT / "src")},
                "argv": argv,
            }
        )

    if target.get("kind") != "validation-tool" and args.sdk in {"typescript", "both"}:
        commands.append(
            {
                "id": "typescript-build",
                "workdir": str(TYPESCRIPT_SDK_ROOT),
                "env": {},
                "argv": ["npm", "--workspace", "@talosprotocol/sdk", "run", "build"],
            }
        )
        argv = [
            "node",
            "examples/a2a_v1_live_interop.mjs",
            "--gateway-url",
            args.gateway_url,
            "--prompt",
            args.prompt,
        ]
        if args.api_token:
            argv.extend(["--api-token", args.api_token])
        if isinstance(interop_profile, str):
            argv.extend(["--interop-profile", interop_profile])
        if args.exercise_streams:
            argv.append("--exercise-streams")
        commands.append(
            {
                "id": "typescript-live-smoke",
                "workdir": str(TYPESCRIPT_SDK_ROOT),
                "env": {},
                "argv": argv,
            }
        )

    if _should_include_tck(args, target):
        commands.append(_make_tck_command(args))

    return commands


def render_plan(
    manifest: dict[str, Any],
    target: dict[str, Any],
    args: argparse.Namespace,
    commands: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "checked_at": manifest["checked_at"],
        "primary_target": manifest["primary_target"],
        "selected_target": target["id"],
        "protocol_gap_note": manifest["protocol_gap_note"],
        "run_mode": "execute" if args.run else "plan",
        "target": target,
        "gateway_url": args.gateway_url,
        "sdk_selection": args.sdk,
        "exercise_streams": args.exercise_streams,
        "tck_enabled": _should_include_tck(args, target),
        "tck_dir": str(_resolve_tck_dir(args)) if _resolve_tck_dir(args) else None,
        "tck_category": args.tck_category if _should_include_tck(args, target) else None,
        "talos_validation_commands": commands,
    }


def execute_commands(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for command in commands:
        env = os.environ.copy()
        env.update(command["env"])
        report_path = command.get("report_path")
        proc = subprocess.run(
            command["argv"],
            cwd=command["workdir"],
            env=env,
            text=True,
            capture_output=True,
            timeout=int(command.get("timeout_seconds", 60)),
        )
        result = {
            "id": command["id"],
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        if isinstance(report_path, str):
            report_file = Path(report_path)
            if report_file.exists():
                result["report_path"] = str(report_file)
                try:
                    result["compliance_report"] = json.loads(report_file.read_text())
                except json.JSONDecodeError:
                    result["compliance_report"] = {"raw": report_file.read_text()}
        results.append(result)
    return results


def _http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        request_headers.setdefault("Content-Type", "application/json")
        body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw)
    except urllib_error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return exc.code, parsed


def _http_sse(url: str, payload: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    req = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=30) as response:
        events: list[dict[str, Any]] = []
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            events.append(json.loads(line[6:]))
        return response.status, events


def _normalize_localhost_url(base_url: str, value: str) -> str:
    base = urlsplit(base_url.rstrip("/") + "/")
    target = urlsplit(value)
    base_host = base.hostname
    target_host = target.hostname
    if not (
        isinstance(base_host, str)
        and isinstance(target_host, str)
        and base_host in {"localhost", "127.0.0.1"}
        and target_host in {"localhost", "127.0.0.1"}
        and base.port == target.port
    ):
        return value
    netloc = base_host
    if target.port is not None:
        netloc = f"{netloc}:{target.port}"
    return urlunsplit((target.scheme, netloc, target.path, target.query, target.fragment))


def probe_v03_target(gateway_url: str, prompt: str) -> dict[str, Any]:
    card_status, card_payload = _http_json(f"{gateway_url.rstrip('/')}/.well-known/agent-card.json")
    rpc_url = gateway_url.rstrip("/") + "/"
    if isinstance(card_payload, dict) and isinstance(card_payload.get("url"), str):
        rpc_url = card_payload["url"]
    rpc_url = _normalize_localhost_url(gateway_url, rpc_url)

    extended_status, extended_payload = _http_json(
        rpc_url,
        method="POST",
        payload={
            "jsonrpc": "2.0",
            "id": "talos-probe-extended",
            "method": "agent/getAuthenticatedExtendedCard",
            "params": {},
        },
    )
    send_status, send_payload = _http_json(
        rpc_url,
        method="POST",
        payload={
            "jsonrpc": "2.0",
            "id": "talos-probe-send",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": "talos-probe-message",
                    "role": "user",
                    "parts": [{"kind": "text", "text": prompt}],
                }
            },
        },
    )
    stream_status, stream_payload = _http_sse(
        rpc_url,
        {
            "jsonrpc": "2.0",
            "id": "talos-probe-stream",
            "method": "message/stream",
            "params": {
                "message": {
                    "messageId": "talos-probe-stream-message",
                    "role": "user",
                    "parts": [{"kind": "text", "text": prompt}],
                }
            },
        },
    )

    return {
        "id": "upstream-v0.3-probe",
        "detected_rpc_url": rpc_url,
        "agent_card_status": card_status,
        "agent_card": card_payload,
        "authenticated_extended_card_status": extended_status,
        "authenticated_extended_card": extended_payload,
        "message_send_status": send_status,
        "message_send": send_payload,
        "message_stream_status": stream_status,
        "message_stream": stream_payload,
    }


def probe_java_hybrid_target(gateway_url: str, prompt: str) -> dict[str, Any]:
    card_status, card_payload = _http_json(f"{gateway_url.rstrip('/')}/.well-known/agent-card.json")
    rpc_url = gateway_url.rstrip("/") + "/"
    capabilities = card_payload.get("capabilities") if isinstance(card_payload, dict) else None
    if isinstance(card_payload, dict):
        interfaces = card_payload.get("supportedInterfaces")
        if isinstance(interfaces, list):
            for item in interfaces:
                if isinstance(item, dict) and isinstance(item.get("url"), str):
                    rpc_url = item["url"]
                    break
    rpc_url = _normalize_localhost_url(gateway_url, urljoin(f"{gateway_url.rstrip('/')}/", rpc_url))

    if isinstance(capabilities, dict) and capabilities.get("extendedAgentCard") is False:
        extended_status = None
        extended_payload: dict[str, Any] = {
            "skipped": True,
            "reason": "Target agent card does not advertise extended discovery",
        }
    else:
        extended_status, extended_payload = _http_json(f"{gateway_url.rstrip('/')}/extendedAgentCard")

    send_status, send_payload = _http_json(
        rpc_url,
        method="POST",
        payload={
            "jsonrpc": "2.0",
            "id": "talos-probe-send",
            "method": "SendMessage",
            "params": {
                "message": {
                    "messageId": "talos-probe-message",
                    "role": "ROLE_USER",
                    "parts": [{"text": prompt}],
                }
            },
        },
    )
    stream_status, stream_payload = _http_sse(
        rpc_url,
        {
            "jsonrpc": "2.0",
            "id": "talos-probe-stream",
            "method": "SendStreamingMessage",
            "params": {
                "message": {
                    "messageId": "talos-probe-stream-message",
                    "role": "ROLE_USER",
                    "parts": [{"text": prompt}],
                }
            },
        },
    )

    return {
        "id": "upstream-java-hybrid-probe",
        "detected_rpc_url": rpc_url,
        "agent_card_status": card_status,
        "agent_card": card_payload,
        "extended_agent_card_status": extended_status,
        "extended_agent_card": extended_payload,
        "message_send_status": send_status,
        "message_send": send_payload,
        "message_stream_status": stream_status,
        "message_stream": stream_payload,
    }


def probe_target(target: dict[str, Any], gateway_url: str, prompt: str) -> dict[str, Any]:
    profile = target.get("talos_smoke_profile")
    if profile == "upstream_java_hybrid":
        return probe_java_hybrid_target(gateway_url, prompt)
    return probe_v03_target(gateway_url, prompt)


def format_text(report: dict[str, Any]) -> str:
    target = report["target"]
    lines = [
        f"Target: {target['display_name']} ({target['id']})",
        f"Checked: {report['checked_at']}",
        f"Provider: {target['provider']}",
        f"Kind: {target['kind']}",
        f"Protocol: {target['protocol_spec_version']}",
    ]
    if "release_version" in target:
        lines.append(f"Release: {target['release_version']} ({target['release_date']})")
    lines.append(f"Rationale: {target['rationale']}")
    lines.append(f"Gap Note: {report['protocol_gap_note']}")
    lines.append("")
    lines.append("Suggested upstream setup:")
    for step in target.get("setup_commands", []):
        lines.append(f"  - {step}")
    if target.get("notes"):
        lines.append("")
        lines.append("Notes:")
        for note in target["notes"]:
            lines.append(f"  - {note}")
    if report["gateway_url"]:
        lines.append("")
        lines.append("Talos validation commands:")
        for command in report["talos_validation_commands"]:
            env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in command["env"].items())
            shell_cmd = shlex.join(command["argv"])
            rendered = f"{env_prefix} {shell_cmd}".strip()
            missing = command.get("missing_requirements")
            suffix = ""
            if isinstance(missing, list) and missing:
                suffix = " [missing: " + ", ".join(missing) + "]"
            lines.append(f"  - (cd {command['workdir']} && {rendered}){suffix}")
    if "results" in report:
        lines.append("")
        lines.append("Execution results:")
        for result in report["results"]:
            lines.append(f"  - {result['id']}: exit_code={result['exit_code']}")
            if "report_path" in result:
                lines.append(f"    report_path={result['report_path']}")
    if "upstream_probe" in report:
        probe = report["upstream_probe"]
        lines.append("")
        lines.append("Upstream probe:")
        if "error" in probe:
            lines.append(f"  - error: {probe['error']}")
        else:
            lines.append(f"  - id: {probe['id']}")
            lines.append(f"  - rpc_url: {probe['detected_rpc_url']}")
            lines.append(f"  - agent_card_status: {probe['agent_card_status']}")
            if "authenticated_extended_card_status" in probe:
                lines.append(
                    f"  - authenticated_extended_card_status: {probe['authenticated_extended_card_status']}"
                )
            if "extended_agent_card_status" in probe:
                lines.append(f"  - extended_agent_card_status: {probe['extended_agent_card_status']}")
            lines.append(f"  - message_send_status: {probe['message_send_status']}")
            lines.append(f"  - message_stream_status: {probe['message_stream_status']}")
    return "\n".join(lines)


def maybe_write_report(path: str | None, report: dict[str, Any]) -> None:
    if not path:
        return
    destination = Path(path)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    manifest, by_id = load_targets()

    if args.list:
        listing = {
            "checked_at": manifest["checked_at"],
            "primary_target": manifest["primary_target"],
            "targets": [
                {
                    "id": target["id"],
                    "display_name": target["display_name"],
                    "kind": target["kind"],
                    "protocol_spec_version": target["protocol_spec_version"],
                    "release_version": target.get("release_version"),
                    "release_date": target.get("release_date"),
                }
                for target in manifest["targets"]
            ],
        }
        maybe_write_report(args.report_file, listing)
        if args.json:
            print(json.dumps(listing, indent=2, sort_keys=True))
        else:
            for target in listing["targets"]:
                release = target["release_version"]
                release_suffix = f" release={release} ({target['release_date']})" if release else ""
                print(
                    f"{target['id']}: {target['display_name']} [{target['kind']}] "
                    f"spec={target['protocol_spec_version']}{release_suffix}"
                )
        return 0

    target = select_target(args, manifest, by_id)
    commands = make_command_plan(args, target)
    report = render_plan(manifest, target, args, commands)

    if args.run:
        if args.gateway_url is None:
            raise SystemExit("--gateway-url is required with --run")
        unresolved = [
            command for command in commands
            if isinstance(command.get("missing_requirements"), list) and command["missing_requirements"]
        ]
        if unresolved:
            missing = ", ".join(
                f"{command['id']} needs {', '.join(command['missing_requirements'])}"
                for command in unresolved
            )
            raise SystemExit(f"cannot execute plan: {missing}")
        report["results"] = execute_commands(commands)
        if target.get("kind") != "validation-tool" and target.get("protocol_spec_version") == "v0.3.0":
            try:
                report["upstream_probe"] = probe_target(target, args.gateway_url, args.prompt)
            except Exception as exc:  # pragma: no cover - live network fallback
                report["upstream_probe"] = {"id": "upstream-probe", "error": str(exc)}
        maybe_write_report(args.report_file, report)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(format_text(report))
        failures = [result for result in report["results"] if result["exit_code"] != 0]
        return 1 if failures else 0

    maybe_write_report(args.report_file, report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
