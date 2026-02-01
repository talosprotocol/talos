# Simplified Architecture

> **Talos v5.15** | **The "Secure Pipe" Concept**

---

## 🏗️ How it Works

Talos acts as a **Secure Pipe** between an AI Agent and the external world. No request can pass through without being verified against a budget and logged for audit.

```mermaid
flowchart LR
    A[Agent] -->|Request| G[Gateway]
    G <-->|Check Budget| C[Config Service]
    G -->|Authorized?| T[Tool / LLM]
    G -->|Receipt| L[Audit Log]
    
    style G fill:#f96,stroke:#333
    style C fill:#69f,stroke:#333
    style L fill:#6f6,stroke:#333
```

---

## 📝 The Life of a Request

When an agent wants to perform an action (like calling a tool or sending a message):

```mermaid
sequenceDiagram
    participant A as AI Agent
    participant G as Talos Gateway
    participant C as Config (Budgets)
    participant T as External Tool
    participant L as Audit Log

    A->>G: 1. Send Request (Signed)
    G->>C: 2. Check Quota & Budget
    C-->>G: 3. Approved (Budget Remaining)
    
    rect rgb(240, 240, 240)
        Note right of G: Security Boundary
        G->>T: 4. Invoke Tool / API
        T-->>G: 5. Return Result
    end

    G->>L: 6. Log Signed Receipt
    G-->>A: 7. Return Result + Proof
```

---

## 🔑 Key Concepts for Humans

### 💰 Adaptive Budgets
Think of this as a **Smart Credit Card** for your AI. Every time the AI does something, Talos checks if it has enough "credits" and if the action follows the safety rules.

### 🛡️ The Gateway (The Guard)
The Gateway is like a **Security Checkpoint**. It checks the ID of the agent, verifies the signature of the message, and makes sure everything is encrypted.

### 📜 The Audit Log (The Black Box)
Like an airplane's black box, the Audit Log records everything. Because it uses **Merkle Chaining**, it is physically impossible to change a past log entry without everyone noticing.

### 🏗️ Contract-Driven
We use a **Master Blueprints** (Contracts) to make sure that the Python version, the JavaScript version, and the Rust version of Talos all speak exactly the same language.

---

> [!TIP]
> **Ready to try it?** Go to the [Quickstart](getting-started-quickstart) guide to see this flow in action!
