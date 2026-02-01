# Talos Protocol - Non-Technical Runbook

## What is Talos?
Talos is a security layer for AI agents. Just as https (the lock icon in your browser) secures web traffic, Talos secures the conversations between AI models and the tools they use.

It provides a **tamper-evident audit trail**, meaning every action taken by an AI is cryptographically signed and logged. If anyone tries to alter history, the system detects it immediately.

## What this Demo Shows
This demo showcases a "Secure Chat" where an AI Assistant (powered by a local model, Ollama) chats with you.

Crucially, **every message is audited**.
- When you send a message, Talos logs the request.
- When the AI considers its response, Talos logs the tool usage.
- When the AI replies, Talos logs the outcome.

You will see "Verified" and "Audited" badges in the dashboard, proving that the conversation is secured by the Talos Protocol.

## How to Run the Demo

### Prerequisites
- Docker (optional, for full stack) or Python 3.10+ & Node.js 18+
- **Ollama** installed and running (`ollama serve`)
- Model pulled: `ollama pull llama3.2:latest`

### Step-by-Step

1. **Start the System**
   Open your terminal in the project folder and run:
   ```bash
   ./deploy/scripts/start_all.sh
   ```
   Wait for the message: `All services are running!`

2. **Open the Dashboard**
   Go to **http://localhost:3000** in your web browser.

3. **Navigate to Secure Chat**
   Click the **Secure Chat** button in the top header.

4. **Start Chatting**
   Type "Hello" and hit Send.
   - You will see the AI reply.
   - Notice the green **Audited** badge.
   - The "Session" ID at the top tracks this specific secure conversation.

5. **Verify the Audit Trail**
   Click "Back to Dashboard".
   Look at the "Activity Feed". You will see new events appearing in real-time:
   - `CHAT_REQUEST_RECEIVED`
   - `CHAT_TOOL_CALL`
   - `CHAT_TOOL_RESULT`
   - `CHAT_RESPONSE_SENT`

   This proves that the conversation was fully captured and secured.

## Common Issues

**AI is not replying / Red Error Banner**
- Ensure Ollama is running: `ollama serve`
- Ensure you have the model: `ollama pull llama3.2:latest`

**Dashboard says "Network Error"**
- Ensure the Gateway is running on port 8000 and Connector on 8004.
- Check logs: `cat /tmp/talos-gateway.log`

**"Tampered" or "Invalid" Events**
- If you see red "Invalid" markers in the feed, it means the cryptographic proof verification failed (or simulated failure). In a real production system, this alerts security teams to a potential breach.
