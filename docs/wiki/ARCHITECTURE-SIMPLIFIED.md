# Simplified Architecture

This document explains the Talos flow using simple diagrams and terminology.

## The "Secure Pipe" Concept

Talos acts as a secure pipe between the User and the AI. Nothing passes through without being stamped and logged.

```mermaid
flowchart LR
    User -->|Secure Message| Dashboard
    Dashboard -->|Encrypted Request| Gateway[Talos Gateway]
    Gateway -->|Audit Log| Audit[Tamper-Evident Log]
    Gateway -->|Verified Command| Connector[MCP Connector]
    Connector -->|Prompt| AI[Ollama / AI Model]
```

## detailed Flow: Sending a Message

When you type "Hello" in the chat, here is the behind-the-scenes journey:

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant G as Gateway (Security)
    participant A as Audit Log
    participant C as Connector
    participant AI as AI Model

    Note over U, D: 1. User sends message
    U->>D: "Hello"
    D->>G: Send Secure Request over HTTP

    Note over G: 2. Security Check & Log
    G->>A: Log: REQUEST_RECEIVED (User said something)
    G->>G: Verify User Permissions (Capability)

    Note over G: 3. Forward to Tool
    G->>A: Log: TOOL_CALL (Invoking Chat Tool)
    G->>C: Execute "Chat" Tool

    Note over C, AI: 4. AI Processing
    C->>AI: Send Prompt to Model
    AI-->>C: Reply: "Hi there!"
    C-->>G: Return Result

    Note over G: 5. Verify & Log Result
    G->>A: Log: TOOL_RESULT (AI replied)
    G->>A: Log: RESPONSE_SENT (Sending back to user)

    Note over G, U: 6. Delivery
    G-->>D: "Hi there!" (Signed)
    D->>U: Display Message
```

## Key Concepts

**Tamper-Evident Audit Log**
A database where every entry is cryptographically linked. Talos uses RFC 8785 (JCS) deterministic JSON to ensure that the "stamp" (hash) is byte-perfect across all systems. If someone modifies an old entry, the chain breaks instantly.

**Capability**
A digital key or ticket that grants permission. The Gateway checks this ticket before allowing any message to pass.

**MCP (Model Context Protocol)**
The standard language the Gateway uses to talk to tools (like the Chat Tool or a Database Tool). Talos wraps this standard in a security layer.
