# Simple Guide to Talos Protocol

**What is this?**
Talos is a secure way for your AI Assistant (like Claude) to talk to other computers. Imagine it like a **secure tunnel**. Normally, Claude lives on your computer. With Talos, Claude can securely reach out to another computer (like your work server) and do things there, like reading files or checking databases.

## Why do I need it?
1.  **Safety**: Everything sent through the tunnel is encrypted. Only you and your AI can see it.
2.  **Audit**: Talos keeps a "receipt" (local blockchain) of every message sent, so you know exactly what the AI did.
3.  **No Cloud Needed**: It connects your computers directly to each other.

---

## How to Use It (in 5 Minutes)

### Scenario: Connecting Claude to your Laptop

**Step 1. Install Talos**
On both your computer and the target machine, open the terminal and type:
```bash
pip install talos-protocol
```

**Step 2. Create Identities**
We need to give each computer a name.
*   On Computer A (The Assistant): `talos init --name "MyAssistant"`
*   On Computer B (The Tool/Server): `talos init --name "MyServer"`

**Step 3. Connect them**
Usually, you need a "Registry" to help them find each other.
```bash
talos-server --port 8765
```
(Keep this running in a background window)

Now, tell both computers to check in:
```bash
# Computer A
talos register --server localhost:8765

# Computer B
talos register --server localhost:8765
```

**Step 4. Share a Folder**
On Computer B, let's share a folder so the Assistant can read it.
```bash
# Get your ID
talos status
# Copy the long "Address" string (e.g., a1b2c3...)

# Start sharing
talos mcp-serve --authorized-peer <COMPUTER_A_ID> --command "npx -y @modelcontextprotocol/server-filesystem /Users/me/Documents"
```

**Step 5. Configure Claude**
Open your Claude Desktop config file and add this:
```json
{
  "mcpServers": {
    "my-remote-docs": {
      "command": "talos",
      "args": ["mcp-connect", "<COMPUTER_B_ID>"]
    }
  }
}
```

**Done!** Now simply ask Claude: *"Please summarize the PDF in my remote documents folder."*
Claude will use Talos to securely fetch the file and answer you.
