import json
from src.core.blockchain import Block
from src.core.message import MessagePayload
from src.core.did import DIDDocument
from src.core.validation.engine import ValidationResult
from src.network.protocol import ProtocolFrame

models = {
    "Block": Block,
    "MessagePayload": MessagePayload,
    "DIDDocument": DIDDocument,
    "ValidationResult": ValidationResult,
    "ProtocolFrame": ProtocolFrame,
}

schemas = {}
for name, model in models.items():
    schemas[name] = model.model_json_schema()

print(json.dumps(schemas, indent=2))
