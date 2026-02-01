# Protocol JSON Schemas

This reference documents the JSON schemas for the core data models used in the Talos Protocol. These schemas are automatically generated from Pydantic models.

## Block

```json
{
  "$defs": {
    "BlockHeader": {
      "description": "Block header containing only essential metadata.\n\nA header is ~200 bytes vs ~1MB for a full block.",
      "properties": {
        "index": {
          "title": "Index",
          "type": "integer"
        },
        "timestamp": {
          "title": "Timestamp",
          "type": "number"
        },
        "previous_hash": {
          "title": "Previous Hash",
          "type": "string"
        },
        "merkle_root": {
          "title": "Merkle Root",
          "type": "string"
        },
        "nonce": {
          "title": "Nonce",
          "type": "integer"
        },
        "hash": {
          "title": "Hash",
          "type": "string"
        },
        "difficulty": {
          "default": 2,
          "title": "Difficulty",
          "type": "integer"
        }
      },
      "required": [
        "index",
        "timestamp",
        "previous_hash",
        "merkle_root",
        "nonce",
        "hash"
      ],
      "title": "BlockHeader",
      "type": "object"
    }
  },
  "description": "Represents a block in the blockchain.",
  "properties": {
    "index": {
      "title": "Index",
      "type": "integer"
    },
    "timestamp": {
      "title": "Timestamp",
      "type": "number"
    },
    "data": {
      "items": {
        "type": "object"
      },
      "title": "Data",
      "type": "array"
    },
    "previous_hash": {
      "title": "Previous Hash",
      "type": "string"
    },
    "hash": {
      "default": "",
      "title": "Hash",
      "type": "string"
    },
    "nonce": {
      "default": 0,
      "title": "Nonce",
      "type": "integer"
    },
    "chunk_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Chunk Id"
    },
    "signature": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Signature"
    },
    "anchor_proof": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Anchor Proof"
    }
  },
  "required": [
    "index",
    "timestamp",
    "data",
    "previous_hash"
  ],
## Block

```json
{
  "type": "object",
  "properties": {
    "index": { "type": "integer" },
    "timestamp": { "type": "number" },
    "data": { "type": "object", "properties": { "messages": { "type": "array" } } },
    "previous_hash": { "type": "string" },
    "nonce": { "type": "integer" },
    "hash": { "type": "string" },
    "merkle_root": { "type": "string" }
  },
  "required": ["index", "timestamp", "data", "previous_hash", "hash", "merkle_root"]
}
```

## MessagePayload

```json
{
  "type": "object",
  "description": "Core message structure. Type is serialized as a String (Enum Name).",
  "properties": {
    "id": { "type": "string" },
    "type": { "type": "string", "enum": ["TEXT", "ACK", "MCP_MESSAGE", "MCP_RESPONSE", "HANDSHAKE", "ERROR"] },
    "sender": { "type": "string" },
    "recipient": { "type": "string" },
    "timestamp": { "type": "number" },
    "content": { "type": "string", "description": "Base64 encoded bytes" },
    "signature": { "type": "string", "description": "Base64 encoded bytes" },
    "nonce": { "type": "string", "description": "Base64 encoded bytes (optional)" },
    "metadata": { "type": "object" }
  },
  "required": ["id", "type", "sender", "recipient", "timestamp", "content", "signature"]
}
```

## DIDDocument

```json
{
  "$defs": {
    "ServiceEndpoint": {
      "description": "A service endpoint in a DID document.\n\nDescribes how to interact with the DID subject.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "type": {
          "title": "Type",
          "type": "string"
        },
        "service_endpoint": {
          "title": "Service Endpoint",
          "type": "string"
        },
        "description": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Description"
        }
      },
      "required": [
        "id",
        "type",
        "service_endpoint"
      ],
      "title": "ServiceEndpoint",
      "type": "object"
    },
    "VerificationMethod": {
      "description": "A verification method in a DID document.\n\nUsed for authentication, assertion, key agreement, etc.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "type": {
          "title": "Type",
          "type": "string"
        },
        "controller": {
          "title": "Controller",
          "type": "string"
        },
        "public_key_multibase": {
          "title": "Public Key Multibase",
          "type": "string"
        }
      },
      "required": [
        "id",
        "type",
        "controller",
        "public_key_multibase"
      ],
      "title": "VerificationMethod",
      "type": "object"
    }
  },
  "description": "W3C DID Document implementation.\n\nContains the DID subject's public keys, authentication methods,\nand service endpoints.",
  "properties": {
    "id": {
      "title": "Id",
      "type": "string"
    },
    "controller": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Controller"
    },
    "also_known_as": {
      "items": {
        "type": "string"
      },
      "title": "Also Known As",
      "type": "array"
    },
    "verification_method": {
      "items": {
        "$ref": "#/$defs/VerificationMethod"
      },
      "title": "Verification Method",
      "type": "array"
    },
    "authentication": {
      "items": {
        "type": "string"
      },
      "title": "Authentication",
      "type": "array"
    },
    "assertion_method": {
      "items": {
        "type": "string"
      },
      "title": "Assertion Method",
      "type": "array"
    },
    "key_agreement": {
      "items": {
        "type": "string"
      },
      "title": "Key Agreement",
      "type": "array"
    },
    "capability_invocation": {
      "items": {
        "type": "string"
      },
      "title": "Capability Invocation",
      "type": "array"
    },
    "capability_delegation": {
      "items": {
        "type": "string"
      },
      "title": "Capability Delegation",
      "type": "array"
    },
    "service": {
      "items": {
        "$ref": "#/$defs/ServiceEndpoint"
      },
      "title": "Service",
      "type": "array"
    },
    "created": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Created"
    },
    "updated": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Updated"
    }
  },
  "required": [
    "id"
  ],
  "title": "DIDDocument",
  "type": "object"
}
```
