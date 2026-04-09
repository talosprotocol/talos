import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path

from talos_contracts.infrastructure.canonical import canonical_json_bytes

REPO_ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_SRC = REPO_ROOT / "services/mcp-connector/src"
CONNECTOR_POLICY = CONNECTOR_SRC / "talos_mcp/domain/tool_policy.py"
CONNECTOR_AVAILABLE = CONNECTOR_POLICY.exists()

if CONNECTOR_AVAILABLE:
    sys.path.insert(0, str(CONNECTOR_SRC))
    from talos_mcp.domain.tool_policy import DocumentValidator, DocumentSpec, ToolPolicyError
else:
    DocumentValidator = DocumentSpec = ToolPolicyError = None


def jcs_serialize(data: object) -> bytes:
    return canonical_json_bytes(data)


@unittest.skipUnless(
    CONNECTOR_AVAILABLE, "services/mcp-connector source unavailable in this checkout"
)
class TestHashesCompliance(unittest.TestCase):
    def setUp(self):
        vector_path = REPO_ROOT / "contracts/schemas/mcp/hashing_vectors.json"
        if not vector_path.exists():
            vector_path = REPO_ROOT / "services/mcp-connector/contracts/schemas/mcp/hashing_vectors.json"
        if not vector_path.exists():
            raise FileNotFoundError("hashing vectors not found in contracts or mcp-connector")

        self.vectors = json.loads(vector_path.read_text(encoding="utf-8"))

    def test_tool_call_digests(self):
        for case in self.vectors["tool_call_vectors"]:
            input_data = case["input"]
            expected_digest = case["digest"]
            
            serialized = jcs_serialize(input_data)
            computed = hashlib.sha256(serialized).hexdigest()
            
            self.assertEqual(
                computed, 
                expected_digest, 
                f"Digest mismatch for {case['description']}"
            )

    def test_document_digests(self):
        for case in self.vectors["document_vectors"]:
            doc_type = case["doc_type"]
            expected_digest = case["digest"]
            
            if doc_type == "json":
                input_data = case["input"]
                serialized = jcs_serialize(input_data)
                computed = hashlib.sha256(serialized).hexdigest()
            elif doc_type == "bytes":
                input_b64 = case["input_b64"]
                decoded = base64.b64decode(input_b64)
                computed = hashlib.sha256(decoded).hexdigest()
            
            self.assertEqual(computed, expected_digest, f"Doc digest mismatch for {case['description']}")

    def test_negative_validation(self):
        """Verify negative cases raise ToolPolicyError with correct code."""
        if "negative_validation_vectors" not in self.vectors:
            print("Skipping negative validation (vectors not present)")
            return

        for case in self.vectors["negative_validation_vectors"]:
            print(f"Testing Negative Case: {case['description']}")
            d_spec = case["doc_spec"]
            
            # Construct DocumentSpec from vector dict
            spec = DocumentSpec(
                write_content_pointers=d_spec.get("write_content_pointers", []),
                read_content_pointers=d_spec.get("read_content_pointers", []),
                content_encoding=d_spec.get("content_encoding", "utf8"),
                max_read_bytes=10000,
                max_write_bytes=d_spec.get("max_write_bytes", 10000),
                max_batch_bytes=100000
            )
            
            expected_code = case["error_code"]
            args = case["args"]
            expected_hashes = case.get("expected_hashes")

            with self.assertRaises(ToolPolicyError) as cm:
                DocumentValidator.validate_write_content(
                    doc_spec=spec,
                    args=args,
                    expected_hashes=expected_hashes
                )
            
            self.assertEqual(cm.exception.code, expected_code, f"Wrong error code for {case['description']}")

if __name__ == "__main__":
    unittest.main()
