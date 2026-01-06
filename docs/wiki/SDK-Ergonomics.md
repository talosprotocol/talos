---
status: Implemented
audience: Developer
---

# SDK Ergonomics

> **Problem**: SDK should be pleasant to use.  
> **Guarantee**: Best practices and common patterns.  
> **Non-goal**: API reference—see [Python SDK](Python-SDK).

---

## Design Principles

1. **Async-first**: All I/O operations are async
2. **Context managers**: Resource cleanup is automatic
3. **Type hints**: Full typing support
4. **Sensible defaults**: Works out of the box
5. **Explicit over implicit**: No hidden behavior

---

## Good vs Bad Patterns

### ❌ Bad: Manual Cleanup

```python
# Don't do this
client = TalosClient("agent")
await client.connect()
try:
    await client.send(peer, message)
finally:
    await client.disconnect()  # Easy to forget
```

### ✅ Good: Context Manager

```python
# Do this
async with TalosClient.create("agent") as client:
    await client.send(peer, message)
# Automatic cleanup
```

---

### ❌ Bad: Manual Session Management

```python
# Don't do this
bundle = await client.get_prekey_bundle(peer_id)
await client.establish_session(peer_id, bundle)
await client.send(peer_id, message)
```

### ✅ Good: Auto-Session

```python
# Do this - session established automatically
await client.send(peer_id, message)
```

---

### ❌ Bad: Ignoring Errors

```python
# Don't do this
try:
    await client.send(peer_id, message)
except:
    pass  # Silent failure
```

### ✅ Good: Specific Error Handling

```python
# Do this
from talos import TalosError, PeerUnreachable, CapabilityExpired

try:
    await client.send(peer_id, message)
except PeerUnreachable:
    await client.queue_message(peer_id, message)
except CapabilityExpired:
    new_cap = await client.renew_capability(cap_id)
    await client.send(peer_id, message, capability=new_cap)
except TalosError as e:
    logger.error(f"Talos error: {e.code} - {e.message}")
```

---

### ❌ Bad: Hardcoded Credentials

```python
# Don't do this
client = await TalosClient.create(
    "agent",
    password="hunter2"  # In code!
)
```

### ✅ Good: Environment Variables

```python
# Do this
import os

client = await TalosClient.create(
    "agent",
    password=os.environ["TALOS_KEY_PASSWORD"]
)
```

---

### ❌ Bad: Blocking in Async

```python
# Don't do this
async def handler(message):
    time.sleep(5)  # Blocks event loop!
    return process(message)
```

### ✅ Good: Non-Blocking

```python
# Do this
async def handler(message):
    await asyncio.sleep(5)  # OK
    # Or for CPU-bound:
    result = await asyncio.to_thread(cpu_intensive, message)
    return result
```

---

### ❌ Bad: Unbounded Concurrency

```python
# Don't do this
tasks = [client.send(peer, msg) for msg in messages]
await asyncio.gather(*tasks)  # May overwhelm peer
```

### ✅ Good: Bounded Concurrency

```python
# Do this
import asyncio

semaphore = asyncio.Semaphore(10)

async def send_limited(peer, msg):
    async with semaphore:
        return await client.send(peer, msg)

tasks = [send_limited(peer, msg) for msg in messages]
await asyncio.gather(*tasks)
```

---

## Common Patterns

### Pattern: Retry with Backoff

```python
import asyncio
from talos import PeerUnreachable

async def send_with_retry(client, peer, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.send(peer, message)
        except PeerUnreachable:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

---

### Pattern: Message Handler

```python
async def run_agent(client):
    async for message in client.receive():
        try:
            response = await handle(message)
            if response:
                await client.send(message.sender, response)
        except Exception as e:
            logger.error(f"Handler error: {e}")
```

---

### Pattern: Capability Renewal

```python
async def with_renewed_capability(client, capability, operation):
    """Automatically renew capability if expired."""
    try:
        return await operation(capability)
    except CapabilityExpired:
        renewed = await client.renew_capability(capability.id)
        return await operation(renewed)
```

---

### Pattern: Graceful Shutdown

```python
import signal

async def main():
    client = await TalosClient.create("agent")
    
    shutdown_event = asyncio.Event()
    
    def handle_signal():
        shutdown_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)
    
    async with client:
        while not shutdown_event.is_set():
            await process_messages(client)
    
    print("Shutdown complete")
```

---

### Pattern: Message Batching

```python
async def send_batch(client, peer, messages, batch_size=10):
    """Send messages in batches for efficiency."""
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        await asyncio.gather(*[
            client.send(peer, msg) for msg in batch
        ])
```

---

## Type Hints

The SDK is fully typed:

```python
from talos import TalosClient, Message, Capability, PeerId

async def process(
    client: TalosClient,
    peer: PeerId,
    message: bytes,
    capability: Capability | None = None
) -> Message:
    return await client.send(peer, message, capability=capability)
```

### IDE Support

With proper type hints:
- Autocompletion works
- Type errors caught early
- Documentation on hover

---

## Configuration Patterns

### Development

```python
client = await TalosClient.create(
    "dev-agent",
    log_level="DEBUG",
    data_dir="./dev_data"
)
```

### Production

```python
client = await TalosClient.create(
    "prod-agent",
    log_level="INFO",
    data_dir="/var/lib/talos",
    password=os.environ["TALOS_KEY_PASSWORD"],
    metrics_port=9090,
    health_port=8080
)
```

### Testing

```python
# In tests
from talos.testing import MockTalosClient

async def test_handler():
    client = MockTalosClient()
    client.mock_receive([Message(...)])
    
    await handler(client)
    
    assert client.sent_messages[0].content == expected
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Manual cleanup | Resource leaks | Use context managers |
| Bare `except:` | Hide errors | Catch specific exceptions |
| Blocking I/O | Freezes event loop | Use async APIs |
| Hardcoded secrets | Security risk | Use environment |
| Global client | Testing hard | Dependency injection |
| No timeouts | Hangs forever | Set explicit timeouts |

---

**See also**: [Python SDK](Python-SDK) | [API Reference](API-Reference) | [Error Troubleshooting](Error-Troubleshooting)
