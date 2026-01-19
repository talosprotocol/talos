#!/usr/bin/env python3
"""Common utilities for Talos SDK examples.

Provides:
- CLI argument parsing for --gateway-url, --verbose, --timeout
- Gateway health/reachability check with graceful exit
- Safe printing with redaction of sensitive fields
"""

import argparse
import sys
from typing import Any

# Keys that MUST be redacted in safe_print output
_REDACT_KEYS = frozenset({
    "private_key",
    "seed",
    "mnemonic",
    "ciphertext",
    "ciphertext_b64u",
    "header_b64u",
    "nonce",
    "authorization",
    "signature",
    "token",
    "secret",
    "password",
    "api_key",
})


def parse_common_args(description: str = "Talos SDK Example") -> argparse.Namespace:
    """Parse common CLI arguments for examples.

    Returns:
        Namespace with gateway_url, verbose, and timeout attributes.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--gateway-url",
        default="http://localhost:8000",
        help="Gateway base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output (still redacted)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Gateway connection timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit for paginated results (default: 10)",
    )
    args = parser.parse_args()
    # Normalize URL: strip trailing slash
    args.gateway_url = args.gateway_url.rstrip("/")
    return args


def check_gateway(url: str, timeout: int = 5) -> bool:
    """Check if the gateway is reachable.

    Args:
        url: Gateway base URL
        timeout: Connection timeout in seconds

    Returns:
        True if gateway is reachable, exits with code 1 otherwise.
    """
    import urllib.request
    import urllib.error

    health_url = f"{url}/health"
    print(f"🔍 Checking gateway at {url}...")

    try:
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                print(f"✅ Gateway reachable (status: {resp.status})")
                return True
    except urllib.error.URLError as e:
        print(f"❌ Gateway unreachable: {e.reason}")
        print(f"\n💡 Hint: Ensure the gateway is running at {url}")
        print("   You can start it with: docker-compose up -d talos-gateway")
        sys.exit(1)
    except TimeoutError:
        print(f"❌ Gateway timeout after {timeout}s")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error checking gateway: {e}")
        sys.exit(1)

    return False


def _redact_value(key: str, value: Any) -> Any:
    """Redact sensitive values."""
    if key.lower() in _REDACT_KEYS:
        if isinstance(value, str):
            return f"[REDACTED:{len(value)} chars]"
        elif isinstance(value, bytes):
            return f"[REDACTED:{len(value)} bytes]"
        else:
            return "[REDACTED]"
    return value


def _safe_dict(obj: dict, depth: int = 0) -> dict:
    """Recursively redact sensitive keys in a dict."""
    if depth > 10:
        return {"...": "max depth reached"}

    result = {}
    for key, value in obj.items():
        redacted = _redact_value(key, value)
        if redacted is not value:
            result[key] = redacted
        elif isinstance(value, dict):
            result[key] = _safe_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                _safe_dict(item, depth + 1) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def safe_print(obj: Any, label: str = "") -> None:
    """Print an object with sensitive fields redacted.

    Args:
        obj: Object to print (dict, list, or primitive)
        label: Optional label to prefix the output
    """
    if label:
        print(f"\n📦 {label}:")

    if isinstance(obj, dict):
        safe_obj = _safe_dict(obj)
        for key, value in safe_obj.items():
            print(f"   {key}: {value}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, dict):
                print(f"   [{i}]: {_safe_dict(item)}")
            else:
                print(f"   [{i}]: {item}")
    else:
        print(f"   {obj}")


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"✅ {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"ℹ️  {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"⚠️  {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"❌ {text}")
