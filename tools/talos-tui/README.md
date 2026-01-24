# Talos Protocol TUI

A terminal-based user interface for monitoring and inspecting the Talos Protocol network.

![Talos TUI](https://placeholder-image-url.com) (*Screenshot placeholder*)

## Features (v1)

*   **Status Dashboard**: Real-time view of connected peers, sessions, and network latency.
*   **Audit Viewer**: Read-only inspection of the audit log with pagination.
*   **Safe Execution**: Read-only payload, redacted secrets, and strict version handshake.

## Installation

### From Source

```bash
cd tools/talos-tui/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Ensure you have a running Gateway and Audit service.

```bash
# Minimal run (defaults to localhost)
talos-tui

# Custom Endpoints
export TALOS_GATEWAY_URL="http://localhost:8000"
export TALOS_AUDIT_URL="http://localhost:8001"
talos-tui
```

## Development

### Architecture

This project follows a strict **Hexagonal Architecture**:

*   **`domain`**: Pure Python data models (View State). No imports allowed from adapters/ui.
*   **`ports`**: Protocol definitions for external interactions.
*   **`adapters`**: Implementations of ports (HTTP, SDK).
*   **`ui`**: Textual screens and widgets.

### Running Tests

```bash
# Unit Tests
pytest python/tests/unit

# Architecture Gate
python3 python/tests/architecture/test_import_rules.py

# Performance Budget
python3 python/tests/test_perf_budget.py
```

### Developer Convenience

We provide a `Makefile` and helper scripts to simplify common tasks:

```bash
cd tools/talos-tui/python

# First time setup (creates venv, installs deps)
make setup

# Run the TUI (auto-activates venv)
../../scripts/tui_run.sh

# Run all tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint
```

## Deployment

### Docker

Build the image:
```bash
docker build -t talos-tui -f tools/talos-tui/Dockerfile tools/talos-tui
```

Run container:
```bash
docker run -it --rm \
  -e TALOS_GATEWAY_URL="http://host.docker.internal:8000" \
  -e TALOS_AUDIT_URL="http://host.docker.internal:8001" \
  talos-tui
```

### Helm

Install the chart:
```bash
helm install talos-tui tools/talos-tui/helm/talos-tui \
  --set env.TALOS_GATEWAY_URL="http://gateway-service:8000"
```

To access the TUI in the cluster:
```bash
# Find pod name
kubectl get pods -l app.kubernetes.io/name=talos-tui

# Attach to the running session (requires tty: true in deployment)
kubectl attach -it deployment/talos-tui -c talos-tui
```
