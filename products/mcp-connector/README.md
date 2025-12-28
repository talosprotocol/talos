# Talos MCP Connector

The **Talos MCP Connector** is a product that allows you to securely expose *any* Standard MCP Server over the Talos P2P Network.

This enables you to use local tools (Git, Databases, LLMs) from remote AI Agents (like Claude Desktop) with full cryptographic security and auditability.

## 🚀 Quick Start

### 1. Configuration
Edit `mcp_config.yaml` to define your identity and the tools you want to share.

```yaml
resources:
  - name: "git-repo"
    command: "uvx mcp-server-git"
    allowed_peers: ["<YOUR_AGENT_PEER_ID>"]
```

### 2. Run the Connector
```bash
python3 connector.py mcp_config.yaml
```

The connector will:
1.  Initialize a Talos Identity (`GenericHost`).
2.  Register with the network.
3.  Launch a secure bridge for each defined resource.

### 3. Connect from Agent
On your client machine (Agent), use `talos mcp-connect`:

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "remote-git": {
      "command": "talos",
      "args": ["mcp-connect", "<HOST_PEER_ID>"]
    }
  }
}
```

## 📦 Supported Resource Types
Any MCP Server that runs over Stdio is supported.
*   **Git**: `uvx mcp-server-git`
*   **SQLite**: `uvx mcp-server-sqlite`
*   **Postgres**: `uvx mcp-server-postgres`
*   **Ollama**: (See `examples/mcp_server_ollama.py`)
*   **Google Drive**: `uvx mcp-server-gdrive`

## 🔒 Security
*   **Zero-Trust**: Only peers listed in `allowed_peers` can access the tool.
*   **Encryption**: All traffic is E2EE using X25519/ChaCha20.
*   **Audit**: Every interaction is logged to the local chain.
