# Talos API Testing

This directory holds root-level API testing assets that are not owned by a
single service.

## Layout

- `postman/`: Postman collection plus the lightweight Python collection runner.
- `scripts/`: local stack setup and seed helpers for API testing.
- `pytest/`: cross-service API smoke tests.
- `karate/`: additional Karate feature tests and runner.
- `logs/`: generated local-stack logs. This directory is disposable.

## Common Commands

Start the local Postman test stack:

```bash
api-testing/scripts/run-script-test.sh
```

Run the Postman collection simulator against a running stack:

```bash
python3 api-testing/postman/simulate_postman.py
```

The first AI Gateway request in the collection calls
`POST /admin/v1/auth/token` with `X-Talos-Admin-Secret` and stores the returned
scoped session JWT as `api_session_token`. Subsequent admin and protected
data-plane requests use that JWT. The seeded virtual key remains
`test-key-hard` and is passed only when minting sessions or when explicitly
testing direct data-plane virtual-key auth.

Run cross-service pytest smoke checks:

```bash
pytest api-testing/pytest
```

Run the additional Karate tests:

```bash
api-testing/karate/run-karate.sh
```

Clean generated logs and caches:

```bash
scripts/cleanup_generated.sh
```
