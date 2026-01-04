# Docker Image Contract: `ghcr.io/talosprotocol/talos`

> [!IMPORTANT]
> This document defines the stability guarantees and public interface for the official Talos Docker image. Downstream consumers (agents, deployments, tools) should rely ONLY on the surface area defined here.

## Image Identity

- **Registry**: `ghcr.io/talosprotocol/talos`
- **Purpose**: Runs the Talos Node (Gateway / Control Plane).
- **Maintainer**: Talos Protocol Core Team

## Tags and Versioning

| Tag Format | Trigger | Stability | Use Case |
| :--- | :--- | :--- | :--- |
| `latest` | Push to `main` | Unstable (Rolling) | continuous-delivery, development |
| `vX.Y.Z` | Git Tag `vX.Y.Z` | Stable (Immutable) | production deployments, pinned dependencies |
| `sha-<hash>` | Commit Push | Immutable | precise supply-chain auditing |

## Runtime Contract

### Entrypoint & Command

- **Entrypoint**: `talos-node` (Shim wrapper)
- **Default Command**: `serve`
- **Usage**:
    ```bash
    # Run default node
    docker run ghcr.io/talosprotocol/talos:latest

    # Run specific command (if supported by shim)
    docker run ghcr.io/talosprotocol/talos:latest help
    ```

### Network Ports

| Port | Protocol | Purpose | Visibility |
| :--- | :--- | :--- | :--- |
| **8000** | HTTP | Gateway API & Health | Public / Mesh |

> **Note**: Port **5000** is considered internal and implementation-private. It is NOT part of the public contract.

### Health Check

- **Endpoint**: `GET /healthz`
- **Expected Status**: `200 OK`
- **Docker Healthcheck**: Built-in (see Dockerfile).

### Environment Variables

The following environment variables are part of the public API.

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `TALOS_MODE` | No | `gateway` | Node operation mode (`gateway`, `node`). |
| `PORT` | No | `8000` | Port to listen on. |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARN`, `ERROR`). |

### Filesystem & Persistence

- **Read-Only Compatible**: The image is designed to run with a read-only root filesystem.
- **Writable Paths**:
    - `/tmp` (Ephemeral)
    - `/data` (If persistence is required, though stateless is preferred)

## Security Posture

- **User**: Non-root `talos` user (UID `10001`).
- **Base Image**: Minimal `python:3.11-slim`.
- **Capabilities**: None required. Should run with `--cap-drop=ALL`.
- **Build Artifacts**: No compilers, build tools, or secrets in the final image.
