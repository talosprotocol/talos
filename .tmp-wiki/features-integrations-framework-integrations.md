---
status: Planned
audience: Developer
---

# Framework Integrations

> **Problem**: Developers want Talos with their existing tools.  
> **Guarantee**: Integration guides for popular frameworks.  
> **Non-goal**: Complete implementations—these are guides.

---

## Integration Status

| Framework | Status | Priority |
|-----------|--------|----------|
| **LangChain** | 📋 Planned | High |
| **LlamaIndex** | 📋 Planned | High |
| **CrewAI** | 📋 Planned | Medium |
| **AutoGen** | 📋 Planned | Medium |
| **Ollama** | ✅ Supported | High |
| **DSPy** | 📋 Planned | Low |

---

## Ollama Integration

Ollama works with Talos for local LLM inference.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Your Agent                        │
├─────────────────────────────────────────────────────┤
│  Talos Client  ←──────────────→  Talos Network     │
│       │                                             │
│       ▼                                             │
│  ┌─────────────────────────────────────────────┐   │
│  │               Ollama API                     │   │
│  │  localhost:11434 (local inference)          │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Usage

```python
import ollama
from talos import TalosClient

async def agent_with_local_llm():
    async with TalosClient.create("local-agent") as client:
        # Receive message via Talos
        message = await client.receive_one()
        
        # Process with local Ollama
        response = ollama.chat(
            model="llama2",
            messages=[{"role": "user", "content": message.content.decode()}]
        )
        
        # Reply via Talos
        await client.send(
            message.sender,
            response["message"]["content"].encode()
        )
```

### Benefits

- No cloud dependency
- Data stays local
- Full E2EE with Talos
- Audit trail for all interactions

---

## LangChain Integration (Planned)

### Design

```python
# Planned API
from talos.integrations.langchain import TalosCallbackHandler, TalosSecureTool

# Wrap tools with Talos security
secure_tool = TalosSecureTool(
    tool=existing_tool,
    talos_client=client,
    capability=capability
)

# Callback for audit
callback = TalosCallbackHandler(client=client)

chain = LLMChain(
    llm=llm,
    tools=[secure_tool],
    callbacks=[callback]
)
```

### What It Provides

- Tool invocation via Talos tunnel
- Automatic capability verification
- Audit of all tool calls
- E2EE between chain components

---

## LlamaIndex Integration (Planned)

### Design

```python
# Planned API
from talos.integrations.llama_index import TalosToolSpec

# Create Talos-secured tool spec
tool_spec = TalosToolSpec(
    talos_client=client,
    peer_id=tool_provider,
    capability=capability
)

agent = OpenAIAgent.from_tools(
    tool_spec.to_tool_list()
)
```

---

## CrewAI Integration (Planned)

### Design

```python
# Planned API
from talos.integrations.crewai import TalosAgent, TalosTool

# Create Talos-enabled agent
agent = TalosAgent(
    role="researcher",
    talos_client=client,
    talos_identity="did:talos:researcher"
)

# Create Talos-secured tool
tool = TalosTool(
    tool=search_tool,
    capability=capability
)

crew = Crew(
    agents=[agent],
    tools=[tool]
)
```

### Benefits for Multi-Agent

- Agent-to-agent communication via Talos
- Capability-based tool access
- Cross-agent audit trail

---

## AutoGen Integration (Planned)

### Design

```python
# Planned API
from talos.integrations.autogen import TalosAssistant

assistant = TalosAssistant(
    name="coder",
    talos_client=client,
    talos_peer_id=peer_id
)

user_proxy = autogen.UserProxyAgent(...)

# Chat via Talos channel
user_proxy.initiate_chat(
    assistant,
    message="Write a Python function"
)
```

---

## Generic Integration Pattern

For any framework:

```python
class TalosSecureWrapper:
    def __init__(
        self,
        talos_client: TalosClient,
        peer_id: str,
        capability: Capability
    ):
        self.client = talos_client
        self.peer_id = peer_id
        self.capability = capability
    
    async def invoke(self, method: str, params: dict) -> Any:
        """Invoke tool via Talos."""
        result = await self.client.mcp_call(
            peer_id=self.peer_id,
            method=method,
            params=params,
            capability=self.capability
        )
        return result
    
    def wrap_tool(self, tool: Callable) -> Callable:
        """Wrap a tool function with Talos security."""
        async def wrapped(*args, **kwargs):
            return await self.invoke(tool.__name__, kwargs)
        return wrapped
```

---

## MCP Server Integration

Any MCP server can be Talos-secured:

```python
from talos import TalosClient, MCPServer

async with TalosClient.create("tool-server") as client:
    # Wrap existing MCP server
    server = MCPServer(client)
    
    @server.tool("my_tool")
    async def my_tool(param: str, capability: Capability):
        # Capability verified automatically
        return do_something(param)
    
    await server.serve(port=8766)
```

---

## Timeline

| Framework | Target |
|-----------|--------|
| Ollama | ✅ Now |
| LangChain adapter | Q2 2025 |
| LlamaIndex adapter | Q2 2025 |
| CrewAI adapter | Q3 2025 |
| AutoGen adapter | Q3 2025 |

---

## Contributing Integrations

We welcome community integrations:

1. Follow the [TalosSecureWrapper pattern](#generic-integration-pattern)
2. Add audit callbacks
3. Test with real workflows
4. Submit PR to `talos-integrations` repo

---

**See also**: [MCP Cookbook](mcp-cookbook) | [Python SDK](sdk-python-sdk) | [MCP Integration](mcp-integration)
