# Talos Configuration Service

Backend-for-Frontend (BFF) service for the Talos Configuration Control Plane.

## Features
-   **Validation**: Validates configuration against strict JSON Schema.
-   **Normalization**: Canonicalizes configuration using JCS (RFC 8785).
-   **management**: Handles drafts, history, and publishing.

## API
The API is defined in `contracts/openapi/configuration/v1/openapi.yaml`.

## Development
Run locally:
```bash
uvicorn main:app --reload
```
