# BMP Operations Runbook

This runbook provides step-by-step procedures for common operational tasks and troubleshooting scenarios for the Blockchain Messaging Protocol (BMP) and its MCP integration.

## 📋 Table of Contents

1.  [Deployment Checklist](#deployment-checklist)
2.  [Connectivity Troubleshooting](#connectivity-troubleshooting)
3.  [MCP Configuration Guide](#mcp-configuration-guide)
4.  [Security Auditing](#security-auditing)

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
    *Tip: Use full path to `bmp` executable if it's not in global PATH.*

---

## Security Auditing

### Verifying Traffic Encryption
To confirm traffic is encrypted:

1.  **Start tcpdump** on the registry port or p2p port:
    ```bash
    sudo tcpdump -i any port 8766 -X
    ```
2.  **Send Message**: `bmp send <peer> "Secret"`
3.  **Analyze**: You should NOT see "Secret" in plain text in the packet dump. You should see unrelated binary (Protocol Buffers/MsgPack) and encrypted payload.

### Rotating Keys
If a wallet is compromised:
1.  **Delete**: `rm ~/.bmp/wallet.json`
2.  **Re-init**: `bmp init --name "NewIdentity"`
3.  **Notify**: You must inform all peers of your NEW Peer ID. Old messages cannot be decrypted by the new key.
