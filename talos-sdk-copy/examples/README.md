# Talos SDK Python Examples

This directory contains runnable examples demonstrating key features of the Talos SDK.

## Prerequisites

1. **Python 3.10+**
2. **Install SDK**: `pip install talos-sdk-py` or `pip install -e .` from repo root
3. **Gateway (optional)**: For integration examples, run the Talos Gateway at `http://localhost:8000`

## Environment Variables

| Variable            | Description           | Default                 |
| ------------------- | --------------------- | ----------------------- |
| `TALOS_GATEWAY_URL` | Gateway base URL      | `http://localhost:8000` |
| `TALOS_VERBOSE`     | Enable verbose output | `false`                 |

## Examples

### Core SDK

| Example                       | Description                                  | Gateway Required |
| ----------------------------- | -------------------------------------------- | ---------------- |
| `quickstart.py`               | Basic wallet, client, and MCP signing        | No (mock mode)   |
| `sign_mcp.py`                 | MCP request signing with audit bindings      | No               |
| `secrets_demo.py`             | Secret envelope encryption (no keys printed) | No               |
| `session_persistence_demo.py` | Save/restore ratchet state                   | No               |
| `multi_message_demo.py`       | 10 messages, unique digests verified         | No               |

### A2A Communication (Phase 10)

| Example                   | Description                        | Gateway Required |
| ------------------------- | ---------------------------------- | ---------------- |
| `a2a_messaging.py`        | Agent-to-agent encrypted messaging | Optional         |
| `a2a_live_integration.py` | Full gateway integration demo      | Yes              |
| `group_management.py`     | Group membership lifecycle         | Optional         |

## Running Examples

All examples support common flags:

```bash
python examples/<example>.py --help
```

| Flag            | Description                            | Default                 |
| --------------- | -------------------------------------- | ----------------------- |
| `--gateway-url` | Gateway base URL                       | `http://localhost:8000` |
| `--verbose`     | Enable verbose output (still redacted) | `false`                 |
| `--timeout`     | Connection timeout in seconds          | `5`                     |

### Quick Start

```bash
# Without gateway (mock mode)
python examples/quickstart.py

# With gateway
python examples/quickstart.py --gateway-url http://localhost:8000

# A2A messaging (Double Ratchet)
python examples/a2a_messaging.py --verbose
```

## Security Notes

- **No plaintext is ever sent to the gateway** - all A2A frames are E2E encrypted before transmission.
- **Sensitive fields are redacted** in all example output (private keys, ciphertext, headers, nonces).
- Examples generate **ephemeral wallets** for demonstration - do not use in production.

## Development

To add a new example:

1. Import common utilities: `from _common import parse_common_args, check_gateway, safe_print`
2. Use `parse_common_args()` for CLI flags
3. Use `safe_print()` for any output that might contain sensitive data
4. Check gateway with `check_gateway(args.gateway_url, args.timeout)` if needed
