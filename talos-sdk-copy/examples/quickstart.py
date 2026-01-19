#!/usr/bin/env python3
"""Talos SDK Quickstart Example.

This example demonstrates the basic usage of the Talos SDK:
1. Generate an identity wallet
2. Sign a message
3. Verify the signature
4. Create a TalosClient
5. (Optional) Connect to gateway and sign an MCP request

Run: python examples/quickstart.py --help
"""

import asyncio
import sys
from pathlib import Path

# Add examples dir to path for _common import
sys.path.insert(0, str(Path(__file__).parent))

from _common import (
    parse_common_args,
    check_gateway,
    safe_print,
    print_header,
    print_success,
    print_info,
)

from talos_sdk import TalosClient, Wallet


async def main():
    args = parse_common_args(description="Talos SDK Quickstart")

    print_header("Talos SDK Quickstart")

    # 1. Generate a new identity wallet
    wallet = Wallet.generate(name="my-agent")
    print_info(f"Generated wallet: {wallet.name}")
    print(f"   DID: {wallet.to_did()}")
    print(f"   Address: {wallet.address[:16]}...")

    # 2. Sign a message
    message = b"Hello, Talos!"
    signature = wallet.sign(message)
    print_info(f"Signed message: {message.decode()}")
    print(f"   Signature: {signature.hex()[:32]}...")

    # 3. Verify the signature
    is_valid = Wallet.verify(message, signature, wallet.public_key)
    print_success(f"Verification: {'Valid' if is_valid else 'Invalid'}")

    # 4. Create a TalosClient
    client = TalosClient(args.gateway_url, wallet)
    print_info("Created TalosClient")
    print(f"   Protocol version: {client.protocol_version()}")
    print(f"   Supported range: {client.supported_protocol_range()}")

    # 5. Optional: Connect and sign an MCP request
    print_header("Gateway Integration (Optional)")

    # Check if gateway is reachable (graceful exit if not)
    try:
        check_gateway(args.gateway_url, args.timeout)
    except SystemExit:
        print_info("Skipping gateway integration (gateway not available)")
        print_info("Run with a gateway to see full demo")
        return

    await client.connect()
    print_success("Connected to gateway")

    frame = client.sign_mcp_request(
        request={"method": "read", "params": {"path": "/data"}},
        tool="filesystem",
        action="read",
    )

    # Safe print - no sensitive fields exposed
    safe_print({
        "correlation_id": frame.correlation_id,
        "signer_did": frame.signer_did,
        "payload_size": len(frame.payload),
    }, "Signed MCP Request")

    await client.close()
    print_success("Disconnected. Quickstart complete!")


if __name__ == "__main__":
    asyncio.run(main())
