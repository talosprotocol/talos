#!/usr/bin/env python3
"""Check that Talos service port consumers match deploy/service-ports.json."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORTS = json.loads((ROOT / "deploy/service-ports.json").read_text())
HOST = PORTS["local_host"]
CONTAINER = PORTS["container"]


def contains(path: str, expected: str) -> bool:
    return expected in (ROOT / path).read_text()


checks = {
    "Compose ingress host/container mapping": contains(
        "docker-compose.yml",
        f"{HOST['gateway_ingress']}:{CONTAINER['envoy_ingress_listener']}",
    ),
    "Compose audit host/container mapping": contains(
        "docker-compose.yml",
        f"{HOST['audit_service']}:{CONTAINER['audit_service']}",
    ),
    "Audit image port": contains("services/audit/Dockerfile", f"EXPOSE {CONTAINER['audit_service']}")
    and contains("services/audit/Dockerfile", f"PORT:-{CONTAINER['audit_service']}"),
    "Launcher service ports": contains(
        "deploy/scripts/common.sh",
        f"talos-ai-gateway:{HOST['ai_gateway_direct']}:",
    )
    and contains("deploy/scripts/common.sh", f"talos-audit-service:{HOST['audit_service']}:")
    and contains("deploy/scripts/start_all.sh", f"TALOS_AI_GATEWAY_PORT={HOST['ai_gateway_direct']}")
    and contains("deploy/scripts/start_all.sh", f"TALOS_AUDIT_PORT={HOST['audit_service']}"),
    "Kubernetes audit ports and dashboard URL": contains(
        "deploy/k8s/base/audit/deployment-service.yaml",
        f"containerPort: {CONTAINER['audit_service']}",
    )
    and contains(
        "deploy/k8s/base/dashboard/deployment-service.yaml",
        f"talos-audit-service:{CONTAINER['audit_service']}",
    ),
    "Production ingress excludes Envoy admin port": contains(
        "docker-compose.prod.yml", "ports: !override\n      - 443:10443"
    )
    and not contains("docker-compose.prod.yml", "9901:9901")
    and contains("services/ingress/envoy.prod.yaml", "address: talos-audit-service, port_value: 8002"),
}

for profile in (
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "docker-compose.staging.yml",
):
    checks[f"{profile} audit URL"] = contains(
        profile,
        f"talos-audit-service:{CONTAINER['audit_service']}",
    )

failed = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {name}")

if failed:
    sys.exit(1)
