# Talos Operations Runbook

This runbook provides step-by-step procedures for common operational tasks and troubleshooting scenarios for the Talos Protocol and its MCP integration.

## 📋 Table of Contents

1.  [Quick Demo](#quick-demo)
2.  [Deployment Checklist](#deployment-checklist)
3.  [Connectivity Troubleshooting](#connectivity-troubleshooting)
4.  [MCP Configuration Guide](#mcp-configuration-guide)
5.  [Security Auditing](#security-auditing)

---

## Quick Demo

Run the capability authorization demo to see Phase 1-3 features:

```bash
python examples/demo_capability.py
```

### Expected Output

```
============================================================
  TALOS PROTOCOL DEMO - Phase 1-3 Features
============================================================

✓ Created CapabilityManager
  Issuer: did:talos:issuer
  Key type: Ed25519

✓ Granted capability: cap_fc301fddd52972214e621a54
  Subject: did:talos:agent
  Scope: tool:filesystem/method:read

✓ Authorization result: ALLOWED

✓ Session-cached authorization:
  ├─ Average: 0.1μs
  ├─ p99: 3μs
  └─ Status: ✓ PASS (<1ms target)

✓ Audit events recorded:
  ├─ Total: 3
  ├─ Denials: 1
  └─ Approval rate: 67%

✓ Rate limiter test (burst=5, 10 calls):
  ├─ Allowed: 5
  └─ Blocked: 5
```

### Features Demonstrated

| Feature | Description |
|---------|-------------|
| **Identity** | Ed25519 keypair generation |
| **Capabilities** | Scoped, time-bounded tokens |
| **Session Auth** | <1ms cached authorization |
| **Audit Plane** | Event recording + CSV export |
| **Rate Limiting** | Per-session token bucket |

---

## Deployment Checklist

### 1. Registry Server Setup
The central registry helps peers find each other (until DHT is fully active).

- [ ] **Provision Server**: A VPS or cloud instance with Python 3.11+.
- [ ] **Install Talos**: `pip install talos-protocol`
- [ ] **Start Registry**: 
  ```bash
  nohup talos-server --port 8765 > registry.log 2>&1 &
  ```
- [ ] **Verify**: `telnet localhost 8765` (should connect)

### 2. Client Provisioning
For each new user/agent:

- [ ] **Install**: `pip install talos-protocol`
- [ ] **Initialize**: `talos init --name "<Role/Name>"`
- [ ] **Backup**: Securely store `~/.talos/wallet.json`.
- [ ] **Register**: `talos register --server <registry-ip>:8765`

---

## Connectivity Troubleshooting

### Issue: "Peer not found"
**Symptoms**: `talos send` or `mcp-connect` fails with peer lookup error.

**Steps**:
1.  **Check Registry**: Are both peers registered?
    ```bash
    talos peers
    ```
2.  **Check Network**:
    -   Can the client reach the registry IP?
    -   Can peers reach each other? (NAT/Firewall issues).
    -   *Note*: Currently Talos requires direct reachability or a common network. Future versions will support TURN/Relay.
3.  **Refresh**: Run `talos register` again on both nodes to update IP/Port.

### Issue: "Handshake Failed" or "Decryption Error"
**Symptoms**: Connection drops immediately or garbage text received.

**Steps**:
1.  **Verify Keys**: Ensure the Sender has the correct Recipient Public Key.
2.  **Check Clocks**: Large clock skew (>60s) can invalidates timestamps/signatures.
3.  **Reset**: Delete `~/.talos/blockchain.json` (safe, just history) if state is corrupted.

---

## MCP Configuration Guide

### 🤖 Case A: Connecting Claude Desktop to a Remote Server

**Goal**: Let Claude on a Mac access files on a Linux server.

1.  **Linux Server (Host)**:
    ```bash
    # install talos
    pip install talos-protocol
    talos init --name "LinuxBox"
    talos register --server <registry>
    talos status
    # Copy ID: <LINUX_PEER_ID>
    
    # Start serving
    # Ensure @modelcontextprotocol/server-filesystem is installed
    talos mcp-serve \
        --authorized-peer <MAC_PEER_ID> \
        --command "npx -y @modelcontextprotocol/server-filesystem /home/user/projects"
    ```

2.  **Mac (Agent)**:
    ```bash
    # install talos
    pip install talos-protocol
    talos init --name "ClaudeMac"
    talos register --server <registry>
    talos status
    # Copy ID: <MAC_PEER_ID> (Give this to Linux config above)
    ```

3.  **Config Config**:
    Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
        "remote-linux-fs": {
          "command": "/path/to/venv/bin/talos", 
          "args": ["mcp-connect", "<LINUX_PEER_ID>", "--server", "<registry>"]
        }
      }
    }
    ```
    *Tip: Use full path to `talos` executable if it's not in global PATH.*

---

## Security Auditing

### Verifying Traffic Encryption
To confirm traffic is encrypted:

1.  **Start tcpdump** on the registry port or p2p port:
    ```bash
    sudo tcpdump -i any port 8766 -X
    ```
2.  **Send Message**: `talos send <peer> "Secret"`
3.  **Analyze**: You should NOT see "Secret" in plain text in the packet dump. You should see unrelated binary (Protocol Buffers/MsgPack) and encrypted payload.

### Rotating Keys
If a wallet is compromised:
1.  **Delete**: `rm ~/.talos/wallet.json`
2.  **Re-init**: `talos init --name "NewIdentity"`
3.  **Notify**: You must inform all peers of your NEW Peer ID. Old messages cannot be decrypted by the new key.
