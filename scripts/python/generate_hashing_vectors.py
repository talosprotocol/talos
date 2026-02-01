import hashlib
import json
from typing import Any


# Approximate JCS (RFC 8785) for our use case (no floats, simple types)
# 1. Sort keys
# 2. No whitespace (separators=(',', ':'))
def jcs_serialize(data: Any) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_vectors() -> None:
    vectors: dict[str, list[dict[str, Any]]] = {
        "tool_call_vectors": [],
        "document_vectors": [],
    }

    # 1. Tool Call Vectors
    # Case A: Standard Write
    tc_write = {
        "tool_server": "postgres",
        "tool_name": "execute_query",
        "capability": {"read_only": False},
        "args": {"query": "INSERT INTO users VALUES (1)", "params": [1]},
        # principal_id excluded
    }
    vectors["tool_call_vectors"].append(
        {
            "description": "Standard Write Tool Call",
            "input": tc_write,
            "digest": sha256_digest(jcs_serialize(tc_write)),
        }
    )

    # Case B: Standard Read
    tc_read = {
        "tool_server": "postgres",
        "tool_name": "execute_query",
        "capability": {"read_only": True},
        "args": {"query": "SELECT * FROM users"},
    }
    vectors["tool_call_vectors"].append(
        {
            "description": "Standard Read Tool Call",
            "input": tc_read,
            "digest": sha256_digest(jcs_serialize(tc_read)),
        }
    )

    # Case C: Empty Args
    tc_empty = {
        "tool_server": "system",
        "tool_name": "ping",
        "capability": {"read_only": True},
        "args": {},
    }
    vectors["tool_call_vectors"].append(
        {
            "description": "Empty Args Tool Call",
            "input": tc_empty,
            "digest": sha256_digest(jcs_serialize(tc_empty)),
        }
    )

    # 2. Document Vectors
    # Case A: JSON Doc
    doc_json = {"foo": "bar", "baz": 123}
    vectors["document_vectors"].append(
        {
            "description": "Simple JSON Document",
            "doc_type": "json",
            "input": doc_json,
            "digest": sha256_digest(jcs_serialize(doc_json)),
        }
    )

    # Case B: Bytes Doc (String simulation of check)
    raw_data = b"Hello World"
    vectors["document_vectors"].append(
        {
            "description": "Raw Bytes Document",
            "doc_type": "bytes",
            "input_b64": "SGVsbG8gV29ybGQ=",  # For JSON representation
            "digest": sha256_digest(raw_data),
        }
    )

    # Write output
    output_path = "contracts/schemas/mcp/hashing_vectors.json"
    with open(output_path, "w") as f:
        # We output the JSON nicely formatted for readability,
        # but the logical tests using it MUST re-serialize 'input' fields using JCS.
        json.dump(vectors, f, indent=2)

    print(f"Generated vectors to {output_path}")


if __name__ == "__main__":
    generate_vectors()
