from typing import Any, Dict, List, Union
import re

DENYLIST = {
    "authorization", "token", "secret", "password", "private_key", 
    "api_key", "cookie", "set-cookie", "session", "ciphertext", 
    "header_b64u", "ciphertext_b64u", "nonce"
}

PEM_PATTERN = re.compile(r"-----BEGIN [A-Z ]+-----(.*?)-----END [A-Z ]+-----", re.DOTALL)
JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9-_]+\.eyJ[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+")

def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    new_data = {}
    for k, v in data.items():
        if k.lower() in DENYLIST:
            new_data[k] = "***REDACTED***"
        else:
            new_data[k] = redact_value(v)
    return new_data

def redact_value(v: Any) -> Any:
    if isinstance(v, dict):
        return redact_dict(v)
    elif isinstance(v, list):
        return [redact_value(i) for i in v]
    elif isinstance(v, str):
        if PEM_PATTERN.search(v):
            return "***PEM REDACTED***"
        if len(v) > 100 and JWT_PATTERN.match(v): # Heuristic for JWT
             return "***JWT REDACTED***"
        if len(v) > 65536: # Cap large fields
             return v[:64] + "...(TRUNCATED)"
    return v
