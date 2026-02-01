from typing import Any

DENYLIST = {
    "password",
    "secret",
    "key",
    "token",
    "auth",
    "credential",
    "private",
    "client_id",
    "client_secret",
}


def redact_config(config: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact sensitive keys in a configuration dictionary.

    Rules:
    - Keys in DENYLIST are redacted to "***".
    - Keys ending in "_ref" are NOT redacted (they are references).
    - Case-insensitive key matching for heuristics.

    Args:
        config: The configuration dictionary to redact.

    Returns:
        dict[str, Any]: The redacted configuration dictionary.
    """
    if not isinstance(config, dict):
        return config

    redacted = {}
    for k, v in config.items():
        key_lower = k.lower()

        # Check if it's a reference (skip redaction)
        if key_lower.endswith("_ref"):
            redacted[k] = v
            continue

        # Check denylist and heuristics
        is_sensitive = any(term in key_lower for term in DENYLIST)

        if is_sensitive:
            # Basic heuristic: if it looks like a secret, redact it.
            # Strict denylist match or partial match for things like "db_password"
            if isinstance(v, (str, int, float, bool)) or v is None:
                redacted[k] = "***"
            else:
                # Recurse for nested structures (though secrets usually aren't objects)
                if isinstance(v, dict):
                    redacted[k] = redact_config(v)
                elif isinstance(v, list):
                    redacted[k] = _redact_list(v)
                else:
                    redacted[k] = "***"
        else:
            if isinstance(v, dict):
                redacted[k] = redact_config(v)
            elif isinstance(v, list):
                redacted[k] = _redact_list(v)
            else:
                redacted[k] = v

    return redacted


def _redact_list(data: list[Any]) -> list[Any]:
    """Helper to redact sensitive items within a list.

    Args:
        data: The list of items to redact.

    Returns:
        list[Any]: The list with sensitive items redacted.
    """
    redacted_list: list[Any] = []
    for item in data:
        if isinstance(item, dict):
            redacted_list.append(redact_config(item))
        elif isinstance(item, list):
            redacted_list.append(_redact_list(item))
        else:
            redacted_list.append(item)
    return redacted_list
