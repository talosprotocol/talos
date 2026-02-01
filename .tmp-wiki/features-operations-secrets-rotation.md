# Secrets Rotation Automation (Phase 13)

Talos provides automated, zero-downtime secret rotation to mitigate the risk of long-term credential exposure.

## Overview

The rotation system is built into the `SecretStore` and managed by a background worker that ensures secrets are rotated based on defined policies without impacting service availability.

## Architecture

### Components

- **`MultiKekProvider`**: Manages multiple Key Encryption Keys (KEKs) simultaneously during rotation windows.
- **`PostgresSecretStore`**: Stores encrypted secret envelopes with metadata for versioning.
- **`RotationWorker`**: A background process that identifies secrets nearing expiry and orchestrates the rotation.

### Workflow

1. **Detection**: `RotationWorker` scans `SecretStore` for secrets whose `next_rotation_at` has passed.
2. **Locking**: Uses Postgres advisory locks (`pg_advisory_xact_lock`) to ensure only one worker handles a specific secret.
3. **Generation**: A new version of the secret is generated or requested from the provider.
4. **Encryption**: The new secret is encrypted with the latest KEK.
5. **Update**: The new version is stored in the database.
6. **Grace Period**: Both old and new versions remain valid for a short window to account for cached SDK sessions.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `SECRET_ROTATION_INTERVAL_DAYS` | `30` | Default time between rotations |
| `ROTATION_WORKER_SLEEP_SEC` | `3600` | How often the worker scans |
| `KEK_ROTATION_THRESHOLD_DAYS` | `90` | When to rotate the master KEK |

## Admin API

- `GET /admin/v1/secrets/rotation/status`: View current rotation progress.
- `POST /admin/v1/secrets/rotate/{secret_id}`: Manually trigger rotation for a specific secret.

## Security Considerations

- **Fail-Closed**: If rotation fails, the system stays on the current valid version.
- **Atomic Updates**: Database transactions ensure that secret updates are atomic.
- **Audit Logging**: Every rotation event is logged to the Talos Audit Service.
