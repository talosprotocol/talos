# Talos Protocols: Operational Runbook

Use this guide to start, stop, and operate the Talos services in the correct order.

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
