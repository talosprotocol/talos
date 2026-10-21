# Talos Protocols: Operational Runbook

Use this guide to start, stop, and operate the Talos services in the correct order.

## Production Compose profile

The root `docker-compose.yml` is for local development. For the production
override, provide `PROD_POSTGRES_PASSWORD`, `PROD_REDIS_PASSWORD`,
`PROD_AUTH_SECRET`, `PROD_ADMIN_PASSWORD`, `PROD_AUTH_ADMIN_SECRET`,
`PROD_AUTH_ADMIN_PRINCIPAL`, and `PROD_AUTH_COOKIE_HMAC_SECRET` through the
deployment secret manager, then run:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Use unique values. `PROD_AUTH_COOKIE_HMAC_SECRET` must be base64url-encoded and
at least 32 decoded bytes; the other authentication secrets must meet the
dashboard readiness checks. The production override removes inherited host
ports for Postgres, Redis, audit, and the dashboard. Only Envoy ports 80 and
443 are public; its admin port is not published. The TLS certificate directory
must be provisioned before starting Envoy.

The local port roles are defined in [`service-ports.json`](service-ports.json):
public ingress is 8000, direct AI Gateway is 8001, and Audit is 8002.

## 1. Environment Setup

Ensure you are in the `deploy` root directory.

```bash
# Set mode (released = PyPI, workspace = local SDK mount)
export EXAMPLES_MODE=workspace
```

## 2. Start Standalone Agents (Backend)

The agents must be running for the Dashboard to connect to them.

### DevOps Agent (Port 8200)
```bash
cd repos/talos-aiops
./scripts/up.sh $EXAMPLES_MODE
# Verify: curl http://localhost:8200/health
```

### Secure Chat Agent (Port 8100)
```bash
cd repos/talos-ai-chat-agent
./scripts/up.sh $EXAMPLES_MODE
# Verify: curl http://localhost:8100/health
```

## 3. Start Dashboard (Frontend & Integrator)

The dashboard proxies requests to the agents.

```bash
cd repos/talos-dashboard
# Ensure env vars point to local agents
export TALOS_CHAT_URL="http://localhost:8100"
export TALOS_AIOPS_URL="http://localhost:8200"

npm install
npm run dev
# Access: http://localhost:3000
```

## 4. Verification Steps

| Feature | Action | Expected Result |
|---------|--------|-----------------|
| **Secure Chat** | Go to `/examples/chat` -> Send "Hello" | Backend responds with encrypted echo ("Echo (Secure): ...") |
| **DevOps Agent** | Go to `/examples/devops` -> Click "Check Status" | Status updates from "Checking..." to "ONLINE" (proxying to :8200) |
| **Legacy Agent** | Go to `http://localhost:3002` | "Reference Implementation" UI loads (Simulation Mode) |

## 5. Shutdown

```bash
# Stop Agents
cd repos/talos-aiops && ./scripts/down.sh
cd repos/talos-ai-chat-agent && ./scripts/down.sh

# Stop Dashboard
# Ctrl+C in the terminal running npm run dev
```
