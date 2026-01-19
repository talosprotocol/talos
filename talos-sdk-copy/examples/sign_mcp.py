#!/usr/bin/env python3
"""MCP Request Signing Example.

This example demonstrates how to sign MCP requests for secure AI tool invocation.
"""

from talos_sdk import Wallet, sign_mcp_request, verify_mcp_response


def main():
    print("=== MCP Request Signing Example ===\n")

    # Create an agent wallet
    agent_wallet = Wallet.generate(name="agent-1")
    print(f"Agent DID: {agent_wallet.to_did()}")

    # Define an MCP request
    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "read_file",
            "arguments": {
                "path": "/etc/passwd",
            },
        },
    }

    # Sign the request with audit bindings
    signed_frame = sign_mcp_request(
        wallet=agent_wallet,
        request=mcp_request,
        session_id="session-abc123",
        correlation_id="req-001",
        tool="filesystem",
        action="read",
    )

    print("\nSigned MCP Request:")
    print("  Tool: filesystem")
    print("  Action: read")
    print(f"  Correlation ID: {signed_frame.correlation_id}")
    print(f"  Payload size: {len(signed_frame.payload)} bytes")
    print(f"  Signature: {signed_frame.signature.hex()[:32]}...")

    # Verify the signature (as the gateway would)
    is_valid = verify_mcp_response(
        frame=signed_frame,
        expected_correlation_id="req-001",
        signer_public_key=agent_wallet.public_key,
    )
    print(f"\nVerification: {'✓ Valid' if is_valid else '✗ Invalid'}")

    # Test with wrong correlation ID
    is_invalid = verify_mcp_response(
        frame=signed_frame,
        expected_correlation_id="wrong-id",
        signer_public_key=agent_wallet.public_key,
    )
    print(f"Wrong correlation ID: {'✓ Rejected' if not is_invalid else '✗ Accepted'}")


if __name__ == "__main__":
    main()
