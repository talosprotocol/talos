# Access Control Lists (ACLs)

> **Fine-Grained Permission Control for MCP Agents**

## Overview

The ACL system provides granular permission control for MCP tool and resource access. It allows you to specify exactly which tools each peer can use, which resources they can access, and how often they can make requests.

## Features

| Feature | Description |
| :--- | :--- |
| **Pattern Matching** | Wildcard patterns for tools and resources |
| **Deny-First** | Deny rules always take precedence |
| **Rate Limiting** | Requests/min and bytes/day limits |
| **Audit Logging** | All access attempts are logged |
| **YAML Config** | Human-readable configuration files |

---

## Quick Start

### 1. Create a permissions file

```yaml
# config/permissions.yaml
default_allow: false

peers:
  <AGENT_PEER_ID>:
    enabled: true
    allow_tools:
      - "file_read"
      - "git_*"
    deny_tools:
      - "rm_*"
      - "delete_*"
    rate_limit:
      requests_per_minute: 60
```

### 2. Load in your server

```python
from src.mcp_bridge.acl import load_acl_from_file
from src.mcp_bridge.proxy import MCPServerProxy

acl = load_acl_from_file("config/permissions.yaml")

server = MCPServerProxy(
    engine=engine,
    allowed_client_id=peer_id,
    command="uvx mcp-server-git",
    acl_manager=acl,  # Enable ACL checks
)
```

### 3. Access is automatically enforced

When a peer tries to call a tool:

- ✅ Allowed tools execute normally
- ❌ Denied tools return JSON-RPC error

---

## Permission Rules

### Tool Patterns

```yaml
allow_tools:
  - "file_read"       # Exact match
  - "git_*"           # Prefix wildcard (git_status, git_diff, etc.)
  - "*_list"          # Suffix wildcard
  - "search_*"        # All search tools
```

### Resource Patterns

```yaml
allow_resources:
  - "//localhost/repo/**"       # All files in repo
  - "//localhost/data/*.json"   # Only JSON files
  
deny_resources:
  - "**/.git/**"                # Block git internals
  - "**/secrets/**"             # Block secrets
  - "**/.env"                   # Block env files
```

### Evaluation Order

1. **Peer enabled?** → If disabled, DENY
2. **Rate limited?** → If exceeded, DENY
3. **Explicit deny match?** → DENY (deny always wins)
4. **Explicit allow match?** → ALLOW
5. **No match?** → Use `default_allow` setting

---

## Rate Limiting

Protect your server from abuse:

```yaml
rate_limit:
  requests_per_minute: 60      # Max 60 requests/min
  data_bytes_per_day: 100000000  # Max 100MB/day
  max_execution_time_seconds: 30  # Max 30s per tool
```

Rate-limited requests receive this error:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Access denied: Rate limit exceeded: 60/min",
    "data": {"permission": "RATE_LIMITED"}
  }
}
```

---

## Audit Logging

Every access attempt is logged:

```python
acl = ACLManager()

# ... after some requests ...

log = acl.get_audit_log(limit=100)
for entry in log:
    print(f"{entry['timestamp']}: {entry['peer_id'][:16]}... "
          f"{entry['method']} -> {entry['permission']}")
```

Sample output:

```text
1703367890.123: abc123... tools/call -> ALLOW
1703367891.456: abc123... tools/call -> DENY
1703367892.789: xyz789... resources/read -> RATE_LIMITED
```

---

## Configuration Examples

### Read-Only Agent

```yaml
readonly_agent:
  allow_tools:
    - "*_read"
    - "*_list"
    - "*_get"
  deny_tools:
    - "*_write"
    - "*_delete"
    - "*_create"
```

### Development Agent (Full Access)

```yaml
dev_agent:
  allow_tools:
    - "*"
  deny_tools: []
  rate_limit:
    requests_per_minute: 1000
```

### Suspended Agent

```yaml
suspended_agent:
  enabled: false  # Completely blocked
```

---

## API Reference

### ACLManager

```python
class ACLManager:
    def __init__(self, default_allow: bool = False)
    def add_peer(self, permissions: PeerPermissions) -> None
    def remove_peer(self, peer_id: str) -> bool
    def get_peer(self, peer_id: str) -> Optional[PeerPermissions]
    def check(self, peer_id, method, params) -> ACLCheckResult
    def get_audit_log(self, limit: int = 100) -> list[dict]
```

### ACLCheckResult

```python
@dataclass
class ACLCheckResult:
    allowed: bool           # True if access granted
    permission: Permission  # ALLOW, DENY, or RATE_LIMITED
    reason: str            # Human-readable explanation
    matched_rule: str      # Which pattern matched
```

---

## See Also

- [MCP Integration](features-integrations-mcp-integration) - Overview of MCP tunneling
- [Cryptography Guide](security-cryptography) - How peers are authenticated
- [Validation Engine](security-validation-engine) - Block-level security
