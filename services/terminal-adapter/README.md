# Talos Terminal MCP Adapter

**Repo Role**: Structured terminal access for AI agents with policy enforcement and audit logging.

## Overview

The Terminal MCP Adapter replaces raw shell access with a structured MCP tool interface that:

1. **Forces structured API calls** instead of uncontrolled shell commands
2. **Classifies commands by risk** (READ/WRITE/HIGH_RISK) for policy enforcement
3. **Maintains audit trails** via session-based Merkle trees

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Terminal MCP Adapter                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                  MCP Tool Surface                     │    │
│  │  terminal:execute | terminal:read | terminal:stream  │    │
│  │  terminal:write_input | terminal:anchor_session      │    │
│  └─────────────────────────┬────────────────────────────┘    │
│                            │                                  │
│  ┌─────────────────────────▼────────────────────────────┐    │
│  │                CommandClassifier                      │    │
│  │  READ: ls, cat, git status (bypass Supervisor)       │    │
│  │  WRITE: mkdir, npm install (Supervisor check)        │    │
│  │  HIGH_RISK: rm, curl, git push (halt + escalate)     │    │
│  └─────────────────────────┬────────────────────────────┘    │
│                            │                                  │
│  ┌─────────────────────────▼────────────────────────────┐    │
│  │                SessionManager                         │    │
│  │  • Ephemeral Merkle trees (in-memory)                │    │
│  │  • Write-Ahead Log (crash recovery)                  │    │
│  │  • Periodic anchoring (every 10 min)                 │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Quickstart

### Installation

```bash
cd services/terminal-adapter
pip install -e ".[dev]"
```

### Running

```bash
# Set project root
export TALOS_PROJECT_ROOT=/path/to/your/project

# Start adapter
python -m terminal_adapter.main
# or
uvicorn terminal_adapter.main:app --port 8083
```

### Usage

```bash
# Execute a READ command (fast path)
curl -X POST http://localhost:8083/tools/terminal:execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ls", "args": ["-la"]}'

# Execute a WRITE command (requires dev mode or Supervisor)
curl -X POST http://localhost:8083/tools/terminal:execute \
  -H "Content-Type: application/json" \
  -d '{"command": "mkdir", "args": ["-p", "new_dir"]}'

# List sessions
curl http://localhost:8083/tools/terminal:list_sessions
```

## MCP Tools

| Tool | Scope | Risk | Description |
|------|-------|------|-------------|
| `terminal:execute` | `terminal:write` | WRITE | Execute command, wait for completion |
| `terminal:stream` | `terminal:write` | WRITE | Execute command, stream output |
| `terminal:read` | `terminal:read` | READ | Read from existing session |
| `terminal:write_input` | `terminal:write` | WRITE | Send stdin to running session |
| `terminal:abort` | `terminal:write` | WRITE | Send SIGINT/SIGTERM to session |
| `terminal:list_sessions` | `terminal:read` | READ | List active terminal sessions |
| `terminal:anchor_session` | `terminal:read` | READ | Force anchor session tree |

## Command Classification

Commands are classified by risk level:

| Risk Level | Latency | Examples |
|------------|---------|----------|
| **READ** | ~5ms | `ls`, `cat`, `git status` |
| **WRITE** | ~50-100ms | `mkdir`, `npm install`, `git commit` |
| **HIGH_RISK** | Halts | `rm`, `curl`, `git push` |

## Security

- **Signed Policy Manifest**: Classifications can be locked via a Supervisor-signed manifest
- **Paranoid Mode**: If manifest is invalid, ALL commands require Supervisor approval
- **Path Sandboxing**: Working directory confined to project root
- **Environment Filtering**: Dangerous env vars (LD_PRELOAD, etc.) are blocked

## Testing

```bash
pytest tests/
```

## License

Apache License 2.0
